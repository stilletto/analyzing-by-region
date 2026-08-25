---
name: analyzing-by-region
description: Use before analysing anything whose parts interact and which is too big to cover well in one sweep — code or a subsystem, a plan or migration, a design, a control system or robot behaviour, game rules or an economy, a protocol, a data pipeline, a contract, someone else's system. Triggers: being asked what happens when this runs, whether it will work, how it fails, what could go wrong, what players or users will actually do, or for a review or audit; a problem that splits into cases; noticing a first pass came out as a shallow balanced overview, or that you are summarising breadth-first instead of going deep anywhere. Also whenever several agents are about to be pointed at one question, when deciding how many to spawn, or when tempted to give them roles or personas.
---

# Analyzing by Region

## Overview

**Cut the material into regions, then cover each region in its own exhaustive pass.
Do the passes yourself first — spawn agents only to buy the last few points.**

The win comes from the partition instruction, not from the fan-out. Covering the whole
thing in one balanced sweep is what loses; owning one region at a time and being
exhaustive in it is what wins, and a single agent can do that in successive passes.

Measured across four open-ended analysis tasks — code, a prose plan, a physical design —
against verified reference sets, coverage of what a fan-out of many agents found between
them (`skill-writer/evals/results/`):

| variant | code | plan | physical | mean |
|---|---|---|---|---|
| one agent, one balanced sweep | 0.51 | 0.35 | 0.52 | **0.46** |
| **one agent, region-by-region passes** | 0.67 | 0.68 | 0.73 | **0.69** |
| two agents, one region each | 0.87 | 0.62 | 0.85 | **0.78** |
| two agents, different perspectives | — | — | — | 0.55 |
| four agents, no seeding | — | — | — | 0.63 |

Domains measured so far: code, a prose plan, a physical design. The description above is deliberately wider than that — it says where to *try* this; the table says where it is *proven*. Treat anything outside those three as untested.

**The instruction is most of the win, and it is nearly free**: +0.23 coverage for +15%
tokens, and it is the best coverage-per-token on every task measured.

**It removes variance, not just raises the mean.** Bare agents ranged 0.35–0.52; the same
agent given the instruction ranged 0.67–0.73. The floor moves much further than the
ceiling — what the skill really buys is that the bad case stops being bad.

## When NOT to use

- **Independent tasks** — separate bugs, separate files, separate subsystems with nothing
  between them. That is superpowers:dispatching-parallel-agents, and it already works.
- **Material one agent can read exhaustively.** On a single file everyone finds nearly
  everything and there is nothing left to decorrelate. Fan-out pays only where attention
  must be allocated because it cannot cover everything.

## The recipe

**0. Decide whether to spawn at all.** Doing the passes yourself captures most of the
benefit for a fraction of the cost. Everything below applies either way — a "region" is a
pass when you do it yourself and an agent when you delegate it.

**Fan out only when the seams are REAL — read off the material, not invented by you.**
Measured: two agents beat self-partitioning on code (0.87 vs 0.67) and on a physical
design (0.85 vs 0.73), and LOST on a prose plan (0.62 vs 0.68) — the one task whose split
had to be invented. The agents separated perfectly there (overlap 0.02); the problem is
that in a plan most consequences ARE cross-region — data problems cause schedule problems
cause staffing problems — and two separate contexts leave nobody able to join the ends.
One agent taking both regions in succession still holds both in one head.

So: obvious seams (modules, subsystems, physically distinct components) → fan out is
worth it. Seams you had to invent → take the passes yourself.

**1. Cut the material into regions along its real seams**, and cover it completely —
every part of the system belongs to exactly one agent. Cross-cutting concerns (what grows
over time, what is observable, what survives a restart) are the ones that fall between
regions, so assign each of them explicitly to one owner rather than leaving them to
whoever notices.

**2. Give each region this shape of instruction, verbatim in spirit:**

