# analyzing-by-region on three diverse tasks — with vs without

T1 code (session/permissions subsystem, obvious seams), T2 prose (a six-week warehouse
cutover plan, NO obvious seams — the split was invented), T3 physical (gravity-fed
rainwater irrigation). Pools built from all six reports per task, single-pass verified,
then scored by 7 judges each seeing all six reports on their slice of the pool.

    condition                  T1 code  T2 plan  T3 physical   mean
    1 agent, no skill             0.51     0.35        0.52    0.46
    1 agent, self-partition       0.67     0.68        0.73    0.69   +0.23
    2 agents, partitioned         0.87     0.62        0.85    0.78   +0.32

    cost, coverage per 100k tokens
    1 agent, no skill             0.95     0.58        0.83
    1 agent, self-partition       1.16     0.89        1.03    <-- best on every task
    2 agents, partitioned         0.71     0.54        0.69

    pool sizes: 70 / 141 / 75 verified claims (286 total)
    verification drop rate: 23% / 16% / 23%

## 1. The skill holds across all three domains

Self-partitioning beat the bare agent on every task, by +0.16, +0.33 and +0.21. It is
also the best cost-efficiency on every task, which the D2 run could not show because
D2 had no no-skill comparison at matched question type.

**It removes variance, not just raises the mean.** Bare agents scored 0.51 / 0.35 / 0.52
— the prose plan is where a single balanced sweep is worst. With the instruction the same
agent scores 0.67 / 0.68 / 0.73. The floor moves much more than the ceiling: the skill's
real value is that the bad case stops being bad.

## 2. NEW: fan-out needs REAL seams; self-partitioning does not

The pair beat self-partitioning on code (0.87 vs 0.67) and on the physical design (0.85
vs 0.73) — and LOST on the prose plan (0.62 vs 0.68).

T2 is the task whose seams do not exist in the material; the "material vs people" split
was invented by the orchestrator. Pair jaccard was 0.02, so the two agents did separate
almost perfectly — they obeyed. But in a plan, most consequences ARE cross-region: data
problems cause schedule problems cause staffing problems. Splitting that across two
contexts left nobody able to join the ends. One agent taking both regions in succession
still holds both in one head.

**Rule, added to the skill:** if you had to invent the seams rather than read them off the
material, take the passes yourself and do not fan out.

## 3. Limits

- 2 reps for the single-agent conditions, 1 pair per task for the fan-out condition.
- Pools were verified in a single pass inside the pool builder, not by 3 independent
  refuters as on D2. Drop rates (16-23%) match D2's 18%, and contamination is symmetric
  across conditions, so differences are usable and absolute numbers are not.
- Each pool is built from the six reports being scored, so claims no report made are
  invisible. Coverage is coverage-of-what-was-said-by-someone.
- Opus 5 only.
