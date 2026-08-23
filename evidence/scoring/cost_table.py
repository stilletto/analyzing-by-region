#!/usr/bin/env python3
"""Cost-efficiency of each fan-out condition on D2.

AGENT tokens only. Judge tokens are an artifact of measuring, not a cost of using the
technique, so they are excluded; they are reported separately at the bottom.
"""
# agent label -> tokens actually spent (from run notifications)
TOK = {
    "P1": 63436, "P2": 52758, "P3": 54165, "P4": 53761,
    "F": 65130,  "B": 56298,
    "PA": 74725, "PB": 60851, "PA2": 61858, "PB2": 67239,
    "Q1": 49674, "Q2": 62772, "Q3": 57471, "Q4": 68480,
}
# condition -> (coverage, [agent labels])
RUNS = [
    ("single free agent",        0.47, ["P1"]),
    ("single free agent",        0.49, ["P2"]),
    ("free pair",                0.60, ["P1", "P2"]),
    ("free pair",                0.51, ["P3", "P4"]),
    ("reframed pair",            0.55, ["F", "B"]),
    ("partitioned pair",         0.69, ["PA", "PB"]),
    ("partitioned pair",         0.65, ["PA2", "PB2"]),
    ("free quad",                0.63, ["P1", "P2", "P3", "P4"]),
    ("partitioned quad",         0.68, ["Q1", "Q2", "Q3", "Q4"]),
]


def main(extra=None):
    runs = RUNS + (extra or [])
    print(f"{'condition':22} {'cov':>5} {'tokens':>9} {'cov/100k':>9}  agents")
    print("-" * 66)
    agg = {}
    for name, cov, labels in runs:
        if not all(l in TOK for l in labels):
            print(f"{name:22}   -- token counts missing")
            continue
        t = sum(TOK[l] for l in labels)
        print(f"{name:22} {cov:>5.2f} {t:>9,} {cov/t*1e5:>9.2f}  {'+'.join(labels)}")
        agg.setdefault(name, []).append((cov, t))

    print(f"\n{'condition (averaged)':22} {'cov':>5} {'tokens':>9} {'cov/100k':>9}   vs best cov")
    print("-" * 70)
    best = max(sum(c for c, _ in v) / len(v) for v in agg.values())
    rows = []
    for name, v in agg.items():
        cov = sum(c for c, _ in v) / len(v)
        t = sum(t for _, t in v) / len(v)
        rows.append((cov / t * 1e5, cov, t, name))
    for eff, cov, t, name in sorted(rows, reverse=True):
        flag = "  <-- best efficiency" if eff == max(r[0] for r in rows) else ""
        star = "  <-- best coverage" if abs(cov - best) < 1e-9 else ""
        print(f"{name:22} {cov:>5.2f} {t:>9,.0f} {eff:>9.2f}   {cov/best:>5.0%}{star}{flag}")


if __name__ == "__main__":
    main()
