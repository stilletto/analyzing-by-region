# Three objective benchmarks, all saturated. What that tells us.

The pool-based instruments in this repo need judges and hand-built reference sets. These
three need neither — the ground truth is mechanical. All three turned out to be unusable
for measuring this skill, and the reason is the same each time.

## 1. ARC-AGI-1 (grid puzzles) — 40/40 both conditions

Local copy, 419 tasks, exact grid match. Took 40, ran bare and region-instructed.
Both 40/40, not one task flipped. A 10-task fresh control with the answer key stored
outside the directory scored 9/10, so the ceiling is genuine and not leakage.

## 2. SWE-bench Lite, file localization — 4/4 bare

Real repos (requests, pytest, sphinx) checked out at each instance's base commit, agent
given the issue text and asked which file must change; ground truth is the file touched by
the gold patch. The bare agent got all four, in 3-4 tool calls and ~30k tokens each.
Stopped at the ceiling check — 4 agents, not 2M tokens.

## 3. Branch coverage of a 2360-line module — 98-99% all conditions

Agent writes a pytest suite for `ipaddress`; coverage.py scores it. Both conditions got
the same hint list; the only difference was flat list versus four regions with
be-exhaustive-within.

    bare      951/958 statements, 313/318 branches   99.1%
    bare      951/958              314/318           99.1%
    region    945/958              309/318           98.3%
    region    949/958              311/318           98.7%

The region condition wrote two to three times as many tests (189 and 267 against 102 and
73) and covered marginally *less*.

**This instrument was broken on the first attempt and the bug is worth recording.**
Measuring `ipaddress` directly reported 77% for everyone, with 238 of the 290 "uncovered"
lines being `def` and `class` signatures — statements that execute at import, which
coverage never saw because the module was already in `sys.modules` before tracing began.
The union of four independent suites was also exactly 77%, which is what exposed it. Fixed
by copying the module to a fresh name so it is first imported under tracing; a trivial
smoke test then scores 36.4% instead of 2.3%.

## The pattern, and why it is not just bad luck

All three are **bounded** tasks: a finite set of correct answers exists. One grid, one
file, one module's reachable lines. On bounded tasks this model already performs at or
near completion, so there is no headroom for any instruction to occupy.

The skill's measured effect lives entirely on **unbounded** tasks — "what actually happens
when this runs", where the set of true statements has no fixed size. There the bare agent
reaches 0.35-0.52 and the instruction adds +0.16 to +0.33.

That is a characterisation of the skill, not an excuse for the nulls:

> It does not make the model more accurate where the task has a bottom.
> It stops it stopping early where the task has none.

Which also predicts where it is worth paying for, and where it is not.
