"""Main sweeps: latency, push strength, torque limit, speed limit. Writes results/sweeps.json."""
import sys, time, itertools, os
import numpy as np
from experiments import run_many, save

V = [("A_biped", {}, {}),
     ("B1_tail_narrow", dict(back=0.1), dict(tail_alpha=0.12)),
     ("B2_tail_wide", dict(back=0.1), dict(tail_alpha=0.12)),
     ("B2_tail_wide", dict(back=0.15), dict(tail_alpha=0.17))]
STD_PUSH = [(2.6, 0.2, [60, 0, 0]), (4.2, 0.2, [0, 50, 0])]
STABS = [0.0, 0.5, 1.0]


def cases():
    out = []
    # 1. latency
    for (vn, g, sm), lat, k, pn in itertools.product(V, [0.002, 0.01, 0.02, 0.03, 0.04, 0.06, 0.08, 0.10, 0.15, 0.20],
                                                     STABS, ["none", "push"]):
        out.append(dict(exp="latency", variant=vn, gait=dict(g), sim=dict(sm, stab_k=k),
                        servo=dict(latency=lat), push=STD_PUSH if pn == "push" else [], pname=pn, x=lat))
    # 2. push strength (impulse over 0.2 s), mid-walk, direction
    dirs = {"fwd": [1, 0, 0], "back": [-1, 0, 0], "side": [0, 1, 0]}
    for (vn, g, sm), dn, J, lat, k in itertools.product(V, dirs, [10, 20, 30, 40, 50, 60], [0.005, 0.04], [0.5, 1.0]):
        F = (np.array(dirs[dn]) * J / 0.2).tolist()
        out.append(dict(exp="push_" + dn, variant=vn, gait=dict(g), sim=dict(sm, stab_k=k),
                        servo=dict(latency=lat), push=[(2.6, 0.2, F)], pname="%s%d" % (dn, J), x=J))
    # 3. torque scale
    for (vn, g, sm), ts, k, pn in itertools.product(V, [1.0, 0.7, 0.5, 0.4, 0.3, 0.25, 0.2], [0.5, 1.0], ["none", "push"]):
        out.append(dict(exp="torque", variant=vn, gait=dict(g), sim=dict(sm, stab_k=k),
                        servo=dict(torque=ts, latency=0.005), push=STD_PUSH if pn == "push" else [], pname=pn, x=ts))
    # 4. speed scale (w_max base 20 rad/s)
    for (vn, g, sm), ws, k, pn in itertools.product(V, [1.0, 0.5, 0.3, 0.2, 0.15, 0.1], [0.5, 1.0], ["none", "push"]):
        out.append(dict(exp="speed", variant=vn, gait=dict(g), sim=dict(sm, stab_k=k),
                        servo=dict(speed=ws, latency=0.005), push=STD_PUSH if pn == "push" else [], pname=pn, x=ws))
    return out


if __name__ == "__main__":
    os.makedirs("results", exist_ok=True)
    C = cases()
    print(len(C), "cases", flush=True)
    t = time.time()
    R = run_many(C)
    save(R, "results/sweeps.json")
    print("done %.0fs" % (time.time() - t))
