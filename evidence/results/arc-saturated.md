# ARC-AGI-1: the instrument is saturated. No measurement possible.

Local benchmark found at `teacher-learning/Qwen2.5/eval/data/arc_agi_1.jsonl` — 419 tasks,
exact-grid-match scoring, no judges and no hand-built pool. Objectively the best instrument
in this repo, and it turned out to be unusable for this model.

    40 tasks, every ~10th from the file
    bare agent                40/40 = 1.00
    region instruction        40/40 = 1.00
    difference                +0.00, and not one task flipped either way

## It is a real ceiling, not leakage

`KEY.json` was left in the task directory during the main run — the same mistake made
earlier with a pool file. Both conditions scoring perfectly is exactly what contamination
looks like, so it had to be ruled out.

Control: 10 FRESH tasks with no overlap with the 40, key stored outside the directory,
bare condition only. **9/10 correct.** Opus 5 solves this set on its own. The ceiling is
genuine and the main run is not contaminated — but the main run also measures nothing,
because a test where both arms score 100% has no power.

## The pre-registered prediction was not tested

Before running, the prediction was recorded: the skill should give little or nothing on
ARC, because an ARC grid is small and fully visible, so coverage is not the bottleneck and
the skill's mechanism has nothing to work on. The observed difference is indeed zero — but
with both arms at ceiling the experiment could not have detected an effect if one existed.
The prediction survives untested. It is not evidence either way.

## The process failure, plainly

Section 10e of the design requires measuring the ceiling FIRST, with two agents, before
building anything else — a rule written after two earlier instruments saturated. It was
not applied here. Sixteen agents ran, then ten more for a re-run, and only then was the
ceiling checked. About 2M tokens to learn something two runs would have shown.

**Rule tightened: the two-agent ceiling check applies to borrowed benchmarks too, not just
to hand-built tasks.** A benchmark being externally famous says nothing about whether the
model under test still finds it hard.

## One finding that survives regardless

The region instruction pushed a five-puzzle batch past the 64,000 output-token ceiling and
the run died. Writing out size, colour, position and count for every example pair is
genuinely verbose. That is a real operational cost of this skill on batched work, and it
belongs in the skill.

## What a usable objective benchmark would need

Something this model does not saturate. ARC-AGI-1 is not it. Nothing else objective and
locally available was found — the machine has speech datasets and training logs, no
reasoning benchmarks beyond this one.
