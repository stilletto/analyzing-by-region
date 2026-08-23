# Final result: partition seeding, replicated and scaled

All groups: same task, same 110-claim verified pool, same judges, Opus 5.

    condition     n  mean single   UNION   jacc   rare   agents
    free          2         0.48    0.60   0.61    39%   P1+P2
    free          2         0.45    0.51   0.75    25%   P3+P4
    reframe       2         0.46    0.55   0.66    34%   F+B
    partition     2         0.45    0.69   0.30    70%   PA+PB
    partition     2         0.41    0.65   0.28    72%   PA2+PB2
    free          4         0.46    0.63   0.67    17%   P1+P2+P3+P4
    partition     4         0.29    0.68   0.22    53%   Q1+Q2+Q3+Q4

## 1. Partition beats free, and it replicates

n=2: partition 0.67 vs free 0.55 -> **+0.11**.

The means are not the strongest part. **Both partition runs (0.65, 0.69) exceed both free
runs (0.51, 0.60)** — the distributions do not overlap, on 2 reps each. And partition is
the more STABLE condition: rep spread 0.05 against free's 0.09. A better prompt would not
predict lower variance; decorrelation does, because partition removes the coin-flip of
which areas a free agent happens to wander into.

Every column carries the ensemble signature at once: partition has the weakest individual
agents and the highest union, jaccard drops by half, and ~70% of what a partitioned pair
finds comes from exactly one of its two agents.

## 2. Perspective reframing loses, again

reframe 0.55 sits between the two free runs and BELOW their better one, and it raised
jaccard to 0.66 — the instructed pair was more alike than the uninstructed pair. Telling
one agent "walk forward from the entry" and another "work back from the damage" funnels
both into the same central narrative. This was the pre-registered claim. It is refuted.

## 3. THE SCALING RESULT — splitting further buys nothing

    partition n=2 -> 0.67
    partition n=4 -> 0.68     (+0.01 for double the agents)

    free      n=2 -> 0.55
    free      n=4 -> 0.63     (+0.08 for double the agents)

Doubling a PARTITIONED fan-out is worthless; doubling a FREE fan-out is not. The curves
converge: partition front-loads the entire gain into the first split. At n=4 the
advantage has shrunk from +0.11 to +0.05.

The mechanism is visible in the per-agent column: mean single recall collapses 0.45 ->
0.29 when regions are quartered. Q1, which owned only stock and reservations, returned 14
of 110. A region too small to contain consequences produces a report about details
instead of about what happens.

**The headline, and the practically useful form of all of this:**

> A partitioned PAIR reached 0.67. A free fan-out needed FOUR agents to reach 0.63.
> Same coverage for half the agents — and splitting past the natural seams adds nothing.

## 4. Diagnostic for over-splitting

Over-splitting announces itself: individual recall falls while union stands still. If the
agents are each returning much less and the union is not moving, the regions are smaller
than the phenomena in them.

## 5. Limits

- One task, one system, one 2-way and one 4-way split. 2 reps at n=2, 1 rep at n=4.
- Opus 5 only; Haiku is out of band on this instrument.
- Free agents got no extra instruction while reframe and partition pairs did, so the
  strict like-for-like contrast is reframe vs partition; free is the no-intervention
  control.
- The partition was chosen by hand along obvious seams. How to partition material with no
  obvious seams is untested, and the n=4 result suggests the choice matters more than the
  count.
