"""Confirm complete torque sets: all five joints limited at once, pushes at three gait phases."""
import itertools, time
import numpy as np
from experiments import run_many, save

BASE = np.array([200, 250, 250, 180, 120], float)
V = {"A_biped": ({}, {}), "B1_tail_narrow@10": (dict(back=0.1), dict(tail_alpha=0.12)),
     "B2_tail_wide@10": (dict(back=0.1), dict(tail_alpha=0.12)), "B2_tail_wide@15": (dict(back=0.15), dict(tail_alpha=0.17))}
SETS = {  # hip_roll, hip_pitch, knee, ankle_pitch, ankle_roll  (N*m)
    "A_biped": [[75, 60, 125, 90, 25], [90, 75, 160, 100, 35]],
    "B1_tail_narrow@10": [[30, 90, 90, 35, 15], [40, 110, 110, 45, 20]],
    "B2_tail_wide@10": [[40, 110, 90, 35, 25], [50, 130, 110, 45, 30]],
    "B2_tail_wide@15": [[30, 130, 90, 35, 15], [40, 160, 110, 45, 20]],
}


def cases():
    out = []
    for name, (g, sm) in V.items():
        vn = name.split("@")[0]
        for si, st in enumerate(SETS[name]):
            for dt, k in itertools.product([-0.3, 0.0, 0.3], [0.5, 1.0]):
                push = [(2.6 + dt, 0.2, [60, 0, 0]), (4.2 + dt, 0.2, [0, 50, 0])]
                out.append(dict(exp="confirm", variant=vn, gait=dict(g), sim=dict(sm, stab_k=k),
                                servo=dict(torque=(np.array(st) / BASE).tolist(), latency=0.005),
                                push=push, pname="push", set=st, set_i=si, dt=dt, x=si))
    return out


if __name__ == "__main__":
    C = cases(); print(len(C), "cases", flush=True); t = time.time()
    R = run_many(C); save(R, "results/confirm.json"); print("done %.0fs" % (time.time() - t))
