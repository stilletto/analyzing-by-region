# T1, six conditions, one 112-claim pool rebuilt from all twelve reports

    condition              effort   cov   tokens  cov/100k   reps
    bare                   xhigh   0.41   53,149     0.77    0.43 0.39
    self-partition         xhigh   0.58   57,739     1.00    0.54 0.61
    partitioned pair       xhigh   0.72  123,002     0.59    0.72
    bare                   max*    0.40   59,252     0.67    0.41 0.38
    free skill choice      max*    0.38   64,260     0.59    0.35 0.41
    self-partition         max*    0.58   65,708     0.89    0.60 0.57

## 1. The effort step bought nothing: -0.01

Bare at xhigh 0.41, bare with effortLevel=max 0.40. If the setting applied, max is worth
nothing here. *Caveat: `effortLevel` is a global setting, not a per-call parameter; whether
a running session picks up a mid-session change could not be verified, and token spend
does not separate the conditions (bare runs ranged 50.7k-67.8k regardless of setting).*

## 2. The skill replicated to two decimal places: +0.18

Self-partitioning scored **0.58 and 0.58** across two independent pairs of runs at two
different effort settings, against bare at 0.41 / 0.40. Fourth task, fourth confirmation.
It is also the best cost-efficiency of any condition (1.00 coverage per 100k).

The head-to-head the run was built for: **the instruction is +0.18, the effort step is
-0.01.** They cost about the same in tokens.

## 3. mental-simulation: third consecutive negative, this time self-selected

Both free-choice agents invoked `superpowers:using-superpowers` and then reached past the
whole superpowers collection for `mental-simulation`. Result 0.38 against bare 0.40, and
-0.04 after leave-one-out (dropping the 4 claims only those runs contributed to the pool).

This removes the strongest objection to the earlier D2 result — that the skill had been
pointed at a task it was not for. Given a free choice on a task its own description
matches, an agent selected it, and it cost 25% more tokens for slightly less coverage.

Two readings remain open, and this run does not separate them: either the skill trades
breadth for something this instrument cannot see (its pre-registered defence, section
10e.1), or it does not work. That is now three negatives and no positive on any
instrument that exists.

## 4. The superpowers collection has nothing for this task

Given the full set and an explicit instruction to find what applies, both agents used only
`using-superpowers` (the meta-skill) and then went outside the collection. brainstorming,
systematic-debugging, TDD, writing-plans, dispatching-parallel-agents — none fit
open-ended consequence analysis. That is a gap in the collection, not a failure of the
agents.

## Method notes

- Pool rebuilt from all twelve reports so no arm is scored against a key it did not help
  write; leave-one-out applied to the one arm where it mattered.
- Answer keys, prior reports and prior verdict files were moved out of the task directory
  before this run, but six agents started ~1 minute before that cleanup. They were told to
  read three named files and did not list the directory; leakage is unlikely but not
  provable.
- A pool file was read while its agent was still writing it, so three judges scored 62 of
  the eventual 112 claims. Salvaged because verdicts key on claim id, not position; the
  remaining 50 were judged separately.
