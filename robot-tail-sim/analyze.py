"""Summarise results/sweeps.json -> results/summary.json (+ printed tables)."""
import json
import numpy as np
from collections import defaultdict

JOINTS = ["hip_roll", "hip_pitch", "knee", "ankle_pitch", "ankle_roll"]
BASE_TAU = np.array([200, 250, 250, 180, 120], float)
BASE_W = 20.0

# Actuators actually on sale (snapshot Oct-Nov 2026, reseller prices; see README for sources)
CATALOG = [
    # name, peak N*m, rated N*m, speed rad/s, price USD
    ("RobStride 03", 60, 20, 20.9, 235),
    ("RobStride 04", 120, 40, 20.9, 307),
    ("MyActuator X8-P20-120", 120, 43, 16.5, 645),
    ("Leadshine HJ2-110 (harmonic)", 194, 84, 4.2, 859),
    ("MyActuator X12-P20-320", 320, 85, 13.1, 1370),
    ("MyActuator X15-P20-450", 450, 145, 11.3, 1950),
]
MARGIN = 1.25


def key_of(c):
    v = c["variant"]
    b = c.get("gait", {}).get("back")
    return v if b is None else f"{v}@{int(round(b * 100))}cm"


LABELS = {
    "A_biped": "A: biped",
    "B1_tail_narrow@10cm": "B1: tail, one wheel (COM 10 cm back)",
    "B2_tail_wide@10cm": "B2: tail, two wheels (COM 10 cm back)",
    "B1_tail_narrow@15cm": "B1: tail, one wheel (COM 15 cm back)",
    "B2_tail_wide@15cm": "B2: tail, two wheels (COM 15 cm back)",
}


def pick(req_peak, req_rms, req_w):
    ok = [a for a in CATALOG if a[1] >= MARGIN * req_peak and a[2] >= MARGIN * req_rms and a[3] >= MARGIN * req_w]
    return min(ok, key=lambda a: a[4]) if ok else None


def load(paths=("results/sweeps.json", "results/extra2.json", "results/extra.json")):
    R = []
    for p in paths:
        try:
            R += json.load(open(p))
        except FileNotFoundError:
            pass
    return R


def joint_minima(R, keys):
    """Per joint: smallest tested torque limit (N*m) such that it and every larger tested limit passed with pushes."""
    out = {}
    for k in keys:
        rows = [c for c in R if c["exp"] == "joint_torque" and key_of(c) == k]
        if not rows:
            continue
        res = []
        for j in range(5):
            d = defaultdict(bool)
            for c in rows:
                if c["joint"] == j:
                    d[c["x"]] |= not c["fell"]
            best = None
            for x in sorted(d, reverse=True):
                if not d[x]:
                    break
                best = x
            res.append(dict(joint=JOINTS[j], min=best, tested=sorted(d.items())))
        out[k] = res
    return out


