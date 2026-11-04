"""Batch experiments: one case = (robot variant, gait, servo class, disturbance)."""
import os
import json
import numpy as np
from multiprocessing import Pool

from sim import Robot, GaitPlan, Sim, ServoSpec, G

ZC = 0.904      # COM height of the crouched stance (pelvis 0.84 m)
PZ = 0.84

VARIANTS = {
    "A_biped": dict(tail=None, mode="biped"),
    "B1_tail_narrow": dict(tail=dict(tip="narrow"), mode="tail_narrow"),
    "B2_tail_wide": dict(tail=dict(tip="wide"), mode="tail_wide"),
}


def run_case(case):
    """case: dict with keys variant, servo (dict for ServoSpec.scaled), gait (dict), sim (dict), push list."""
    v = VARIANTS[case["variant"]]
    tail = None if v["tail"] is None else dict(v["tail"], **case.get("tail", {}))
    r = Robot(tail)
    gait = dict(case.get("gait", {}))
    if tail is not None:
        gait.setdefault("t_start", 4.5)
    plan = GaitPlan(v["mode"], ZC, PZ, **gait)
    base = ServoSpec()
    spec = base.scaled(**case.get("servo", {}))
    pushes = []
    for (tp, dur, F) in case.get("push", []):
        tp = tp + (plan.t_start if case.get("push_rel", True) else 0.0)
        pushes.append((tp, dur, np.array(F, float)))
    simkw = dict(case.get("sim", {}))
    s = Sim(r, spec, plan, push=pushes, **simkw)
    res = s.run()
    out = dict(case)
    out.update(fell=bool(res["fell"]), t_fall=res["t_fall"], dist=res["dist"],
               peak_tau=res["peak_tau"].tolist(), peak_w=res["peak_w"].tolist(),
               peak_pow=res["peak_pow"].tolist(), rms_tau=res["rms_tau"].tolist(),
               winch_F_peak=res["winch_F_peak"], mass=r.mass,
               tail_share=float(np.median(s.log[s.log[:, 0] > plan.t_start, 9]) / (r.mass * G)) if r.has_tail and not res["fell"] else None)
    return out


def run_many(cases, procs=4):
    with Pool(procs) as p:
        return p.map(run_case, cases)


def save(results, path):
    with open(path, "w") as f:
        json.dump(results, f, indent=1, default=float)
