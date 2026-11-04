"""MJCF builder: human-proportioned biped (1.75 m, ~70 kg) with an optional tail.

Frames: x forward, y left, z up. Segment lengths and masses follow Winter's
anthropometric tables (fractions of height H and mass M).

Tail (when enabled) is a chain of segments hinged in the sagittal plane.
Each hinge can only CURL (tip goes up); at 0 rad it hits a hard stop and the
tail is straight. Springs curl the tail; one cable (fixed tendon over all
hinges) pulled by a slow winch straightens it. The winch is modelled as a
series-elastic position actuator on the cable: force = k*(u - L), cable can only
pull (force >= 0). So the more the winch winds in, the straighter/stiffer the
tail and the more body weight it carries.

Tail tip: one wheel (narrow) or two wheels on an axle (wide). Wheels roll
forward freely and resist sideways slip, so the tail can stay on the ground
while the robot walks.

Options for a second tail actuator:
  base_servo: hinge at the tail root (swings the whole tail in pitch)
  tip_servo : last hinge driven by its own servo instead of the cable
"""
import numpy as np

H = 1.75
M = 70.0

# Winter segment fractions
L_THIGH = 0.245 * H      # 0.429
L_SHANK = 0.246 * H      # 0.431
ANKLE_H = 0.039 * H      # 0.068
FOOT_L = 0.152 * H       # 0.266
FOOT_W = 0.055 * H       # 0.096
HIP_HALF_W = 0.09

M_THIGH = 0.100 * M
M_SHANK = 0.0465 * M
M_FOOT = 0.0145 * M
M_PELVIS = 0.142 * M
M_TRUNK = 0.355 * M
M_HEAD = 0.081 * M
M_ARM = 0.050 * M

LEG_JOINTS = ["hip_roll", "hip_pitch", "knee", "ankle_pitch", "ankle_roll"]
SIDES = ["l", "r"]

DEFAULT_TAIL = dict(
    tip="wide",          # "narrow" | "wide"
    n_seg=5,
    length=1.10,
    beta_deg=62.0,       # straight-tail angle below horizontal
    attach=(-0.11, 0.0, -0.02),
    seg_mass=0.40,
    tip_mass=0.50,
    base_mass=1.2,       # winch + bracket, added to pelvis
    curl_max=1.0,        # rad per hinge
    curl_k=15.0,         # N*m/rad curl spring per hinge
    curl_ref=0.9,        # spring rest angle (curled)
    cable_r=(0.10, 0.08, 0.06, 0.045, 0.03),   # cable moment arm per hinge, root -> tip (m)
    cable_k=4.0e5,       # series cable/spring stiffness (N/m)
    cable_fmax=4000.0,   # winch force limit (N)
    wheel_r=0.05,
    axle_half=0.22,      # wide tip: wheel at +-axle_half
    base_servo=False,
    tip_servo=False,
    one_way=False,       # wheels with a freewheel clutch: roll forward, lock backward
)


def _quat_y(theta):
    return (np.cos(theta / 2), 0.0, np.sin(theta / 2), 0.0)


def _fmt(v):
    return " ".join(f"{x:.6g}" for x in v)


def leg_xml(side):
    s = 1 if side == "l" else -1
    y = s * HIP_HALF_W
    foot_cx = 0.05
    return f"""
    <body name="{side}_thigh" pos="0 {y} 0">
      <joint name="{side}_hip_roll" axis="1 0 0" range="-0.5 0.5"/>
      <joint name="{side}_hip_pitch" axis="0 1 0" range="-1.9 0.7"/>
      <geom type="capsule" fromto="0 0 0 0 0 {-L_THIGH:.4f}" size="0.06" mass="{M_THIGH:.4f}" rgba=".55 .6 .7 1"/>
      <body name="{side}_shank" pos="0 0 {-L_THIGH:.4f}">
        <joint name="{side}_knee" axis="0 1 0" range="-0.05 2.4"/>
        <geom type="capsule" fromto="0 0 0 0 0 {-L_SHANK:.4f}" size="0.045" mass="{M_SHANK:.4f}" rgba=".55 .6 .7 1"/>
        <body name="{side}_foot" pos="0 0 {-L_SHANK:.4f}">
          <joint name="{side}_ankle_pitch" axis="0 1 0" range="-0.9 0.9"/>
          <joint name="{side}_ankle_roll" axis="1 0 0" range="-0.5 0.5"/>
          <geom name="{side}_sole" type="box" pos="{foot_cx} 0 {-ANKLE_H/2:.4f}"
                size="{FOOT_L/2:.4f} {FOOT_W/2:.4f} {ANKLE_H/2:.4f}" mass="{M_FOOT:.4f}" rgba=".3 .3 .35 1"/>
          <site name="{side}_sole_c" pos="{foot_cx} 0 {-ANKLE_H:.4f}" size="0.01"/>
        </body>
      </body>
    </body>"""


