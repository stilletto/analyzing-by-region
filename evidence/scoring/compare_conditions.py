#!/usr/bin/env python3
"""Compare seeding conditions on D2. Reads judge verdict files, prints one table.

Usage: compare_conditions.py <verdict.json> [...]
Verdict files are {"<agent-label>": {"<claim-id>": bool}}, merged across pool halves.
"""
import itertools, json, pathlib, statistics, sys

# condition -> list of agent labels forming ONE group (a pair or a quad)
GROUPS = [
    ("free",       2, ["P1", "P2"]),
    ("free",       2, ["P3", "P4"]),
    ("reframe",    2, ["F", "B"]),
    ("partition",  2, ["PA", "PB"]),
    ("partition",  2, ["PA2", "PB2"]),
    ("free",       4, ["P1", "P2", "P3", "P4"]),
    ("partition",  4, ["Q1", "Q2", "Q3", "Q4"]),
]


def main():
    v = {}
    for f in sys.argv[1:]:
        for k, m in json.loads(pathlib.Path(f).read_text()).items():
            v.setdefault(k, {}).update(m)
    ids = sorted({c for m in v.values() for c in m})
    n = len(ids)

    print(f"pool = {n} verified claims\n")
    print(f"{'condition':12} {'n':>2} {'mean single':>12} {'UNION':>7} {'jacc':>6} {'rare':>6}  agents")
    print("-" * 74)
    rows = []
    for cond, k, labels in GROUPS:
        if not all(l in v for l in labels):
            print(f"{cond:12} {k:>2}   -- missing: {[l for l in labels if l not in v]}")
            continue
        sets = [{c for c in ids if v[l].get(c)} for l in labels]
        union = set().union(*sets)
        rare = {c for c in union if sum(c in s for s in sets) == 1}
        jac = statistics.mean(len(a & b) / len(a | b) for a, b in itertools.combinations(sets, 2))
        mean = statistics.mean(len(s) for s in sets) / n
        rows.append((cond, k, mean, len(union) / n, jac, len(rare) / len(union)))
        print(f"{cond:12} {k:>2} {mean:>12.2f} {len(union)/n:>7.2f} {jac:>6.2f} "
              f"{len(rare)/len(union):>6.0%}  {'+'.join(labels)}")

    print()
    for k in (2, 4):
        f = [r[3] for r in rows if r[0] == "free" and r[1] == k]
        p = [r[3] for r in rows if r[0] == "partition" and r[1] == k]
        if f and p:
            print(f"n={k}: partition {statistics.mean(p):.2f} vs free {statistics.mean(f):.2f}"
                  f"  ->  {statistics.mean(p)-statistics.mean(f):+.2f}"
                  + (f"   (free reps spread {max(f)-min(f):.2f}, "
                     f"partition reps spread {max(p)-min(p):.2f})" if len(f) > 1 or len(p) > 1 else ""))
    p2 = [r[3] for r in rows if r[0] == "partition" and r[1] == 2]
    p4 = [r[3] for r in rows if r[0] == "partition" and r[1] == 4]
    if p2 and p4:
        print(f"\nscaling: partition n=4 {statistics.mean(p4):.2f} vs n=2 {statistics.mean(p2):.2f}"
              f"  ->  {statistics.mean(p4)-statistics.mean(p2):+.2f}")


if __name__ == "__main__":
    main()
