"""Separate the effect of axle width from COM offset (B1 at 15 cm), and test a rear battery for hip load."""
import itertools, time, os
import numpy as np
from experiments import run_many, save

STD_PUSH = [(2.6, 0.2, [60, 0, 0]), (4.2, 0.2, [0, 50, 0])]


def cases():
    out = []
    vn, g, sm = "B1_tail_narrow", dict(back=0.15), dict(tail_alpha=0.17)
    for lat, k, pn in itertools.product([0.002, 0.01, 0.02, 0.03, 0.04, 0.06, 0.08, 0.10, 0.15, 0.20], [0.0, 0.5, 1.0], ["none", "push"]):
        out.append(dict(exp="latency", variant=vn, gait=dict(g), sim=dict(sm, stab_k=k), servo=dict(latency=lat),
                        push=STD_PUSH if pn == "push" else [], pname=pn, x=lat))
    dirs = {"fwd": [1, 0, 0], "back": [-1, 0, 0], "side": [0, 1, 0]}
    for dn, J, lat, k in itertools.product(dirs, [10, 20, 30, 40, 50, 60], [0.005, 0.04], [0.5, 1.0]):
        F = (np.array(dirs[dn]) * J / 0.2).tolist()
        out.append(dict(exp="push_" + dn, variant=vn, gait=dict(g), sim=dict(sm, stab_k=k), servo=dict(latency=lat),
                        push=[(2.6, 0.2, F)], pname="%s%d" % (dn, J), x=J))
    for ts, k in itertools.product([1.0, 0.7, 0.5, 0.4, 0.3], [0.5, 1.0]):
        out.append(dict(exp="torque", variant=vn, gait=dict(g), sim=dict(sm, stab_k=k), servo=dict(torque=ts, latency=0.005),
                        push=STD_PUSH, pname="push", x=ts))
    # rear battery: 8 kg at 20 cm or 10 kg at 40 cm behind the hip axis (trunk mass reduced by the same amount)
    for bat, k in itertools.product([None, (8.0, -0.20, 0.02), (10.0, -0.40, 0.0)], [0.5, 1.0]):
        out.append(dict(exp="battery", variant="B2_tail_wide", gait=dict(back=0.15), sim=dict(tail_alpha=0.17, stab_k=k),
                        servo=dict(latency=0.005), push=STD_PUSH, pname="push", battery=bat, x=0 if bat is None else bat[0]))
    return out


if __name__ == "__main__":
    C = cases()
    print(len(C), "cases", flush=True)
    t = time.time()
    R = run_many(C)
    save(R, "results/extra2.json")
    print("done %.0fs" % (time.time() - t))
