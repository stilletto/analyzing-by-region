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

## The supplied regions were checked for leakage, and the gap survives it

The supplied regions for the physical design named two things the brief itself never says —
*"the available head and pressure"* and *"the water budget over a year"*. Those are not parts
of the design, they are the two calculations the design's viability turns on, and 20 of the
75 reference claims sit in them. The whole gap is worth about 10 claims, so the phrasing
could have been the entire effect.

It was re-run with every such word removed — regions listing only components the brief names,
on four repetitions:

    agent chooses its own regions     0.60   sd 0.047   (6 runs)
    regions supplied, de-hinted       0.68   sd 0.061   (4 runs)   +0.08, threshold 0.072
    regions supplied, as originally   0.73              (2 runs)

At most a third of the gap was phrasing, and that third is inside the noise of two runs
against four. The de-hinted condition also covers the two clusters it is no longer told
about at 0.69 and 0.72 — above its own average. The agent reaches head, pressure and the
water budget on its own; what it needed was not the hint.

## What supplied regions change is length, and nothing an instruction says does

    regions supplied, de-hinted        8,969 words
    regions supplied, as originally    9,262 words
    agent chooses its own regions      6,046 words
    six different step-1 rewrites      6,000-6,200 words, every one

Two supplied partitions with different wording produce the same length and the same coverage.
Six self-cut instructions as different from each other as "cut where couplings are thinnest"
and "derive regions from kinds of bad outcome" produce the same length as each other and as
having no step 1 at all. The content of the partition is not what does the work — its
**origin** is.

The likely mechanism: an agent that draws its own regions draws them at the granularity of
the effort it had already decided to spend, so the partition tells it nothing it did not
already know and cannot make it keep going. A partition that arrives from outside is a
contract it did not negotiate, and a pass against it cannot be ended on the feeling of having
covered the topic. Restating a self-authored partition does not substitute — that was tested
directly and failed (the named-list rewrite).

## Closing that gap was attempted and failed

Six different step-1 rewrites were built and measured against the file's own baseline —
inventory-and-deal; cut where couplings are thinnest; read fully first then verify the cut
against three concrete failures; make two different cuts and run both; derive regions from
kinds of bad outcome rather than from parts; expand each region into a named list of six to
ten items and refuse to end the pass until every item is worked through. On six repetitions
per condition:

    baseline (this file)         0.60   sd 0.047
    cut by couplings             0.62   sd 0.046      +0.02, threshold 0.054 — not distinguishable
    two different cuts           0.59   sd 0.056      -0.01 — not distinguishable
    named list per region        0.56   sd 0.047      -0.04 — not distinguishable
    regions from outcomes        0.56   sd 0.035      -0.04 — not distinguishable
    inventory and deal           worse on the prose task by 0.08

The reports were read afterwards to confirm the instructions had actually been followed;
they had. The ideas failed on their merits, not through being ignored. Variants are kept
in `step1-trials/` so they are not retried.

## Length is a bigger lever than the cut, and this is not yet exploited

Across 18 runs of the same task, report length varied 2.8x (3,628 to 10,158 words) and
correlated with coverage at r = 0.54. The short half averaged 0.57, the long half 0.63 —
a larger difference than any of the six partitioning rewrites produced. Correlation is
not causation here: the agent that understood more may simply have written more.

The named-list rewrite was a direct attempt to make length the cause. It did not move it:
six instructions as different as these all landed between 6,000 and 6,200 words, while the
condition with regions supplied from outside landed at 9,262. Within the named-list runs the
correlation held (r = 0.75, short half 0.53, long half 0.60), but no instruction changed
which half a run fell into. Length behaves as a symptom of how much the agent found, not as
a lever on it.

## Running the whole analysis twice and merging beats improving one run

This is the largest lever found, and it was found only after six attempts to improve the
partition had failed. Each run reads the material fresh, chooses its own regions and does
its own passes; a separate agent then merges the two reports.

                              physical design      prose plan
    one run                   0.598  (6 runs)      0.457  (6 runs)
    two runs merged           0.702  (3 pairs)     0.619  (3 pairs)
    gain                      +0.104               +0.162
    regions supplied by hand  0.680  (1 run)       0.680  (1 run)

On the physical design two merged runs beat a human-drawn partition; on the prose plan they
nearly reach it. Cost is about 3.5x one run.

**The merge is nearly lossless when told that loss is the only thing that matters.** Against
a perfect union computed from the judges' own verdicts:

    physical design   real merge 0.702  vs perfect union 0.729   -0.027
    prose plan        real merge 0.619  vs perfect union 0.626   -0.007

Every merged report came out longer than its two inputs combined. The instruction used is
in SKILL.md verbatim; the operative clause is "length is not a concern, loss is". A merge
that comes out shorter than its inputs has compressed, and compression here is loss.

## The rewritten file, run as it will actually be used

Four runs of the current SKILL.md on the physical design, with nothing said about budget.
They diverged by themselves: one did a single pass, two spawned a second run and merged,
one spawned three. That spread is the deployment reality, so each is placed against the
old file's curve at its own cost rather than averaged.

    tokens   words    coverage    old file at the same cost
      65k     7,953     0.613     0.598  (one run)
      97k    23,222     0.787     ~0.65  (interpolated)
     130k    13,826     0.733     ~0.67  (interpolated)
     207k    23,601     0.840     0.702  (two runs merged, hand-orchestrated)

Every point sits above the old curve. The run that behaved like the old file scored 0.613,
inside the old distribution — no regression detected at equal cost, on one run, which is
not the same as proving there is none.

An agent orchestrating its own sub-runs is cheaper than the hand-orchestrated version
measured above: 0.787 for 97k against 0.702 for 215k. The parent does not re-read the
material for each run.

## Paying an agent to draw the regions does not pay for itself

The obvious way to get an outside partition without spending a person's time is to have one
agent cut and a second, fresh agent work to that cut. It reproduces the supplied-region
condition almost exactly — and costs exactly what it gains.

    who drew the regions        coverage   agents   tokens
    the working agent itself      0.598      1        65k
    a person                      0.680      1        68k
    a separate cutter agent       0.667      1+1     110k

At equal agent count an outside cut is worth +0.06 to +0.08 whoever draws it; the 29.5k the
cutter costs is the whole difference. Against the alternative use of those tokens it is
flat: a cutter plus two workers reached 0.787 for 192k, three plain runs reached 0.784 for
195k. Region-drawing is not where extra budget belongs.

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
