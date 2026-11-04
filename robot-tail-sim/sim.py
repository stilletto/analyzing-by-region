"""Simulation core: servo model, whole-body IK, ZMP preview planner, controller, runner.

The same control architecture is used for every variant:
  plan (LIPM + ZMP preview control) -> whole-body IK -> joint position commands
  -> servo model (latency, motor lag, torque-speed envelope) -> MuJoCo physics.
A DCM (capture point) stabilizer shifts the commanded COM from delayed state
measurements. The only variant-specific part is WHERE the total ZMP may go:
inside the stance foot for the biped, inside the hull of feet + tail wheels
for the tailed robot.
"""
import numpy as np
import mujoco
from scipy.linalg import solve_discrete_are

from model import build, LEG_JOINTS, SIDES, ANKLE_H, HIP_HALF_W, FOOT_L

G = 9.81
SOLE_CX = 0.05          # sole centre is 5 cm ahead of the ankle


# ----------------------------------------------------------------------------- servo
class ServoSpec:
    """Per-joint servo class. Torques in N*m, speeds in rad/s, times in s."""

    def __init__(self, name="premium", tau_max=None, w_max=None, latency=0.002, t_motor=0.0005,
                 kp=None, kd=None):
        self.name = name
        # order per leg: hip_roll, hip_pitch, knee, ankle_pitch, ankle_roll
        self.tau_max = np.array(tau_max if tau_max is not None else [200, 250, 250, 180, 120], float)
        self.w_max = np.array(w_max if w_max is not None else [20, 20, 20, 20, 20], float)
        self.latency = latency          # sensor -> controller -> servo command, total
        self.t_motor = t_motor          # torque (current loop + driver) lag
        self.kp = np.array(kp if kp is not None else [2500, 2500, 2500, 2000, 1500], float)
        self.kd = np.array(kd if kd is not None else [60, 60, 60, 60, 40], float)

    def scaled(self, name=None, torque=1.0, speed=1.0, latency=None, t_motor=None):
        s = ServoSpec(name or self.name, self.tau_max * torque, self.w_max * speed,
                      self.latency if latency is None else latency,
                      self.t_motor if t_motor is None else t_motor, self.kp, self.kd)
        return s


class ServoBank:
    def __init__(self, spec, dt):
        self.spec = spec
        self.tau_max = np.tile(spec.tau_max, 2)
        self.w_max = np.tile(spec.w_max, 2)
        self.kp = np.tile(spec.kp, 2)
        self.kd = np.tile(spec.kd, 2)
        self.a = dt / (spec.t_motor + dt)
        self.tau = np.zeros(10)

    def step(self, q_cmd, q, qd):
        tau_pd = self.kp * (q_cmd - q) - self.kd * qd
        self.tau += self.a * (tau_pd - self.tau)
        motoring = self.tau * qd > 0
        lim = np.where(motoring, self.tau_max * np.clip(1.0 - np.abs(qd) / self.w_max, 0.0, 1.0),
                       self.tau_max)
        self.tau = np.clip(self.tau, -lim, lim)
        return self.tau


