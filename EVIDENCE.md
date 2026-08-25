# Measured effect, and the limits of the evidence

Kept out of SKILL.md so the skill itself carries only what is needed to execute it.

## Two numbers, and the difference between them matters

Everything is scored the same way: an open question — *what actually happens when this
runs?* — over material with many interacting parts, answered against a reference set of
verified claims about that system. The score is how much of what is true the answer
actually stated.

**With the regions supplied by a person who had read the material:**

| | code | prose plan | physical design | mean |
|---|---|---|---|---|
| one sweep, no method | 0.51 | 0.35 | 0.52 | **0.46** |
| regions supplied | 0.67 | 0.68 | 0.73 | **0.69** |

**With this skill file used as-is, the agent choosing its own regions:**

| | code | prose plan | physical design | mean |
|---|---|---|---|---|
| one sweep, no method | 0.51 | 0.35 | 0.52 | **0.46** |
| skill file, as-is | 0.56 | 0.47 | 0.59 | **0.54** |

So the method is worth +0.23 when someone who understands the material draws the regions,
and +0.08 when the agent draws them itself. **Two thirds of the effect lives in the
partition, not in the passes.** Any claim of "+0.23" that does not say who chose the
regions is overstating what the file alone does.

## Closing that gap was attempted and failed

Five different step-1 rewrites were built and measured against the file's own baseline —
inventory-and-deal; cut where couplings are thinnest; read fully first then verify the cut
against three concrete failures; make two different cuts and run both; derive regions from
kinds of bad outcome rather than from parts. On six repetitions per condition:

    baseline (this file)         0.60   sd 0.047
    cut by couplings             0.62   sd 0.046      +0.02, threshold 0.054 — not distinguishable
    two different cuts           0.59   sd 0.056      -0.01 — not distinguishable
    regions from outcomes        0.56   sd 0.035      -0.04 — not distinguishable
    inventory and deal           worse on the prose task by 0.08

The reports were read afterwards to confirm the instructions had actually been followed;
they had. The ideas failed on their merits, not through being ignored. Variants are kept
in `step1-trials/` so they are not retried.

## Length is a bigger lever than the cut, and this is not yet exploited

Across 18 runs of the same task, report length varied 2.8x (3,628 to 10,158 words) and
correlated with coverage at r = 0.54. The short half averaged 0.57, the long half 0.63 —
a larger difference than any of the five partitioning rewrites produced. Correlation is
not causation here: the agent that understood more may simply have written more. Untested.

## Trimming this file: half the size, not free

The file was cut from 1,578 words to 732 by moving the evidence out. Measured both ways,
agent choosing its own regions:

    code             fat 0.56   lean 0.56   —   equal
    physical design  fat 0.78   lean 0.59   —   fat higher by 0.19, at 2.3x the tokens

Not equivalent. The fat version wins on one of two tasks and costs 125k tokens against
54k; per token the lean version is nearly twice as efficient (1.09 vs 0.62 coverage per
100k). The fat version's advantage is plausibly the length effect above rather than
anything in its extra text — it made the agent work longer, not better. `SKILL.md.fat` is
kept for that reason.

## Limits

- Claude Opus 5 only. Domains: code, prose planning, physical design. Mathematics untested.
- Reference sets are pooled from many independent answers and adversarially verified
  (16–23% of candidate claims are discarded). Anything no answer ever produced is invisible
  to the metric, so these are coverage-of-what-was-found, not coverage of truth.
- Absolute numbers depend on how a reference set was built and must not be compared across
  tasks. Differences between conditions on the same task are the usable quantity.
- Run-to-run spread within one condition reaches 0.15. Anything below about 0.05 on two
  repetitions is noise; six repetitions were needed to settle the step-1 question.

Full record: https://github.com/stilletto/analyzing-by-region
