# Skill evaluation harness — design

Written BEFORE any skill variant exists. Pre-registered on purpose: a metric invented
after seeing results gets fitted to whichever variant the author already likes.

First subject: **seeding parallel agents** (one question, N threads, seeded apart).
Second subject, same harness: **mental-simulation v1 vs v2** — currently justified by
argument, never measured.

---

## 1. The claim, stated so it can lose

> Fanning N agents at one question and seeding them apart recovers materially more of the
> true finding set than N identical agents, **and** more than one agent given N× the
> budget.

Sub-claim, the one I actually care about and the one most likely to be wrong:

> Seeding by **entry point and assumption** (forward / backward / outward; "assume it
> holds" vs "assume it broke") beats seeding by **role label** ("you are a security
> expert"), because a role changes vocabulary while an entry point changes search order.

**Pre-registered kill condition.** If entry-point seeding does not beat identical agents
by more than the measured noise floor (§8) on at least two of the three discovery tasks,
the skill does not get written. If it beats identical agents but not the compute-matched
single agent, it gets written as "spend the tokens on one deeper pass instead" — the
opposite skill.

---

## 2. Why the obvious eval is wrong

The tempting metric is "union of findings across N agents". It is broken three ways:

1. **Union rises with N mechanically.** Five agents beat one because they are five. Any
   arm with more agents wins without teaching us anything.
   → every arm is **cost-matched in total output tokens**, not in agent count.
2. **Union rewards speculation.** An agent that lists fifty maybes scores well. Coverage
   without precision is gameable.
   → nothing counts until it survives adversarial verification (§7), and precision is
   reported alongside coverage.
3. **It cannot separate "diversity helped" from "more compute helped".** This is the
   whole question, and the naive design cannot answer it.
   → the compute-matched single agent (A1) is the load-bearing control, not a formality.

---

## 3. Three modes, three metrics — they do not share one number

| Mode | Question | Primary metric | Secondary |
|---|---|---|---|
| **Discovery** | "what is here / what breaks" | coverage of reference set, cost-normalised | rare-find rate, pairwise Jaccard, precision |
| **Generation** | "produce X" | judged quality of the *best* output | quality of the median output; spread |
| **Verification** | "is this claim true" | precision + recall against a seeded key | agreement rate between verifiers |

Reporting one blended score across modes would hide the interesting result, which is that
the right combining rule differs per mode: union for discovery, pick-a-winner for
generation, vote for verification. An eval that averages them cannot see that.

---

## 4. Arms

All arms cost-matched on total output tokens (±15%). `k` = agents per arm, chosen per arm
so the budgets match.

Note on A2: `temperature` and `top_p` are removed on Opus 5, so identical agents
cannot be spread apart artificially — A2's diversity is whatever sampling
nondeterminism the model has left, and nothing more. That makes A2 an honest floor
rather than a tunable arm.

| id | arm | what it isolates |
|---|---|---|
| A0 | 1 agent, 1× budget | floor |
| A1 | **1 agent, N× budget**, no further instruction | does diversity beat simply thinking longer? |
| A1b | **1 agent, N× budget, told to make the diverse passes itself** — forward, then backward, then from the most loaded component, in one context | the real competitor. If A1b wins, the skill is "do the passes yourself", and fanning out is wasted money |
| A2 | N identical agents, union | does resampling alone (sampling noise) buy anything? |
| A3 | N agents, **role labels** only | the intuitive seeding — vocabulary diversity |
| A4 | N agents, **entry point + assumption** | search-order diversity — my actual claim |
| A5 | N agents, **input slice** | what `dispatching-parallel-agents` already does |
| A6 | A4 + A3 combined | do they compose or interfere? |

A1 must be implemented honestly: models do not spend a budget just because they are
allowed to, so A1 without further instruction tends to be a straw man — which is exactly
why A1b exists. **A1b is the arm most likely to beat A4, and it is the cheap outcome.**

Pilot runs A1b, A2, A4 only. A3/A5/A6 are added only if the pilot shows the harness
discriminates at all.

---

## 5. Tasks

Deliberately includes tasks where the claim should **fail**. An eval that can only produce
wins is a marketing instrument.

**Discovery — wide answer space (diversity should help):**
- `D1` Code review of a ~400-line service with **13 planted defects** across 6 classes
  (concurrency, resource lifetime, error classification, security, spec mismatch,
  performance-at-scale). Known answer key.
- `D2` "What happens when this runs" on a stateful system with no planted key —
  reference-pool ground truth (§6). This is the mental-simulation shape.
- `D3` Non-code: an ops runbook / migration plan with hidden coupling between steps.

**Narrow answer space (diversity should NOT help) — falsification task:**
- `N1` One specific bug, one root cause, findable by reading one file correctly.
  Expected result: A4 ≈ A2 ≈ A1. **If A4 wins here, the metric is measuring verbosity,
  not coverage, and the harness is broken.**

**Generation:**
- `G1` Design a schema + API for stated constraints, judged on pre-stated criteria.

**Verification:**
- `V1` 20 candidate findings, 10 real and 10 plausible-but-false, seeded by hand.
  Measures whether diverse skeptics separate them better than identical ones.

Tasks must not be recognisable public code — mutate names, structure and domain, or the
model recalls the answer instead of finding it.

---

## 6. Ground truth, and its ceiling

Two sources, used together because each covers the other's weakness:

**Planted key (D1, V1).** Exact, cheap to score, but unrepresentative: planted defects are
cleaner than real ones and cluster in classes the planter thought of.

**Reference pool (D2, D3).** Build once, expensively: ~20 agents across every seeding,
pool all findings, adversarially verify each (§7), keep what survives. Small configurations
are then scored against that pool.

**Leave-one-out pooling, mandatory.** The pool is built from all seedings including the
ones being scored, so an arm that contributed heavily to the pool would score high by
construction. When scoring arm X, rebuild the reference set **excluding every finding that
only arm X's runs produced**. Without this, A4 is graded against a key it wrote.

**The ceiling, stated up front:** the pool is built by the same model family, so anything
*every* seeding misses is invisible to this eval, and measured coverage is coverage-of-what-
we-can-see, never of truth. The planted key partially calibrates this — if planted defects
are recovered at roughly the rate pool items are, the pool is probably not missing whole
categories. If planted recovery is much lower, the pool is flattering itself and the
absolute numbers must not be quoted, only the arm-vs-arm differences.

---

## 7. Scoring pipeline

1. **Canonicalise.** A finding is `(location, mechanism)` — file+line / step+state for
   code, component+failure-mode for a mechanism. Never score on wording. Semantic dedup is
   where this harness is most likely to break, so it is a distinct, auditable step and not
   a side effect of the judge.
1b. **Normalise granularity.** One agent writes "no timeout"; another writes three
   findings — worker hangs, queue stalls, no alert. Score at the granularity of the
   *reference item*, splitting or merging the agent's text to match, and let the narrow
   judge (step 3) make that call rather than the aggregator. Granularity drift inflates
   whichever arm happens to write in smaller pieces.
2. **Verify.** Each distinct finding goes to 3 adversarial verifiers instructed to
   *refute*, defaulting to refuted when uncertain. Survives on ≥2 of 3. Unverified findings
   count toward precision loss, never toward coverage.
3. **Match.** A narrow judge answers one yes/no per pair: "is this the same defect as this
   reference item?" Narrow questions have checkable answers; "score this review" does not.
4. **Audit.** Read 10% of match decisions by hand, both directions. Report the audit
   disagreement rate next to every result. If it exceeds ~10%, the numbers are noise and
   are reported as such.

Metrics computed per arm per task:
- `coverage` = verified findings matched / reference set size
- `coverage_per_100k` = coverage ÷ output tokens — the headline for cost-matched arms
- `rare_rate` = share of the arm's findings that exactly one agent in the arm produced
  (the direct decorrelation measure; this is what a vote would have deleted)
- `jaccard_mean` = mean pairwise overlap between agents in the arm (lower = decorrelated)
- `precision` = verified / claimed

---

## 8. Controls — these come before any real run

- **Noise floor (mandatory first).** Run the *same* arm twice under two different labels.
  The difference between them is the floor. Any arm-vs-arm gap smaller than that floor is
  not a result. Nothing else in this document means anything until this number exists.
- **Positive control.** An arm whose agents are handed 4 of the 13 planted defects. It must
  score visibly higher, or the metric cannot detect improvement and the harness is dead.
- **Negative control.** `N1`, above — where the claim should fail.
- **Reps.** 5 per arm per task minimum; single samples lie. If the noise floor is wide,
  raise reps rather than reporting a narrow-margin win.

---

## 9. Procedure and budget

**Pilot gate.** `D1` + `N1`, arms A1/A2/A4, 3 reps, plus the noise floor and the positive
control. Roughly 45–60 agent runs. Proceed only if: the positive control separates, the
noise floor is smaller than the A2↔A4 gap, and audit disagreement is under 10%.

**Full run** (only past the gate): 6 tasks × 6 arms × 5 reps. Add arms one at a time,
cheapest question first.

Everything runs through one script so an arm is a config row, not a hand-written prompt —
otherwise prompt-craft drift between arms becomes the real independent variable.

---

## 10. How this eval could lie to me

| Failure | Symptom | Guard |
|---|---|---|
| Reference pool is self-flattering | planted recovery ≪ pool recovery | §6, quote only differences |
| Judge favours verbose findings | precision falls as coverage rises | precision reported always |
| Semantic dedup merges distinct defects | coverage plateaus early on every arm | §7.1 separate, 10% audit |
| Task leakage from public code | uniformly high coverage, low variance | mutate the source |
| Prompt-craft drift between arms | the arm I wrote last wins | arms are config rows |
| Cost matching drifts | A4 quietly spends 2× A2 | log tokens per arm, hard ±15% |
| Arm graded against a key it wrote | the pool-heavy arm wins everywhere | leave-one-out pooling, §6 |
| Granularity inflation | one arm reports in smaller pieces and "covers" more | §7.1b |
| A1 is a straw man | single-agent arm underspends its budget | A1b, instructed explicitly |
| **Reading an agent's output file before the agent finished** | a pool or result file that looks complete and is not; downstream work silently scores half the data | Wait on the COMPLETION NOTIFICATION, never on the file existing. A file appears with its first written byte. |
| Fitting the skill to the metric | later variants win only on this eval | kill condition fixed in §1, held-out task added at the end |

---

## 10b. Execution mode: Claude Code subagents, not the API (degradation, recorded)

The only API key available returns `This organization has been disabled`, and there is
no `ant` CLI profile, so `harness.py` cannot run. The pilot runs through Claude Code
subagents instead. What that costs:

| Design requirement | Under subagents |
|---|---|
| **Arms cost-matched on output tokens (±15%)** | **Lost.** No `effort` knob and no per-call token control. Cost can only be *measured* after the fact, from each agent's reported token usage, and coverage normalised by it. Arms are cost-*measured*, not cost-*controlled* — and cost matching was load-bearing for the A1b comparison. |
| Reproducible arm = config row | Partly kept: prompts are byte-identical across agents within an arm except the output path (a digit). |
| `effort` sweep (A1b at max vs others at high) | Lost. A1b can only be approximated by instruction, not by budget. |
| Isolation from the answer key | Kept, and tightened: the fixture is copied to a scratch directory with no key anywhere near it, and agents are told to read exactly one file and not search. Residual risk if an agent disobeys; spot-check the transcripts. |
| Judge as a narrow, cached call | Kept — one judge agent reads the reports and writes the verdict JSON. |

**Consequence for reading the results:** an A1b-vs-A4 comparison is not decidable in this
mode, because the whole point of A1b is spending the same money in one context. The
A2-vs-A2b noise floor, the A2pos positive control, and the A2-vs-A4 comparison at equal
agent count remain valid, because those arms have identical shape and differ only in
seeding. Report A1b, if run at all, as indicative only.

## 10c. D2 measurement scheme (open finding space) — supersedes section 6 for D2

Two planted-key instruments saturated at ~0.88 single-agent coverage (results/). The
instrument moved to the open-ended task, where saturation is impossible by construction:
the set of true statements about a running system is not a finite list.

**Ground truth = a verified reference pool, built ORTHOGONALLY.**

The obvious construction is fatal: if the pool is built by diverse seeding, then diverse
arms match it *by construction* and the eval measures its own annotation. So the pool is
built by a seeding no scored arm uses — **component slicing**: one agent per class or
cross-cutting concern (stock, locking, payment, webhook, database, sweep, lifecycle,
money, observability, growth), each told to be exhaustive inside its slice and ignore
everything else. Forward/backward/loaded (A4) and role labels (A3) are unrelated to that
partition.

This replaces leave-one-out pooling, which is no longer needed: no scored arm contributes
to the pool at all.

**Pipeline.** slice agents -> canonicalise and dedup into a numbered list -> 3 independent
verifiers instructed to REFUTE, item survives on >= 2 -> that is the reference set.
Verification is batched (each verifier judges the whole list) rather than 3 calls per
item, or the cost is unmanageable.

**Scoring.** Each arm's recall against the fixed pool. An arm's finding that is true but
absent from the pool is recorded as **pool escape** and reported, never scored — escape
rate is the running measure of pool incompleteness, and the honest replacement for
pretending the pool is complete.

**Mandatory pre-check, from the two failures.** Before any arm runs, measure single-agent
recall against the pool with 2 agents. **The instrument is only usable if that lands
between 0.4 and 0.6.** Above that the ceiling is reached by the first agent and every arm
ties; below it the task may be so hard that findings are noise. This check costs 2 agents
and would have saved 24 on the first gate.

## 10d. Model change mid-experiment — recorded

Arms run on **Claude Haiku 4.5**, 2 reps, to control cost at volume. Consequences that
must be stated wherever these results are quoted:

- **The pool and the 0.48 gate were produced by Opus 5 agents.** A weaker model scored
  against a stronger model's pool is not the same measurement. The gate is therefore
  RE-RUN on Haiku before any arm is dispatched, and the Haiku single-agent recall is the
  number that licenses (or refuses) the Haiku arms.
- **Thinking mode is not controllable through the subagent interface** — it accepts a
  model, not a thinking or effort setting. "No thinking" could only be enforced through
  the direct API path, which is blocked by the disabled key. Haiku runs at the harness
  default.
- **Judges stay on the stronger model.** Every number rests on the judges; their measured
  agreement (100% on the D1 overlap, 87-91% between refuters) was established there, and
  moving them would inject noise directly into each metric rather than into one arm.
- **Cross-model comparison is not licensed.** Nothing here compares Haiku arms against
  the Opus precheck. Arms are only ever compared with other arms run on the same model.

## 10e. The standard skill check — one agent, with and without

The default question about any skill is not which fan-out topology wins. It is simply:

> **does one agent do better WITH this skill than the same agent WITHOUT it, on one task?**

No fan-out, no partitioning, no extra reasoning budget. One agent, one task, same
instrument, same judges. Fan-out topology is a separate and much longer question and must
not be mixed into this one.

The D2 instrument makes this cheap, because the no-skill baseline is already paid for:
four free agents on the same task scored 0.47, 0.49, 0.43, 0.46 — **mean 0.46**. Any skill
aimed at this kind of task can be measured against that number for the price of two runs.

Report three columns every time: coverage, tokens spent, and coverage per 100k tokens. A
skill that buys +0.05 coverage for +80% tokens is a different proposition from one that
buys +0.05 for free, and the coverage column alone hides that.

### 10e.1 Pre-registered caveats for the mental-simulation measurement

Written BEFORE the verdicts came back, so it cannot be read as post-hoc excuse-making.

**The metric measures breadth; the skill deliberately trades breadth for depth.**
mental-simulation instructs the agent to prune low-probability forks and to carry at most
3-4 live branches. That is a coverage-REDUCING instruction by design: the skill optimises
for a derived, defensible bottom line, not for the longest list. A low recall score would
therefore mean "the skill does something this instrument does not measure", not "the
skill does not work".

**Format mismatch.** The pool was canonicalised from prose slice reports. Skill answers
arrive as traces with fork lines, probabilities and branch walks. The judge must match a
compressed trace line against a verbose pool claim; the instruction "layout is
irrelevant" reduces but does not remove that bias against the terser format.

**So the honest verdict has two parts**: the coverage number, plus a separate judgement
about what the number cannot see. If a skill scores at or slightly below baseline while
attaching derived probabilities and traced consequences to each finding, the conclusion is
that skills of that kind need a DIFFERENT instrument — one that scores calibration and
derivation rather than enumerative recall. Coverage-against-a-pool is the right instrument
for breadth skills, and the wrong one for judgement skills.

## 11. What gets built first

1. The harness script — tasks, arms, reps, token accounting, raw output capture.
2. `D1` with its 12 planted defects and `N1`, both mutated beyond recall.
3. Noise floor + positive control. **Report those two numbers before running anything else.**
4. Only then: the pilot, and only then any skill variant.

No skill variant is written until step 3 produces a usable noise floor. Writing the variant
first is how the metric ends up serving the variant.