def tail_xml(t):
    beta = np.deg2rad(t["beta_deg"])
    n = t["n_seg"]
    ls = t["length"] / n
    parts = []
    head = f'<body name="tail_base" pos="{_fmt(t["attach"])}" quat="{_fmt(_quat_y(-beta))}">'
    parts.append(head)
    if t["base_servo"]:
        parts.append('<joint name="tail_pitch" axis="0 1 0" range="-0.7 0.7" armature="0.05" damping="1"/>')
    parts.append('<geom type="sphere" size="0.04" mass="0.1" rgba=".8 .5 .2 1" contype="0" conaffinity="0"/>')
    for i in range(n):
        pos = "0 0 0" if i == 0 else f"{-ls:.4f} 0 0"
        parts.append(f'<body name="tail{i}" pos="{pos}">')
        parts.append(
            f'<joint name="tail_j{i}" axis="0 1 0" range="0 {t["curl_max"]}" '
            f'stiffness="{t["curl_k"]}" springref="{t["curl_ref"]}" damping="1.5" armature="0.002"/>')
        parts.append(
            f'<geom type="capsule" fromto="0 0 0 {-ls:.4f} 0 0" size="0.03" mass="{t["seg_mass"]}" '
            f'friction="0.1 0.005 0.0001" priority="1" rgba=".85 .55 .25 1"/>')
    # tip: axle + wheel(s); wheels hinge about the tip's local y axis
    wr = t["wheel_r"]
    tip = [f'<body name="tail_tip" pos="{-ls:.4f} 0 0">']
    ys = [0.0] if t["tip"] == "narrow" else [-t["axle_half"], t["axle_half"]]
    if t["tip"] == "wide":
        tip.append(f'<geom type="capsule" fromto="0 {-t["axle_half"]} 0 0 {t["axle_half"]} 0" size="0.02" '
                   f'mass="{t["tip_mass"]*0.4:.3f}" friction="0.1 0.005 0.0001" priority="1" rgba=".85 .55 .25 1"/>')
    wm = t["tip_mass"] * (0.6 if t["tip"] == "wide" else 1.0) / len(ys)
    for k, y in enumerate(ys):
        tip.append(f'<body name="tail_wheel{k}" pos="0 {y} 0">'
                   f'<joint name="tail_wheel{k}" axis="0 1 0" damping="0.02" armature="0.0005" limited="false"/>'
                   f'<geom name="tail_wheel{k}" type="cylinder" size="{wr} 0.02" quat="0.7071068 0.7071068 0 0" '
                   f'mass="{wm:.3f}" friction="1.0 0.005 0.0001" priority="1" rgba=".15 .15 .15 1"/></body>')
    tip.append("</body>")
    parts.extend(tip)
    parts.extend(["</body>"] * n)
    parts.append("</body>")
    return "\n".join(parts)