# ----------------------------------------------------------------------------- robot
class Robot:
    def __init__(self, tail=None, armature=0.12):
        self.tail_cfg = tail
        self.m, self.xml = build(tail, armature=armature)
        m = self.m
        self.has_tail = tail is not None
        self.leg_names = [f"{s}_{j}" for s in SIDES for j in LEG_JOINTS]
        self.leg_q = np.array([m.jnt_qposadr[m.joint(n).id] for n in self.leg_names])
        self.leg_v = np.array([m.jnt_dofadr[m.joint(n).id] for n in self.leg_names])
        self.leg_act = np.array([m.actuator(n).id for n in self.leg_names])
        self.pelvis = m.body("pelvis").id
        self.foot = {s: m.body(f"{s}_foot").id for s in SIDES}
        self.sole_geom = {s: m.geom(f"{s}_sole").id for s in SIDES}
        self.mass = float(m.body_subtreemass[self.pelvis])
        self.tail_q = np.array([], int)
        self.tail_v = np.array([], int)
        self.wheel_geoms = []
        if self.has_tail:
            names = [m.joint(i).name for i in range(m.njnt)]
            tj = [n for n in names if n.startswith("tail_j")]
            self.tail_q = np.array([m.jnt_qposadr[m.joint(n).id] for n in tj])
            self.tail_v = np.array([m.jnt_dofadr[m.joint(n).id] for n in tj])
            self.wheel_geoms = [m.geom(n).id for n in [m.geom(i).name for i in range(m.ngeom)]
                                if n.startswith("tail_wheel")]
            self.tail_geoms = [i for i in range(m.ngeom) if m.geom_bodyid[i] in
                               [m.body(n).id for n in [m.body(b).name for b in range(m.nbody)]
                                if n.startswith("tail")]]
            self.winch = m.actuator("tail_winch").id
            self.tail_base = m.body("tail_base").id
            self.tail_tip = m.body("tail_tip").id
            self.cable_k = m.actuator_gainprm[self.winch, 0]
            self.one_way = bool(tail.get("one_way", False))
            self.wheel_v = [m.jnt_dofadr[m.joint(n).id] for n in names if n.startswith("tail_wheel")]
            self.base_servo = "tail_pitch" in names
            self.tip_servo = any(m.actuator(i).name == "tail_tip" for i in range(m.nu))
            if self.base_servo:
                self.tail_pitch_act = m.actuator("tail_pitch").id
                self.tail_pitch_q = m.jnt_qposadr[m.joint("tail_pitch").id]
                self.tail_pitch_v = m.jnt_dofadr[m.joint("tail_pitch").id]
            if self.tip_servo:
                self.tail_tip_act = m.actuator("tail_tip").id
                self.tail_tipj_q = self.tail_q[-1]
                self.tail_tipj_v = self.tail_v[-1]
        self.geom_is_floor = m.geom("floor").id


# ----------------------------------------------------------------------------- IK
def rot_err(R, Rt):
    return 0.5 * (np.cross(R[:, 0], Rt[:, 0]) + np.cross(R[:, 1], Rt[:, 1]) + np.cross(R[:, 2], Rt[:, 2]))


class IK:
    """Damped least squares whole-body IK: feet poses, COM xy, pelvis height and attitude."""

    def __init__(self, robot):
        self.r = robot
        self.m = robot.m
        self.d = mujoco.MjData(self.m)
        self.dofs = np.r_[0:6, robot.leg_v]
        nv = self.m.nv
        self.jp = np.zeros((3, nv))
        self.jr = np.zeros((3, nv))
        self.jc = np.zeros((3, nv))
        self.full = np.zeros(nv)
        self.W = np.diag([1, 1, 1, .3, .3, .3] * 2 + [1, 1] + [1] + [.3, .3, .3])
        jids = [self.m.joint(n).id for n in robot.leg_names]
        self.lo = self.m.jnt_range[jids, 0]
        self.hi = self.m.jnt_range[jids, 1]

    def solve(self, qpos_init, tgt, iters=2, tail_q=None):
        m, d, r = self.m, self.d, self.r
        d.qpos[:] = qpos_init
        if tail_q is not None and len(r.tail_q):
            d.qpos[r.tail_q] = tail_q
        for _ in range(iters):
            mujoco.mj_kinematics(m, d)
            mujoco.mj_comPos(m, d)
            rows, errs = [], []
            for s in SIDES:
                b = r.foot[s]
                mujoco.mj_jacBody(m, d, self.jp, self.jr, b)
                rows += [self.jp.copy(), self.jr.copy()]
                errs += [tgt[s + "_pos"] - d.xpos[b], rot_err(d.xmat[b].reshape(3, 3), np.eye(3))]
            mujoco.mj_jacSubtreeCom(m, d, self.jc, r.pelvis)
            rows.append(self.jc[:2].copy())
            errs.append(tgt["com"][:2] - d.subtree_com[r.pelvis][:2])
            b = r.pelvis
            mujoco.mj_jacBody(m, d, self.jp, self.jr, b)
            rows.append(self.jp[2:3].copy())
            errs.append([tgt["pz"] - d.xpos[b][2]])
            rows.append(self.jr.copy())
            errs.append(rot_err(d.xmat[b].reshape(3, 3), tgt.get("pR", np.eye(3))))
            J = np.vstack(rows)[:, self.dofs]
            e = np.concatenate(errs)
            JW = J.T @ self.W
            dq = np.linalg.solve(JW @ J + 1e-6 * np.eye(J.shape[1]), JW @ e)
            self.full[:] = 0
            self.full[self.dofs] = dq
            mujoco.mj_integratePos(m, d.qpos, self.full, 1.0)
            d.qpos[r.leg_q] = np.clip(d.qpos[r.leg_q], self.lo, self.hi)
        return d.qpos.copy()


