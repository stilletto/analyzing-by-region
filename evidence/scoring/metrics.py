#!/usr/bin/env python3
"""Compute arm metrics from judge verdict files. No API needed.

Verdict file format (written by a judge agent):
  {"<arm>/<rep>/<agent>": {"<key_id>": true|false, ...}, ...}
"""
import itertools, json, pathlib, statistics, sys

ROOT = pathlib.Path(__file__).resolve().parent
KEY_IDS = ["bp-as-percent", "cumulative-as-delta", "utc-vs-local", "clamp-negative",
           "double-rounding", "credit-order", "tenant-leak", "guard-bypass",
           "idem-key-mutable", "breaker-asymmetry", "validate-before-normalize",
           "retry-nonidempotent"]
DECOY_IDS = ["decoy-sql", "decoy-bare-except", "decoy-cache-growth", "decoy-eq-compare"]


def load(paths):
    v = {}
    for p in paths:
        v.update(json.loads(pathlib.Path(p).read_text()))
    return v


def arm_reps(verdicts, arm):
    """Group agent verdicts by rep -> list of found-sets."""
    reps = {}
    for k, found in verdicts.items():
        a, rep, agent = k.split("/")
        if a != arm:
            continue
        reps.setdefault(rep, []).append({i for i in KEY_IDS if found.get(i)})
    return reps


def decoy_rate(verdicts, arm):
    """Mean number of decoys an agent in this arm wrongly asserts as a defect."""
    hits, agents = 0, 0
    for k, found in verdicts.items():
        if k.split("/")[0] != arm:
            continue
        agents += 1
        hits += sum(1 for d in DECOY_IDS if found.get(d))
    return hits / agents if agents else float("nan")


def summarise(verdicts, arm):
    n = len(KEY_IDS)
    rows = []
    for rep, sets in sorted(arm_reps(verdicts, arm).items()):
        union = set().union(*sets)
        rare = {i for i in union if sum(i in s for s in sets) == 1}
        pairs = list(itertools.combinations(sets, 2))
        jac = statistics.mean(len(a & b) / len(a | b) for a, b in pairs) if pairs else float("nan")
        rows.append({"rep": rep, "union": len(union) / n,
                     "mean": statistics.mean(len(s) for s in sets) / n,
                     "rare": len(rare) / max(len(union), 1), "jac": jac,
                     "missed": sorted(set(KEY_IDS) - union)})
    return rows


def main():
    verdicts = load(sys.argv[1:])
    arms = sorted({k.split("/")[0] for k in verdicts})
    print(f"{'arm':8} {'rep':6} {'union':>6} {'mean':>6} {'rare':>6} {'jacc':>6}")
    print("-" * 42)
    agg = {}
    for arm in arms:
        rows = summarise(verdicts, arm)
        for r in rows:
            print(f"{arm:8} {r['rep']:6} {r['union']:6.2f} {r['mean']:6.2f} "
                  f"{r['rare']:6.2f} {r['jac']:6.2f}")
        agg[arm] = {f: statistics.mean(r[f] for r in rows) for f in ("union", "mean", "rare", "jac")}
        agg[arm]["decoys_per_agent"] = decoy_rate(verdicts, arm)
        agg[arm]["reps"] = len(rows)
        sd = statistics.stdev([r["union"] for r in rows]) if len(rows) > 1 else 0.0
        agg[arm]["union_sd"] = sd
        print(f"{arm:8} {'AVG':6} {agg[arm]['union']:6.2f} {agg[arm]['mean']:6.2f} "
              f"{agg[arm]['rare']:6.2f} {agg[arm]['jac']:6.2f}   (union sd {sd:.3f}, "
              f"decoys/agent {agg[arm]['decoys_per_agent']:.2f}/4)")
        print("-" * 42)

    if "A2" in agg and "A2b" in agg:
        floor = abs(agg["A2"]["union"] - agg["A2b"]["union"])
        print(f"\nNOISE FLOOR  |A2 - A2b| union = {floor:.3f}")
        print("Any arm-vs-arm gap at or below this is not a result.")
        if "A2pos" in agg:
            lift = agg["A2pos"]["union"] - agg["A2"]["union"]
            print(f"POSITIVE CTL  A2pos - A2 union = {lift:+.3f}"
                  f"   -> {'SEPARATES' if lift > floor else 'DOES NOT SEPARATE - harness is dead'}")

    # what nobody ever finds: the visible part of the reference-set ceiling
    never = set(KEY_IDS)
    for k, found in verdicts.items():
        never -= {i for i in KEY_IDS if found.get(i)}
    print(f"\nFound by NO agent in any arm: {sorted(never) if never else '(none)'}")
    (ROOT / "runs_metrics.json").write_text(json.dumps(agg, indent=1))


if __name__ == "__main__":
    main()
