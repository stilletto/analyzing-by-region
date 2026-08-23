#!/usr/bin/env python3
"""Score the three diverse tasks: no-skill vs self-partition vs partitioned pair.

Reports per task: A1,A2 = no skill.  B1,B2 = one agent, self-partitioned passes.
                  C1,C2 = two agents, one region each (scored as their UNION).
"""
import itertools, json, pathlib, statistics, sys

ROOT = pathlib.Path("/tmp/claude-1000/-home-stilletto-outpainting-skill-writer/"
                    "75b7e04e-aa6f-4c78-9d37-0639de8babed/scratchpad/div")
TOK = {
 "T1": {"A1":51547,"A2":54751,"B1":57553,"B2":57925,"C1":55121,"C2":67881},
 "T2": {"A1":60230,"A2":60307,"B1":74282,"B2":77200,"C1":58092,"C2":57249},
 "T3": {"A1":63169,"A2":62574,"B1":74258,"B2":68823,"C1":61683,"C2":61853},
}


def load(task):
    v = {}
    for f in sorted((ROOT / task).glob("score_*.json")):
        for k, m in json.loads(f.read_text()).items():
            v.setdefault(k, {}).update(m)
    return v


def main():
    print(f"{'task':5} {'condition':24} {'cov':>5} {'tokens':>8} {'cov/100k':>9}")
    print("-" * 58)
    per_cond = {}
    for task in ("T1", "T2", "T3"):
        v = load(task)
        if len(v) < 6:
            print(f"{task:5} -- incomplete ({sorted(v)})")
            continue
        ids = sorted(v["A1"]); n = len(ids)
        S = {k: {i for i in ids if v[k].get(i)} for k in v}
        rows = [
            ("1 agent, no skill",        [len(S["A1"]) / n, len(S["A2"]) / n],
             [TOK[task]["A1"], TOK[task]["A2"]]),
            ("1 agent, self-partition",  [len(S["B1"]) / n, len(S["B2"]) / n],
             [TOK[task]["B1"], TOK[task]["B2"]]),
            ("2 agents, partitioned",    [len(S["C1"] | S["C2"]) / n],
             [TOK[task]["C1"] + TOK[task]["C2"]]),
        ]
        for name, covs, toks in rows:
            c, t = statistics.mean(covs), statistics.mean(toks)
            print(f"{task:5} {name:24} {c:>5.2f} {t:>8,.0f} {c/t*1e5:>9.2f}")
            per_cond.setdefault(name, []).append(c)
        jc = len(S["C1"] & S["C2"]) / max(len(S["C1"] | S["C2"]), 1)
        ja = len(S["A1"] & S["A2"]) / max(len(S["A1"] | S["A2"]), 1)
        print(f"{'':5} {'  pool ' + str(n) + ' claims':24}   jaccard: pair {jc:.2f} vs "
              f"two free agents {ja:.2f}")
        print("-" * 58)

    print("\nAVERAGED ACROSS THE THREE TASKS")
    print(f"{'condition':24} {'cov':>5}  per-task")
    base = statistics.mean(per_cond.get("1 agent, no skill", [0]))
    for name, v in per_cond.items():
        m = statistics.mean(v)
        print(f"{name:24} {m:>5.2f}  {['%.2f' % x for x in v]}   {m-base:+.2f} vs no skill")


if __name__ == "__main__":
    main()
