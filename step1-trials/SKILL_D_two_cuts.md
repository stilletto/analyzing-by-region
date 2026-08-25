---
name: analyzing-by-region
description: Use before analysing anything whose parts interact and which is too big to cover well in one sweep — code or a subsystem, a plan or migration, a design, a control system or robot behaviour, game rules or an economy, a protocol, a data pipeline, a contract, someone else's system. Triggers: being asked what happens when this runs, whether it will work, how it fails, what could go wrong, what players or users will actually do, or for a review or audit; a problem that splits into cases; noticing a first pass came out as a shallow balanced overview, or that you are summarising breadth-first instead of going deep anywhere. Also whenever several agents are about to be pointed at one question, when deciding how many to spawn, or when tempted to give them roles or personas.
---

# Analyzing by Region

**Cut the material into regions, then cover each region in its own exhaustive pass.**
One sweep gives a shallow overview of everything and a real account of nothing.

## Skip it when

- the material fits in one glance — nothing to allocate attention across
- the question has one correct answer — this raises coverage, not accuracy
- the tasks are independent — that is superpowers:dispatching-parallel-agents

## Method

**1. Do not look for the right cut. Cut twice, differently.** Choosing one good
partition is hard and getting it wrong is unrecoverable, so sidestep it: run two passes
over one partition, then two more over a DIFFERENT partition of the same material.

*First partition — by PARTS.* The components, functions, actors, artifacts, dealt into two
piles with nothing left over.

*Second partition — by STAGE.* The material's life over time: getting set up and starting;
normal running; failure and recovery; and the long run — wear, growth, the end of its
useful life. Deal these into two piles too.

Run all four passes. What the first partition's boundary hid will sit inside a region of
the second. Do not skip the second partition because the first "already covered it" —
that judgement is exactly the one that cannot be trusted.

**2. Two regions, usually.** Count the material's separable subsystems, never your budget.
A region must be big enough to hold whole consequences.

**3. One region at a time, with this framing:**

> I own ONLY this region: `<region>`. I will be EXHAUSTIVE within it and IGNORE everything
> else — `<the others>` are covered separately. I will not spend a line on them. I will go
> deeper here than I normally would: this pass is coverage of this region, not a balanced
> overview.

The "ignore the rest, go deeper" half is load-bearing. Without it, a pass given a topic
still writes a balanced overview of the whole — the exact failure being avoided. Keep the
passes separate in the output; never end one with a summary of the whole.

**4. Cross-region work last** — interactions between regions, contradictions between them,
the conclusion. Nothing that owns a single region can see these.

**5. Union, then dedupe. Never vote.** Majority rule deletes the finding that only one pass
reached, and that finding is the point.

## Spawning agents instead

Doing the passes yourself captures most of the benefit far more cheaply. Spawn one agent
per region only when the material will not fit one context, or wall-clock beats tokens —
and only when the seams are **real**, read off the material rather than invented. On
invented seams a fan-out loses to one agent doing both passes: the consequences run across
the regions, and separate contexts cannot join the ends. Give each agent the framing above;
do steps 4 and 5 yourself.

## Mistakes

| Mistake | Fix |
|---|---|
| Roles or perspectives — "as a security engineer", "forward pass" vs "backward pass" | Change what a pass looks AT, not how it looks. Personas make passes MORE alike |
| A topic with no exclusivity — "focus on X" | Name who covers the rest and forbid touching it |
| Splitting to fill a budget | Count seams. Four regions instead of two bought almost nothing at double the cost |
| Over-splitting — each pass returns much less, the combined result stands still | Regions are smaller than the phenomena in them. Merge |
| A gap between regions | Assign every cross-cutting concern to one owner |
| Voting on findings | Union and dedupe |
| Passes that still summarise everything | "Go deeper on yours than you normally would" |
| One batched answer for many items — blows output limits | Give each item its own pass |

Measured effect and limits: `EVIDENCE.md`.