def build_xml(tail=None, armature=0.05, joint_damping=0.5, z0=0.95, battery=None):
    """tail: None (biped) or dict overriding DEFAULT_TAIL.
    battery: None or (mass_kg, x, z) - that much trunk mass moved into a box on the pelvis."""
    t = None
    if tail is not None:
        t = dict(DEFAULT_TAIL)
        t.update(tail)
    pelvis_mass = M_PELVIS + (t["base_mass"] if t else 0.0)
    trunk_mass = M_TRUNK
    battery_geom = ""
    if battery:
        bm, bx, bz = battery
        trunk_mass -= bm
        battery_geom = (f'<geom name="battery" type="box" pos="{bx} 0 {bz}" size="0.06 0.12 0.08" '
                        f'mass="{bm}" rgba=".25 .25 .28 1"/>')
    legs = "\n".join(leg_xml(s) for s in SIDES)
    tailx = tail_xml(t) if t else ""
    motors = "\n".join(
        f'<motor name="{s}_{j}" joint="{s}_{j}" gear="1"/>' for s in SIDES for j in LEG_JOINTS)
    tendon = ""
    tail_act = ""
    if t:
        cable_joints = [f"tail_j{i}" for i in range(t["n_seg"])]
        if t["tip_servo"]:
            cable_joints = cable_joints[:-1]
        cr = t["cable_r"]
        if np.isscalar(cr):
            cr = [cr] * t["n_seg"]
        tj = "".join(f'<joint joint="{j}" coef="{-cr[i]}"/>' for i, j in enumerate(cable_joints))
        tendon = f'<tendon><fixed name="tail_cable">{tj}</fixed></tendon>'
        tail_act = (f'<position name="tail_winch" tendon="tail_cable" kp="{t["cable_k"]}" '
                    f'forcelimited="true" forcerange="0 {t["cable_fmax"]}" ctrllimited="false"/>')
        if t["base_servo"]:
            tail_act += '<motor name="tail_pitch" joint="tail_pitch" gear="1"/>'
        if t["tip_servo"]:
            tail_act += f'<motor name="tail_tip" joint="tail_j{t["n_seg"]-1}" gear="1"/>'

    xml = f"""
<mujoco model="biped{'_tail' if t else ''}">
  <compiler angle="radian" autolimits="true"/>
  <option timestep="0.001" integrator="implicitfast" cone="elliptic" impratio="2"/>
  <size memory="20M"/>
  <visual><global offwidth="1280" offheight="720"/><quality shadowsize="2048"/></visual>
  <default>
    <joint armature="{armature}" damping="{joint_damping}" limited="true"/>
    <geom contype="2" conaffinity="1" friction="1.0 0.005 0.0001" solref="0.004 1"/>
  </default>
  <asset>
    <texture name="grid" type="2d" builtin="checker" rgb1=".86 .88 .9" rgb2=".74 .77 .8" width="512" height="512"/>
    <material name="grid" texture="grid" texrepeat="8 8" reflectance="0.05"/>
    <texture type="skybox" builtin="gradient" rgb1=".93 .95 .98" rgb2=".62 .7 .8" width="256" height="256"/>
  </asset>
  <worldbody>
    <light pos="0 -2 4" dir="0 0.4 -1" directional="true" diffuse=".8 .8 .8"/>
    <geom name="floor" type="plane" size="60 10 0.1" material="grid" contype="1" conaffinity="1"/>
    <body name="pelvis" pos="0 0 {z0}">
      <freejoint name="root"/>
      <geom name="pelvis" type="box" size="0.08 0.14 0.06" mass="{pelvis_mass:.4f}" rgba=".35 .45 .6 1"/>
      <geom name="trunk" type="box" pos="0 0 0.30" size="0.10 0.16 0.22" mass="{trunk_mass:.4f}" rgba=".35 .45 .6 1"/>
      {battery_geom}
      <geom name="head" type="sphere" pos="0 0 0.66" size="0.10" mass="{M_HEAD:.4f}" rgba=".9 .8 .7 1"/>
      <geom name="larm" type="capsule" fromto="0 0.21 0.48 0 0.23 -0.08" size="0.04" mass="{M_ARM:.4f}" rgba=".55 .6 .7 1"/>
      <geom name="rarm" type="capsule" fromto="0 -0.21 0.48 0 -0.23 -0.08" size="0.04" mass="{M_ARM:.4f}" rgba=".55 .6 .7 1"/>
      <site name="imu" pos="0 0 0" size="0.01"/>
      {legs}
      {tailx}
    </body>
  </worldbody>
  {tendon}
  <actuator>
    {motors}
    {tail_act}
  </actuator>
</mujoco>"""
    return xml


def build(tail=None, **kw):
    import mujoco
    xml = build_xml(tail, **kw)
    m = mujoco.MjModel.from_xml_string(xml)
    return m, xml


if __name__ == "__main__":
    import mujoco
    for cfg in [None, dict(tip="narrow"), dict(tip="wide"), dict(tip="wide", base_servo=True)]:
        m, _ = build(cfg)
        d = mujoco.MjData(m)
        mujoco.mj_forward(m, d)
        print(cfg, "mass=%.2f kg" % m.body_subtreemass[1], "nq", m.nq, "nu", m.nu,
              "COM z=%.3f" % d.subtree_com[1][2])
