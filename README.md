# analyzing-by-region

A Claude Code skill, and the measurements behind it.

**Cut the material into regions, then cover each region in its own exhaustive pass.**
Not "review this system" — "you own only the locking and the two mutexes; be exhaustive
there and ignore everything else; go deeper than you normally would." Then the next region.

That instruction, given to one agent with no fan-out, raised coverage of what is true
about a system from **0.46 to 0.69** across code, a prose plan and a physical design.

---

## What was measured

Each task asks an open question — *what actually happens when this runs?* — over material
with many interacting parts. Answers are scored against a reference set of verified claims
about that system: how much of what is true did the answer actually state.

**Two numbers, and which one applies depends on who draws the regions.**

| | code | prose plan | physical design | mean |
|---|---|---|---|---|
| one sweep, no method | 0.51 | 0.35 | 0.52 | **0.46** |
| **skill used as-is**, agent picks its own regions | 0.56 | 0.47 | 0.59 | **0.54** |
| regions supplied by someone who read the material | 0.67 | 0.68 | 0.73 | **0.69** |

**+0.08 on its own; +0.23 when the regions are drawn by someone who understands the
material.** Two thirds of the effect lives in the partition, not in the passes. Earlier
versions of this README quoted only the 0.69 row, which overstated what the file does
unaided; that is corrected here.

Cost of the instruction: **+24% tokens** on average, and it is the best coverage-per-token
of every configuration tested.

### It removes variance more than it raises the mean

Bare agents scored 0.35–0.52 depending on which way they happened to come at the problem.
The same agent given regions scored 0.67–0.73. **The floor moves much further than the
ceiling** — what this buys is that the bad case stops being bad.

### Closing the partition gap was attempted, five ways, and failed

Inventory-and-deal; cut where couplings are thinnest; read fully first then verify the cut
against three concrete failures; make two different cuts and run both; derive regions from
kinds of bad outcome. At six repetitions per condition none moved the result beyond noise
(best was +0.02 against a 0.054 threshold). The reports were read afterwards to confirm
the instructions had been followed — they had. See `step1-trials/` and `EVIDENCE.md`.

### A bigger lever, not yet exploited

Across 18 runs of one task, report length varied 2.8x and correlated with coverage at
r = 0.54; the short half averaged 0.57, the long half 0.63. That is a larger difference
than any partitioning rewrite produced. Whether making an agent write longer *causes*
better coverage, or merely accompanies it, is untested.

## What does not work

**Roles and perspectives.** "You are a security engineer" / "you are an SRE", or "walk
forward from the entry point" / "work backward from the failure". Measured 0.55 against
0.55 for uninstructed agents — and overlap between the agents *rose* from 0.61 to 0.66.
The framing funnels every agent into the same central narrative of the system, where
uninstructed ones would each have wandered somewhere different. If you want two agents to
differ, change **what they look at**, not **how they look at it**.

**Fanning out across seams you invented.** Where the seams are real — modules, subsystems,
physically separate components — two agents beat one (0.87 and 0.85 against 0.67 and 0.73).
Where the split had to be made up, as in a prose plan, the pair *lost* to a single agent
doing both passes (0.62 against 0.68). They separated perfectly (overlap 0.02) — but in a
plan most consequences run *across* the halves, and two separate contexts leave nobody able
to join the ends.

---

## When it does nothing

**On any task with a bottom.** Three objective benchmarks were tried and all three
saturated: ARC-AGI grid puzzles 40/40 in both conditions; SWE-bench file localization 4/4
for a bare agent in three tool calls; branch coverage of a 2360-line module 98-99%
everywhere, with the region condition writing two to three times more tests for marginally
*less* coverage.

They share a property: a finite set of correct answers exists. This model already performs
near completion on those, so no instruction has room to add anything. The measured gain
lives entirely on unbounded questions — *what actually happens when this runs* — where the
set of true statements has no fixed size, a bare pass reaches 0.35–0.52, and stopping early
is the actual failure mode.

> It does not make the model more accurate where the task has a bottom.
> It stops it stopping early where the task has none.

**When the material fits in one glance.** On ARC-AGI grid puzzles: 40/40 both with and
without, not one task changed either way. A grid you can take in at a glance has no
coverage problem to solve, and this skill's entire mechanism is about allocating attention
across material you cannot hold at once. (That run was at ceiling, so it proves little —
but the reasoning stands.)

**It is verbose.** In one run the instruction pushed a batch of five small items past a
64,000 output-token limit and the run died with nothing returned. On batched work, give
each item its own pass.

---

## Install

**Claude Code, Codex, or any runtime with a skills directory** — symlink it into place:

```bash
git clone <this repo> ~/src/analyzing-by-region
ln -s ~/src/analyzing-by-region ~/.claude/skills/analyzing-by-region
```

Claude Code reads `~/.claude/skills/`, Codex reads `~/.codex/skills/`, and several
runtimes also honour `~/.agents/skills/`. Symlinking the same directory into each keeps one
copy to edit.

**ChatGPT and anything else without a skills directory** — there is nothing to install;
paste [`for-chatgpt.md`](for-chatgpt.md) into Custom Instructions, a Project's
instructions, or a Custom GPT.

---

## Limits of the evidence

- Five measurements across four tasks, plus one saturated benchmark. Two repetitions per
  condition on the single-agent arms, one on the fan-out arm.
- Claude Opus 5 only.
- Domains: code, prose planning, physical design. Mathematics is **untested** — nothing
  here says anything about it.
- Reference sets are built by pooling many independent answers and then adversarially
  verifying each claim (16–23% get thrown out). Anything no answer ever produced is
  invisible to the metric, so these are coverage-of-what-was-found, not coverage of truth.
- Absolute numbers depend on how a reference set was built and should not be compared
  across tasks. Differences between conditions on the same task are the usable quantity.

`evidence/METHOD.md` documents the harness, including the ways it can lie and the mistakes
that were made building it. `evidence/results/` has the raw numbers, `evidence/tasks/` the
task materials and their verified reference sets.