# ----------------------------------------------------------------------------- planner
class Preview:
    """Kajita ZMP preview control on the cart-table model."""

    def __init__(self, zc, dt=0.01, horizon=1.6, Qe=1.0, R=1e-6):
        self.dt, self.zc = dt, zc
        A = np.array([[1, dt, dt * dt / 2], [0, 1, dt], [0, 0, 1]])
        B = np.array([[dt ** 3 / 6], [dt * dt / 2], [dt]])
        C = np.array([[1, 0, -zc / G]])
        At = np.block([[np.eye(1), C @ A], [np.zeros((3, 1)), A]])
        Bt = np.vstack([C @ B, B])
        It = np.array([[1], [0], [0], [0]])
        Q = np.zeros((4, 4))
        Q[0, 0] = Qe
        P = solve_discrete_are(At, Bt, Q, np.array([[R]]))
        S = np.linalg.inv(R + Bt.T @ P @ Bt)
        K = S @ Bt.T @ P @ At
        self.Gi = K[0, 0]
        self.Gx = K[0, 1:]
        Ac = At - Bt @ K
        X = -Ac.T @ P @ It
        N = int(horizon / dt)
        Gd = np.zeros(N)
        Gd[0] = -self.Gi
        for j in range(1, N):
            Gd[j] = (S @ Bt.T @ X)[0, 0]
            X = Ac.T @ X
        self.Gd = Gd
        self.N = N
        self.A, self.B, self.C = A, B, C

    def run(self, zmp_ref, x0):
        """zmp_ref: (T,) reference; returns com pos, vel, acc, zmp (T,)"""
        T = len(zmp_ref)
        pad = np.concatenate([zmp_ref, np.full(self.N, zmp_ref[-1])])
        x = np.array([x0, 0.0, 0.0])
        out = np.zeros((T, 4))
        esum = 0.0
        for k in range(T):
            p = (self.C @ x)[0]
            esum += p - zmp_ref[k]
            u = -self.Gi * esum - self.Gx @ x - self.Gd[1:] @ pad[k + 1:k + self.N]
            out[k] = [x[0], x[1], x[2], p]
            x = self.A @ x + self.B[:, 0] * u
        return out


def min_jerk(s):
    s = np.clip(s, 0, 1)
    return 10 * s ** 3 - 15 * s ** 4 + 6 * s ** 5


