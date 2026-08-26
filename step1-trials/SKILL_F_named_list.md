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

**1. Cut along real seams, and cover everything.** Every part belongs to exactly one
region. Cross-cutting concerns — what grows over time, what is observable, what survives a
restart — fall between regions, so assign each explicitly to one owner instead of leaving
it to whoever notices.

*No obvious seams?* Cut on one of: the artifact versus the people and time around it; what
is stored versus what moves; the thing itself versus its operation over its life. Any
honest cut works. An unassigned middle does not.

**2. Two regions, usually.** Count the material's separable subsystems, never your budget.
A region must be big enough to hold whole consequences.

**3. Expand each region into a named list before working it.** A region named "storage"
or "the delivery side" is two words, and a pass against two words ends when the topic
*feels* covered. Write the region out as its contents instead — every named thing inside
it:

> Region B — delivery and use: the tap and the 25 mm main; the eight 16 mm laterals and
> their ball valves; the pressure-compensating drippers; the battery timer valve; the
> available head and pressure; and how the gardeners actually operate it day to day.

Six to ten named items. Fewer than six means the region is still a theme, not a list.

**4. Work the list, one item at a time, and let the list end the pass.** For each item in
turn: what does it do, what does it do when it fails, and what follows from that. Move on
only when that item is done.

> I own ONLY this region: `<the list>`. I will be EXHAUSTIVE within it and IGNORE
> everything else — `<the others>` are covered separately. I will not spend a line on them.
> I will go deeper here than I normally would, and I will not end this pass until every
> item on my list has been worked through.

Both halves are load-bearing. "Ignore the rest, go deeper" stops the pass from becoming a
balanced overview of the whole. **"Not until every item is worked through" is what stops
it ending early** — which is the more common failure, and the one that feels like
finishing rather than like quitting. Keep the passes separate in the output; never end one
with a summary of the whole.

**5. Cross-region work last** — interactions between regions, contradictions between them,
the conclusion. Nothing that owns a single region can see these.

**6. Union, then dedupe. Never vote.** Majority rule deletes the finding that only one pass
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
