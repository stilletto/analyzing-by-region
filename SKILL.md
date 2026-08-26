---
name: analyzing-by-region
description: Use before analysing anything whose parts interact and is too big to cover in one sweep — code or a subsystem, a plan or migration, a design, a control system, game rules or an economy, a protocol, a pipeline, a contract, someone else's system. Triggers: what happens when this runs, will it work, how does it fail, what could go wrong, what will users actually do, a review or an audit, a problem that splits into cases, wanting the most complete account a budget allows, or a first pass that came out as a shallow balanced overview. Also whenever several agents are about to be pointed at one question, or when tempted to give them roles.
---

# Analyzing by Region

**Cut the material into regions, then cover each in its own exhaustive pass.**
One sweep gives a shallow overview of everything and a real account of nothing.

## Skip it when

- the material fits in one glance
- the question has one correct answer — this raises coverage, not accuracy
- the tasks are independent — that is superpowers:dispatching-parallel-agents

## Method

**1. Cut along real seams; cover everything.** Every part belongs to exactly one region.
Cross-cutting concerns — what grows over time, what is observable, what survives a restart
— fall between regions, so assign each to one owner rather than to whoever notices.
*No obvious seams?* Cut the artifact from the people and time around it; what is stored
from what moves; the thing from its operation over its life. Any honest cut works; an
unassigned middle does not.

**2. Two regions, usually.** Count separable subsystems, never your budget. A region must
be big enough to hold whole consequences.

**3. One region at a time, with this framing:**

> I own ONLY this region: `<region>`. I will be EXHAUSTIVE within it and IGNORE everything
> else — `<the others>` are covered separately. I will go deeper here than I normally
> would: this pass is coverage of this region, not a balanced overview.

"Ignore the rest, go deeper" is load-bearing — without it a pass given a topic still writes
a balanced overview of the whole. Keep the passes separate; never end one with a summary of
the whole.

**4. Cross-region work last** — interactions, contradictions, the conclusion. Nothing that
owns a single region can see these.

**5. Union, then dedupe. Never vote.** Majority rule deletes the finding only one pass
reached, and that finding is the point.

## For more coverage: run it all again and merge

Polishing one run has a low ceiling. Running the **entire** analysis again in a clean
context, letting it choose its own regions, then merging, gains more than any refinement
of a single run. Give a fresh agent both reports and this instruction:

> Nothing is lost: every distinct finding in either report must appear, mechanism and
> consequence intact. Same point in both — state it once. Disagreement — keep both readings
> and say they disagree. Do not summarise, do not compress, do not drop a finding for
> seeming minor. Length is not a concern, loss is.

Drop that last clause and the merge compresses, which is loss. The merged report should
come out **longer than both inputs together**; shorter means it summarised. Costs about
3.5x one run; a third run keeps adding, with diminishing returns.

**Do not pay an agent to choose the regions for another agent** — measured, it costs
exactly what it gains. Spend those tokens on another full run.

## One agent per region

Only when the material will not fit one context, or wall-clock beats tokens — and only on
**real** seams read off the material. On invented seams this loses to one context doing
both passes: consequences run across the regions and separate contexts cannot join the
ends. Do steps 4 and 5 yourself.

## Mistakes

| Mistake | Fix |
|---|---|
| Roles or perspectives — "as a security engineer", forward vs backward | Change what a pass looks AT, not how. Personas make passes MORE alike |
| A topic with no exclusivity — "focus on X" | Name who covers the rest and forbid touching it |
| Splitting to fill a budget; each pass then returns less and the total stands still | Count seams. Four regions instead of two bought almost nothing at double the cost |
| Spending extra budget on a better cut | Spend it on another full run and a merge |
| A merge shorter than its inputs | It compressed. Re-merge with "length is not a concern, loss is" |
| One batched answer for many items — blows output limits | Give each item its own pass |

Measured effect and limits: `EVIDENCE.md`.