class GaitPlan:
    """Footsteps, swing trajectories and COM from ZMP preview control.

    mode: 'biped' | 'tail_narrow' | 'tail_wide'
    For tailed modes the total ZMP x goes smoothly behind the stance ankle
    (COM rides between foot and tail); for 'tail_wide' the lateral sway is
    reduced because the two tail wheels can carry roll moments.
    """

    def __init__(self, mode, zc, pz, n_steps=8, step_len=0.25, T_ss=0.6, T_ds=0.2,
                 width=2 * HIP_HALF_W, h_swing=0.06, t_start=2.5, t_end=2.0, dt=0.01,
                 back=0.10, sway_wide=0.25, zmp_in=0.015):
        self.mode, self.zc, self.pz, self.dt = mode, zc, pz, dt
        self.T_ss, self.T_ds, self.h = T_ss, T_ds, h_swing
        hw = width / 2
        # footsteps: list of (side, x, y). Start: both at x=0. Right steps first.
        steps = []
        x_l, x_r = 0.0, 0.0
        side = "r"
        for k in range(n_steps):
            if k == n_steps - 1:  # last step: bring feet together
                nx = x_l if side == "r" else x_r
            else:
                other = x_l if side == "r" else x_r
                nx = other + step_len if k > 0 else step_len / 2 + 0.0
                if k == 0:
                    nx = step_len / 2
            steps.append((side, nx))
            if side == "r":
                x_r = nx
            else:
                x_l = nx
            side = "l" if side == "r" else "r"
        self.steps = steps
        T_step = T_ss + T_ds
        self.t_start = t_start
        self.t_walk_end = t_start + n_steps * T_step
        self.T_total = self.t_walk_end + t_end
        t = np.arange(0, self.T_total, dt)
        self.t = t
        n = len(t)
        # feet trajectories (ankle positions)
        lf = np.zeros((n, 3))
        rf = np.zeros((n, 3))
        lf[:, 1], rf[:, 1] = hw, -hw
        lf[:, 2] = rf[:, 2] = ANKLE_H
        contact = np.ones((n, 2), bool)   # l, r
        xl, xr = 0.0, 0.0
        stance_x = np.zeros(n)
        stance_y = np.zeros(n)
        phase = np.zeros(n, int)          # 0 DS, 1 SS
        for k, (s, nx) in enumerate(steps):
            t0 = t_start + k * T_step
            t1 = t0 + T_ss
            idx = (t >= t0) & (t < t1)
            tau = (t[idx] - t0) / T_ss
            src = xl if s == "l" else xr
            traj = lf if s == "l" else rf
            traj[idx, 0] = src + (nx - src) * min_jerk(tau)
            traj[idx, 2] = ANKLE_H + h_swing * np.sin(np.pi * tau) ** 2 * (1 if nx != src else 0.5)
            traj[t >= t1, 0] = nx
            if s == "l":
                xl = nx
            else:
                xr = nx
            contact[idx, 0 if s == "l" else 1] = False
            phase[idx] = 1
            # positions after step stay
            if s == "l":
                lf[t >= t1, 0] = nx
            else:
                rf[t >= t1, 0] = nx
        self.lf, self.rf, self.contact, self.phase = lf, rf, contact, phase

        # ZMP reference ------------------------------------------------------
        # anchor points (time, x, y) then linear interpolation
        sole = SOLE_CX - 0.02
        anchors = [(0.0, sole, 0.0)]
        xl, xr = 0.0, 0.0
        tail = mode.startswith("tail")
        sway = 1.0
        if mode == "tail_wide":
            sway = sway_wide
        yin = hw - zmp_in
        if tail:
            anchors = [(0.0, sole, 0.0), (t_start - 1.7, sole, 0.0), (t_start - 0.7, -back, 0.0)]
        else:
            anchors = [(0.0, sole, 0.0), (2.0, sole, 0.0)]
        for k, (s, nx) in enumerate(steps):
            t0 = t_start + k * T_step
            t1 = t0 + T_ss
            st = "r" if s == "l" else "l"
            sx = xr if st == "r" else xl
            sy = (-yin if st == "r" else yin) * sway
            if tail:
                # continuous: COM goes from (sx - back + d/2) to (sx - back - d/2) ... use mid
                anchors.append((t0 + T_ss / 2, sx - back + step_len * 0.0, sy))
            else:
                anchors += [(t0, sx + sole, sy), (t1, sx + sole, sy)]
            if s == "l":
                xl = nx
            else:
                xr = nx
        xe = max(xl, xr)
        if tail:
            anchors += [(self.t_walk_end, xe - back, 0.0), (self.T_total, xe - back, 0.0)]
        else:
            anchors += [(self.t_walk_end, xe + sole, 0.0), (self.T_total, xe + sole, 0.0)]
        at = np.array([a[0] for a in anchors])
        ax = np.array([a[1] for a in anchors])
        ay = np.array([a[2] for a in anchors])
        if tail:
            # tailed: smooth x progression, y holds at stance value during SS
            zx = np.interp(t, at, ax)
            zy = np.zeros(n)
            # lateral: hold during SS, ramp during DS
            yan = [(0, 0.0), (t_start, 0.0)]
            xl_, xr_ = 0.0, 0.0
            for k, (s, nx) in enumerate(steps):
                t0 = t_start + k * T_step
                st = "r" if s == "l" else "l"
                sy = (-yin if st == "r" else yin) * sway
                yan += [(t0, sy), (t0 + T_ss, sy)]
            yan += [(self.t_walk_end, 0.0), (self.T_total, 0.0)]
            # first DS ramp: shift earlier
            yan[1] = (t_start - T_ds, 0.0)
            zy = np.interp(t, [a[0] for a in yan], [a[1] for a in yan])
        else:
            # biped: also first lateral shift starts T_ds before first lift
            at[1] = t_start - T_ds - 0.3 if len(at) > 1 else at[1]
            zx = np.interp(t, at, ax)
            zy = np.interp(t, at, ay)
            zy[t < t_start - T_ds] = 0.0
            zy = np.interp(t, np.r_[0, t_start - T_ds, at[2:]], np.r_[0, 0, ay[2:]])
        self.zmp = np.stack([zx, zy], 1)
        pv = Preview(zc, dt)
        cx = pv.run(zx, zx[0])
        cy = pv.run(zy, 0.0)
        self.com = np.stack([cx[:, 0], cy[:, 0]], 1)
        self.comv = np.stack([cx[:, 1], cy[:, 1]], 1)
        self.zmp_lipm = np.stack([cx[:, 3], cy[:, 3]], 1)

    def at(self, tt):
        k = min(int(tt / self.dt), len(self.t) - 2)
        a = (tt - self.t[k]) / self.dt
        a = min(max(a, 0.0), 1.0)
        lerp = lambda X: X[k] * (1 - a) + X[k + 1] * a
        return dict(com=lerp(self.com), comv=lerp(self.comv), zmp=lerp(self.zmp),
                    l_pos=lerp(self.lf), r_pos=lerp(self.rf), contact=self.contact[k], phase=self.phase[k])


