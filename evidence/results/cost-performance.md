# Cost vs performance, every variant. Agent tokens only (judging excluded).

    variant                    reps   cov    tokens  cov/100k   vs base   vs base cost
    4 agents, partitioned         1  0.68   238,397     0.29      +0.22       +325%
    2 agents, partitioned         2  0.67   132,336     0.51      +0.21       +136%
    1 agent, self-partition       2  0.64    91,324     0.70      +0.18        +63%
    4 agents, nothing             1  0.63   224,120     0.28      +0.17       +300%
    2 agents, nothing             2  0.55   112,060     0.50      +0.09       +100%
    2 agents, reframed            1  0.55   121,428     0.45      +0.09       +117%
    1 agent, nothing              4  0.46    56,030     0.83       0.00          0%
    1 agent, mental-simulation    2  0.42    69,928     0.59      -0.05        +25%

    MARGINAL return on upgrading from a bare single agent (0.46 @ 56,030 tokens)
    1 agent, self-partition     +0.18    +35,294    0.51 cov per 100k   <-- best buy
    2 agents, partitioned       +0.21    +76,306    0.27
    2 agents, nothing           +0.09    +56,030    0.17
    2 agents, reframed          +0.09    +65,398    0.13
    4 agents, partitioned       +0.22   +182,367    0.12
    4 agents, nothing           +0.17   +168,090    0.10
    1 agent, mental-simulation  -0.05    +13,898    negative

## 1. The INSTRUCTION carries the effect, not the fan-out

One agent told to make the two partitioned passes itself reaches 0.64 — **96% of the
partitioned pair's coverage for 69% of its tokens, and 94% of the partitioned quad's for
38%**. Its marginal return (0.51 coverage per 100k spent) is nearly double the next best
option.

Headline: **one self-partitioning agent matches four free agents at 41% of the cost**
(0.64 @ 91k vs 0.63 @ 224k).

The fan-out is not useless — a partitioned pair adds +0.03 over self-partitioning — but
that is the last three points for +45% tokens.

## 2. This refutes the main recommendation of analyzing-by-region as first written

The skill led with "give each agent a region" and never mentioned that one agent can take
all the regions itself. That was the expensive form as the default. Corrected: lead with
self-partitioning, present the fan-out as the paid upgrade, and give the numbers so the
reader can decide.

What survives unchanged: partition rather than reframe; "own this region, ignore the
rest, go deeper than usual"; union rather than vote; two regions rather than four; and
the over-splitting diagnostic.

## 3. mental-simulation is NOT validated by this instrument

0.42 against a 0.46 baseline, at +25% tokens. Marginal return is negative.

The caveats were pre-registered (section 10e.1) and stand: this metric scores enumerative
breadth, while the skill explicitly prunes low-probability forks and caps live branches,
and its trace format is being matched against a prose pool. All true — and none of it
licenses a claim that the skill helps. **On the only quantitative instrument available it
costs more and covers less.** To claim otherwise requires building an instrument that
scores what it optimises for: whether the bottom line is derived rather than asserted,
whether probabilities are calibrated, whether branches were walked to a horizon. That
instrument does not exist yet.

Until it does, mental-simulation should be described as untested rather than as
effective.