def main(path=None, out="results/summary.json"):
    R = load() if path is None else json.load(open(path))
    by = defaultdict(list)
    for c in R:
        by[(c["exp"], key_of(c))].append(c)
    keys = [k for k in LABELS if any(kk == k for (_, kk) in by)]
    S = dict(labels=LABELS, keys=keys)

    # latency tolerance: success if any stabilizer gain works
    lat = {}
    for k in keys:
        rows = by[("latency", k)]
        d = defaultdict(dict)
        for c in rows:
            ok = not c["fell"]
            d[c["pname"]][c["x"]] = d[c["pname"]].get(c["x"], False) or ok
        lat[k] = {p: sorted(v.items()) for p, v in d.items()}
    S["latency"] = lat

    def max_pass(pairs):
        """largest x such that every x' <= x passed (pairs sorted by x ascending)."""
        best = None
        for x, ok in pairs:
            if not ok:
                break
            best = x
        return best

    def min_pass(pairs):
        """smallest x such that every x' >= x passed (pairs sorted ascending)."""
        best = None
        for x, ok in sorted(pairs, reverse=True):
            if not ok:
                break
            best = x
        return best

    S["latency_max"] = {k: {p: max_pass(v) for p, v in lat[k].items()} for k in keys}

    # push tolerance
    push = {}
    for k in keys:
        push[k] = {}
        for dn in ["fwd", "back", "side"]:
            rows = by[("push_" + dn, k)]
            d = defaultdict(dict)
            for c in rows:
                L = c["servo"]["latency"]
                d[L][c["x"]] = d[L].get(c["x"], False) or (not c["fell"])
            push[k][dn] = {str(int(L * 1000)): max_pass(sorted(v.items())) for L, v in d.items()}
    S["push_max"] = push

    # torque / speed minimum scale
    for exp in ["torque", "speed"]:
        res = {}
        for k in keys:
            d = defaultdict(dict)
            for c in by[(exp, k)]:
                d[c["pname"]][c["x"]] = d[c["pname"]].get(c["x"], False) or (not c["fell"])
            res[k] = {p: dict(curve=sorted(v.items()), min=min_pass(sorted(v.items()))) for p, v in d.items()}
        S[exp] = res

    # nominal requirements (premium servos, 2 ms, no push, best of stabilizer gains = 0.5)
    nom = {}
    for k in keys:
        rows = [c for c in by[("latency", k)] if c["x"] == 0.002 and c["pname"] == "none" and not c["fell"]]
        rows.sort(key=lambda c: abs(c["sim"]["stab_k"] - 0.5))
        if rows:
            c = rows[0]
            nom[k] = dict(peak_tau=c["peak_tau"][:5], rms_tau=c["rms_tau"][:5], peak_w=c["peak_w"][:5],
                          tail_share=c.get("tail_share"), winch_F_peak=c.get("winch_F_peak"), mass=c["mass"])
    S["nominal"] = nom

    # requirements: per-joint minimum torque limit (with pushes) + RMS/speed from the full-torque pushed run
    jm = joint_minima(R, keys)
    S["joint_min"] = jm
    req = {}
    for k in keys:
        rows = [c for c in by[("torque", k)] if c["pname"] == "push" and not c["fell"] and c["x"] == 1.0]
        if not rows:
            continue
        full = min(rows, key=lambda c: sum(c["rms_tau"]))
        joints = []
        total = 0
        for j in range(5):
            mn = jm.get(k, [{}] * 5)[j].get("min")
            need = mn if mn is not None else full["peak_tau"][j]
            rm, w = full["rms_tau"][j], full["peak_w"][j]
            a = pick(need, rm, w)
            joints.append(dict(joint=JOINTS[j], need_peak=need, full_peak=full["peak_tau"][j], rms=rm, w=w,
                               pick=a[0] if a else None, price=a[4] if a else None))
            total += 2 * (a[4] if a else np.nan)
        req[k] = dict(joints=joints, legs_cost=total)
    S["requirements"] = req
    json.dump(S, open(out, "w"), indent=1, default=float)
    return S


def show(S):
    print("\n== latency tolerance (max latency where every smaller latency also passed) ==")
    for k in S["keys"]:
        print(f"  {LABELS[k]:45s}", {p: (None if v is None else f"{v*1000:.0f} ms") for p, v in S["latency_max"][k].items()})
    print("\n== max push impulse survived (N*s, 0.2 s push mid-walk) by latency ==")
    for k in S["keys"]:
        print(f"  {LABELS[k]:45s}", S["push_max"][k])
    for exp in ["torque", "speed"]:
        print(f"\n== minimum {exp} scale ==")
        for k in S["keys"]:
            print(f"  {LABELS[k]:45s}", {p: v["min"] for p, v in S[exp][k].items()})
    print("\n== nominal demand (premium servos) peak | rms N*m ==")
    for k, v in S["nominal"].items():
        print(f"  {LABELS[k]:45s}", np.round(v["peak_tau"]).astype(int), "|", np.round(v["rms_tau"]).astype(int),
              "w", np.round(v["peak_w"], 1), "tail", v["tail_share"])
    print("\n== actuator pick (pushes, smallest passing torque scale) ==")
    for k, v in S["requirements"].items():
        print(f"  {LABELS[k]} legs = ${v['legs_cost']:.0f}")
        for j in v["joints"]:
            print(f"     {j['joint']:12s} need {j['need_peak']:6.1f} (full-run peak {j['full_peak']:6.1f}) rms {j['rms']:5.1f} w {j['w']:4.1f} -> {j['pick']} ${j['price']}")


if __name__ == "__main__":
    show(main())