# ----------------------------------------------------------------------------- contacts
def contact_summary(r, m, d):
    """Return total normal force and CoP for feet and for tail wheels (+ tail geoms)."""
    f6 = np.zeros(6)
    feet_f, feet_p = 0.0, np.zeros(3)
    tail_f, tail_p = 0.0, np.zeros(3)
    tail_set = set(getattr(r, "tail_geoms", []))
    for i in range(d.ncon):
        c = d.contact[i]
        g = c.geom1 if c.geom2 == r.geom_is_floor else c.geom2
        mujoco.mj_contactForce(m, d, i, f6)
        fn = f6[0]
        if g in tail_set:
            tail_f += fn
            tail_p += fn * c.pos
        else:
            feet_f += fn
            feet_p += fn * c.pos
    return feet_f, (feet_p / feet_f if feet_f > 1e-6 else feet_p), tail_f, (tail_p / tail_f if tail_f > 1e-6 else tail_p)


# ----------------------------------------------------------------------------- runner
class Sim:
    def __init__(self, robot, servo, plan, stab_k=1.0, push=None, noise=0.0, seed=0,
                 tail_alpha=None, foot_cop_des=0.03, ctrl_dt=0.002, log_every=10,
                 winch_rate=0.10, record=False, tail_pitch_servo=None, winch_tau=0.3,
                 passive_ankle_roll=False, passive_k=150.0, passive_b=6.0):
        self.r, self.spec, self.plan = robot, servo, plan
        self.m = robot.m
        self.d = mujoco.MjData(self.m)
        self.est = mujoco.MjData(self.m)
        self.dt = self.m.opt.timestep
        self.ctrl_every = int(round(ctrl_dt / self.dt))
        self.servos = ServoBank(servo, self.dt)
        self.ik = IK(robot)
        self.stab_k = stab_k
        self.push = push or []          # list of (t, duration, force xyz)
        self.rng = np.random.default_rng(seed)
        self.noise = noise
        self.tail_alpha = tail_alpha
        self.foot_cop_des = foot_cop_des
        self.log_every = log_every
        self.winch_rate = winch_rate      # m/s cable take-up rate limit
        self.winch_tau = winch_tau        # s, time constant of the slow tail-load loop
        self.tail_loaded = False
        self.passive = np.array([4, 9]) if passive_ankle_roll else np.array([], int)
        self.passive_k, self.passive_b = passive_k, passive_b
        self.dbg = []
        self._tip_x_prev = 0.0
        self.record = record
        self.tail_pitch_servo = tail_pitch_servo
        lat_steps = int(round(servo.latency / self.dt))
        self.n_sense = lat_steps // 2
        self.n_cmd = lat_steps - self.n_sense
        self.omega = np.sqrt(G / plan.zc)

    def initial_qpos(self):
        p = self.plan.at(0.0)
        q0 = self.m.qpos0.copy()
        q0[2] = self.plan.pz
        q0[self.r.leg_q] = np.tile([0.0, -0.35, 0.7, -0.35, 0.0], 2)
        if self.r.has_tail:
            q0[self.r.tail_q] = self.m.jnt_range[[self.m.jnt_qposadr.tolist().index(a) for a in self.r.tail_q], 1] * 0 + 0.9
        tgt = dict(l_pos=p["l_pos"], r_pos=p["r_pos"], com=np.r_[p["com"], 0], pz=self.plan.pz)
        q = self.ik.solve(q0, tgt, iters=30)
        return q

    def run(self, T=None, stop_on_fall=True):
        m, d, r = self.m, self.d, self.r
        plan = self.plan
        T = T or plan.T_total
        q = self.initial_qpos()
        d.qpos[:] = q
        d.qvel[:] = 0
        mujoco.mj_forward(m, d)
        # put feet exactly on the floor
        zmin = min(d.geom_xpos[r.sole_geom[s]][2] - ANKLE_H / 2 for s in SIDES)
        d.qpos[2] -= zmin - 0.0005
        mujoco.mj_forward(m, d)
        n_steps = int(T / self.dt)
        hist_q = np.zeros((n_steps + 1, m.nq))
        hist_v = np.zeros((n_steps + 1, m.nv))
        q_cmd0 = d.qpos[r.leg_q].copy()
        cmd_buf = [q_cmd0.copy() for _ in range(self.n_cmd + 1)]
        q_ik = d.qpos.copy()
        q_cmd = q_cmd0.copy()
        dc = np.zeros(2)
        # tail
        u_winch = 0.0
        if r.has_tail:
            # start slack: cable length at curled pose
            u_winch = -r.m.tendon_length0[0] if False else 0.0
            mujoco.mj_forward(m, d)
            L = d.ten_length[0]
            u_winch = L - 1.0 / r.cable_k * 0.0   # zero tension
        log = []
        frames = []
        fell = False
        t_fall = None
        peak = dict(tau=np.zeros(10), w=np.zeros(10), pow=np.zeros(10))
        tau_rms = np.zeros(10)
        n_rms = 0
        winch_F_peak = 0.0
        winch_travel = 0.0
        for k in range(n_steps):
            t = k * self.dt
            hist_q[k] = d.qpos
            hist_v[k] = d.qvel
            if k % self.ctrl_every == 0:
                ko = max(0, k - self.n_sense)
                self.est.qpos[:] = hist_q[ko]
                self.est.qvel[:] = hist_v[ko]
                mujoco.mj_forward(m, self.est)
                mujoco.mj_subtreeVel(m, self.est)
                c_m = self.est.subtree_com[r.pelvis][:2].copy()
                v_m = self.est.subtree_linvel[r.pelvis][:2].copy()
                if self.noise:
                    v_m += self.rng.normal(0, self.noise, 2)
                to = ko * self.dt
                p = plan.at(to)
                # account for stance-foot placement error (measured vs planned)
                cl, cr = p["contact"]
                off = np.zeros(2)
                nst = 0
                for s, cflag in (("l", cl), ("r", cr)):
                    if cflag:
                        off += self.est.xpos[r.foot[s]][:2] - p[s + "_pos"][:2]
                        nst += 1
                off /= max(nst, 1)
                xi_m = c_m - off + v_m / self.omega
                xi_r = p["com"] + p["comv"] / self.omega
                err = xi_m - xi_r
                # stabilizer: lean against DCM error (shifts ZMP the right way)
                dc_t = -self.stab_k * err
                dc += 0.2 * (np.clip(dc_t, -0.08, 0.08) - dc)
                pn = plan.at(t + self.n_cmd * self.dt)   # command for when it arrives
                tgt = dict(l_pos=pn["l_pos"], r_pos=pn["r_pos"], com=np.r_[pn["com"] + dc, 0], pz=plan.pz)
                tq = self.est.qpos[r.tail_q] if r.has_tail else None
                q_ik = self.ik.solve(q_ik, tgt, iters=2, tail_q=tq)
                q_cmd = q_ik[r.leg_q].copy()
                # tail winch: slow force loop to carry share alpha of weight
                if r.has_tail:
                    cs = contact_summary(r, m, d)   # tail load cell (current reading)
                    alpha = self.tail_alpha_plan(to, pn)
                    F_des = alpha * r.mass * G
                    F_t = cs[2]
                    # slow integral on cable length, rate-limited
                    dtc = self.ctrl_every * self.dt
                    du = np.clip(dtc * (F_des - F_t) / (0.1 * r.cable_k * self.winch_tau),
                                 -self.winch_rate * dtc, self.winch_rate * dtc)
                    if F_t < 0.3 * F_des and not self.tail_loaded:
                        # deploy: take up any slack, then wind in at full speed
                        u_winch = max(u_winch, d.ten_length[0])
                        du = self.winch_rate * dtc
                    else:
                        self.tail_loaded = True
                    if t < 0.3:
                        du = 0.0
                    u_winch += du
                    d.ctrl[r.winch] = u_winch
                    if k % 100 == 0:
                        self.dbg.append((t, u_winch, d.ten_length[0], d.actuator_force[r.winch], F_t, F_des, self.tail_loaded))
                    if r.base_servo and self.tail_pitch_servo is not None:
                        d.ctrl[r.tail_pitch_act] = self.tail_pitch_servo(self, t, p)
                cmd_buf.append(q_cmd)
                if len(cmd_buf) > self.n_cmd // self.ctrl_every + 2:
                    cmd_buf.pop(0)
            # servo sees command issued ~n_cmd steps ago
            idx = max(0, len(cmd_buf) - 1 - self.n_cmd // self.ctrl_every)
            qc = cmd_buf[idx]
            qj = d.qpos[r.leg_q]
            vj = d.qvel[r.leg_v]
            tau = self.servos.step(qc, qj, vj)
            if len(self.passive):
                # unactuated joint: spring-damper to neutral, no servo
                tau[self.passive] = -self.passive_k * qj[self.passive] - self.passive_b * vj[self.passive]
            d.ctrl[r.leg_act] = tau
            # pushes
            d.xfrc_applied[r.pelvis] = 0
            for (tp, dur, F) in self.push:
                if tp <= t < tp + dur:
                    d.xfrc_applied[r.pelvis, :3] = F
            if r.has_tail and r.one_way:
                vx = d.cvel[r.tail_tip][3:6]   # not used directly; use finite tip velocity below
                vtip = (d.xpos[r.tail_tip][0] - self._tip_x_prev) / self.dt
                self._tip_x_prev = d.xpos[r.tail_tip][0]
                bd = 200.0 if (vtip < -0.002 and k > 0) else 0.02   # implicit damping = clutch
                m.dof_damping[r.wheel_v] = bd
            mujoco.mj_step(m, d)
            if t > 0.5:
                at = np.abs(tau)
                peak["tau"] = np.maximum(peak["tau"], at)
                peak["w"] = np.maximum(peak["w"], np.abs(vj))
                peak["pow"] = np.maximum(peak["pow"], tau * vj)
                tau_rms += tau ** 2
                n_rms += 1
                if r.has_tail:
                    winch_F_peak = max(winch_F_peak, float(d.actuator_force[r.winch]))
            if k % self.log_every == 0:
                fs = contact_summary(r, m, d)
                log.append(np.r_[t, d.subtree_com[r.pelvis], plan.at(t)["com"], fs[0], fs[1][:2], fs[2], fs[3][:2],
                                 d.qpos[r.leg_q], tau, (d.actuator_force[r.winch] if r.has_tail else 0.0),
                                 d.qpos[3:7]])
            if self.record and k % 33 == 0:
                frames.append(d.qpos.copy())
            # fall detection
            zup = d.xmat[r.pelvis].reshape(3, 3)[2, 2]
            if d.qpos[2] < 0.45 or zup < 0.6:
                fell = True
                t_fall = t
                if stop_on_fall:
                    break
        self.log = np.array(log)
        self.frames = frames
        tau_rms = np.sqrt(tau_rms / max(n_rms, 1))
        com_final = d.subtree_com[r.pelvis].copy()
        return dict(fell=fell, t_fall=t_fall, peak_tau=peak["tau"], peak_w=peak["w"], peak_pow=peak["pow"],
                    rms_tau=tau_rms, winch_F_peak=winch_F_peak, com_final=com_final,
                    dist=float(com_final[0]))

    def tail_alpha_plan(self, t, p):
        """Tail share of weight so that the feet CoP sits near the stance ankle."""
        if self.tail_alpha is not None:
            return self.tail_alpha
        cl, cr = p["contact"]
        xs = [p[s + "_pos"][0] for s, c in (("l", cl), ("r", cr)) if c]
        x_fd = np.mean(xs) + self.foot_cop_des
        x_t = self.d.xpos[self.r.tail_tip][0]
        a = (x_fd - p["com"][0]) / max(x_fd - x_t, 0.3)
        return float(np.clip(a, 0.03, 0.6))
