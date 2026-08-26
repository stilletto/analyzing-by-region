# Running the whole analysis twice and merging

The largest lever found, and found only after six attempts to improve the partition had
all failed. Each run reads the material fresh, chooses its own regions and does its own
passes. A separate agent then merges the two reports.

## Result

                              physical design      prose plan
    one run                   0.598  (6 runs)      0.457  (6 runs)
    two runs merged           0.702  (3 pairs)     0.619  (3 pairs)
    gain                      +0.104               +0.162
    regions supplied by hand  0.680  (1 run)       0.680  (1 run)

Two merged runs beat a human-drawn partition on the physical design and nearly reach it on
the prose plan. Cost is about 3.5x one run when orchestrated by hand.

Note this is **replication**, not one agent per region. Each run analyses the whole
subject. What is harvested is that two independent runs disagree about where to go deep.

## The merge is nearly lossless, if told that loss is the only thing that matters

Against a perfect union computed from the judges' own per-claim verdicts:

    physical design   real merge 0.702  vs perfect union 0.729   -0.027
    prose plan        real merge 0.619  vs perfect union 0.626   -0.007

The instruction used, verbatim:

> Nothing is lost: every distinct finding in either report must appear, mechanism and
> consequence intact. Same point in both — state it once. Disagreement — keep both readings
> and say they disagree. Do not summarise, do not compress, do not drop a finding for
> seeming minor. Length is not a concern, loss is.

Every merged report came out longer than its two inputs combined. A merge that comes out
shorter has compressed, and compression here is loss.

## Cost curve, physical design

    schema                                    agents   tokens   coverage
    one run                                      1        65k     0.598
    cutter agent -> one fresh worker             1+1     110k     0.667
    two runs merged                              2       215k     0.702
    three runs merged                            3       280k    ~0.76

## Paying an agent to draw the regions does not pay for itself

    who drew the regions        coverage   agents   tokens
    the working agent itself      0.598      1        65k
    a person                      0.680      1        68k
    a separate cutter agent       0.667      1+1     110k

At equal agent count an outside cut is worth +0.06 to +0.08 whoever draws it. The 29.5k the
cutter costs is the whole difference. Against the alternative use of those tokens it is
flat: a cutter plus two workers reached 0.787 for 192k; three plain runs reached 0.784 for
195k.

## The supplied-region ceiling was checked for leakage

The hand-drawn regions for the physical design named two things the brief never says —
"the available head and pressure" and "the water budget over a year". Those are not parts
of the design but the two calculations its viability turns on, and 20 of the 75 reference
claims sit in them. Re-run with every such word removed, four repetitions:

    agent chooses its own regions     0.60   sd 0.047   (6 runs)
    regions supplied, de-hinted       0.68   sd 0.061   (4 runs)
    regions supplied, as originally   0.73              (2 runs)

At most a third of the gap was phrasing. The de-hinted condition still covers the two
clusters it is no longer told about at 0.69 and 0.72, above its own average.

## What origin, not content, means

    regions supplied, de-hinted        8,969 words
    regions supplied, as originally    9,262 words
    agent chooses its own regions      6,046 words
    six different step-1 rewrites      6,000-6,200 words, every one

Two supplied partitions with different wording give the same length and the same coverage.
Six self-cut instructions as different as "cut where couplings are thinnest" and "derive
regions from kinds of bad outcome" give the same length as each other and as having no
step 1 at all.

## The rewritten skill, run as it will actually be used

Four runs, nothing said about budget. They diverged by themselves: one did a single pass,
two spawned a second run and merged, one spawned three.

    tokens   words    coverage    old file at the same cost
      65k     7,953     0.613     0.598  (one run)
      97k    23,222     0.787     ~0.65  (interpolated)
     130k    13,826     0.733     ~0.67  (interpolated)
     207k    23,601     0.840     0.702  (two runs merged, hand-orchestrated)

Every point sits above the old curve. The run that behaved like the old file scored 0.613,
inside the old distribution — no regression detected at equal cost, on one run, which is
not the same as proving there is none.

An agent orchestrating its own sub-runs is cheaper than hand-orchestration: 0.787 for 97k
against 0.702 for 215k, because the parent does not re-read the material for each run.

## Limits

Two tasks (physical design, prose plan). Three merge pairs each. Four runs of the rewritten
file on one task. Claude Opus 5 only. Run-to-run spread within a condition reaches 0.15,
so single runs are not informative on their own.

## Trimming the rewritten file: no loss

Cut from 984 words to 798 — three mistakes-table rows that restated steps 1, 3 and 5, the
trigger list, and prose throughout. Four runs each, budget unspecified:

    798 words              984 words
     66k    0.667           65k    0.613
     72k    0.667          130k    0.733
    143k    0.800           97k    0.787
    190k    0.853          207k    0.840
    mean 0.747 @ 118k      mean 0.743 @ 125k

At least as good at every cost point. The single-pass runs scored 0.667 twice against 0.613
for the longer file and 0.598 before the rewrite — but on two runs against one, with 0.054
sitting on the noise threshold, so "no loss" is established and "better" is not.