> You own ONLY this region: `<region>`. Be EXHAUSTIVE within it and IGNORE everything
> else — `<the other regions>` are covered separately. Do not spend a single line on
> them. Go deeper on this one than you normally would: the job of this pass is coverage
> of this region, not a balanced overview.

Doing it yourself, that is the framing for each pass in turn, and the passes stay
separate in the output — do not merge them into an overview at the end.

The "ignore the rest, go deeper than usual" half is load-bearing. Without it an agent
given a topic still writes a balanced overview of the whole system, which is what the
free agents already do.

**3. Combine by UNION**, then dedupe. Do not vote. In a search, majority rule deletes the
one real finding that only one agent saw — and in the measured runs ~70% of everything a
partitioned pair found came from exactly one of its two agents.

**4. Do the cross-region work last**, after all passes are in: interactions between
regions, contradictions between them, and the overall conclusion. Nothing that owns a
single region can see those — which is exactly why the passes must not each end in a
summary of the whole.

## How many regions

**Two, usually.** Splitting further bought +0.01 while doubling the cost, because
partitioning front-loads its entire gain into the first cut.

Pick the count from **how many genuinely separable subsystems the material has**, never
from the agent budget. A region has to be big enough to contain whole consequences; if
the phenomena you care about straddle two of your regions, the regions are wrong.

**Over-splitting has a signature: individual coverage collapses while the union stands
still.** In the measured 4-way split, mean single-agent coverage fell 0.45 → 0.29 and the
union moved +0.01. The quarter that owned only stock and reservations returned 14 claims
out of 110 — a region too small to hold consequences produces a report about details
instead of about what happens.

## What backfires

**Roles and perspectives.** "You are a security engineer" / "you are an SRE", or "walk
forward from the entry point" / "work backward from the failure" — these change
vocabulary and framing, not search order. Measured, the reframed pair was **more alike
than the uninstructed pair** (overlap rose from 0.61 to 0.66) and covered less than free
agents did. The instruction funnels every agent into the same central narrative of the
system, where uninstructed agents would each have wandered somewhere different.

If you want two agents to differ, change **what they are looking at**, not **how they are
looking at it**.

## Cost, and where it does not apply

Writing out every region exhaustively is verbose. In one measured run the instruction
pushed a batch of five small puzzles past a 64,000 output-token ceiling and the run died
with nothing returned. On batched work, give each item its own pass rather than asking for
all of them in one answer.

**It does nothing when the material is small enough to see all at once.** Measured on
ARC-AGI-1 grid puzzles: bare 40/40, with the instruction 40/40, not one task changed
either way. That run was at ceiling so it proves little, but the reasoning holds — a grid
you can take in at a glance has no coverage problem to solve, and the skill's whole
mechanism is about allocating attention across material you cannot hold at once. Reach for
it when the material is bigger than one careful look, not when it is smaller.

## Common mistakes

| Mistake | What it looks like | Fix |
|---|---|---|
| Persona seeding | "act as a security expert" | Give a region, not a role |
| Reframing seeding | "forward pass" vs "backward pass" on the whole | Give a region, not a viewpoint |
| Topics without exclusivity | "focus on X" with no "ignore the rest" | Say who owns the other regions and forbid touching them |
| Splitting to fill a budget | 8 agents because 8 were affordable | Count the seams, not the wallet |
| Gaps between regions | cross-cutting concerns owned by nobody | Assign each explicitly to one owner |
| Voting on findings | keep what the majority reported | Union and dedupe; the rare find is the point |
| Expecting balanced reports | each agent still summarises everything | "Go deeper on yours than you normally would" |
| Orchestrator does no work | splice and stop | Interactions and the conclusion are yours |
| Spawning by reflex | agents dispatched before trying the passes yourself | Self-partition first; fan out only for real seams |
| Fanning out on invented seams | prose or a plan cut into halves you made up | Do those passes yourself — measured to lose |
