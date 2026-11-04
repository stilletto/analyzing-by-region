"""Extra experiments: fewer servos (passive ankle roll), a 'budget servo' class, faster walking."""
import itertools, time, os
from experiments import run_many, save

V = [("A_biped", {}, {}),
     ("B1_tail_narrow", dict(back=0.1), dict(tail_alpha=0.12)),
     ("B2_tail_wide", dict(back=0.1), dict(tail_alpha=0.12)),
     ("B2_tail_wide", dict(back=0.15), dict(tail_alpha=0.17))]
STD_PUSH = [(2.6, 0.2, [60, 0, 0]), (4.2, 0.2, [0, 50, 0])]


def cases():
    out = []
    # 1. passive ankle roll (2 servos fewer)
    for (vn, g, sm), lat, k, pn in itertools.product(V, [0.005, 0.02, 0.04, 0.08], [0.5, 1.0], ["none", "push"]):
        out.append(dict(exp="passive_ankle", variant=vn, gait=dict(g), sim=dict(sm, stab_k=k, passive_ankle_roll=True),
                        servo=dict(latency=lat), push=STD_PUSH if pn == "push" else [], pname=pn, x=lat))
    # 2. budget class: slow (6 rad/s), laggy (5 ms motor lag), high latency, reduced torque
    for (vn, g, sm), lat, ts, k, pn in itertools.product(V, [0.02, 0.04, 0.08], [0.5, 0.4], [0.5, 1.0], ["none", "push"]):
        out.append(dict(exp="budget", variant=vn, gait=dict(g), sim=dict(sm, stab_k=k),
                        servo=dict(latency=lat, speed=0.3, torque=ts, t_motor=0.005), push=STD_PUSH if pn == "push" else [],
                        pname=pn, x=lat, ts=ts))
    # 3. faster walking (0.46 m/s): step 0.30 m, 0.5 s single + 0.15 s double support
    for (vn, g, sm), lat, k, pn in itertools.product(V, [0.005, 0.02, 0.04], [0.5, 1.0], ["none", "push"]):
        gg = dict(g, step_len=0.30, T_ss=0.5, T_ds=0.15)
        out.append(dict(exp="fast", variant=vn, gait=gg, sim=dict(sm, stab_k=k),
                        servo=dict(latency=lat), push=STD_PUSH if pn == "push" else [], pname=pn, x=lat))
    return out


if __name__ == "__main__":
    os.makedirs("results", exist_ok=True)
    C = cases()
    print(len(C), "cases", flush=True)
    t = time.time()
    R = run_many(C)
    save(R, "results/extra.json")
    print("done %.0fs" % (time.time() - t))
