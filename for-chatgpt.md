# Paste-ready version (ChatGPT, or any assistant without a skills directory)

ChatGPT has no skills directory, so this cannot be installed — it has to be pasted.
Put the block below into **Settings → Personalization → Custom Instructions**, into a
**Project's instructions**, or into a **Custom GPT's** instructions. Trim it if space is
tight; the four numbered steps and the two prohibitions are what carry the measured effect.

---

When you are asked to analyse something whose parts interact and which is too big to cover
well in one sweep — a codebase or subsystem, a plan, a migration, a design, a control
system, game rules, a protocol, a contract, someone else's system — do not answer in one
balanced pass. A single sweep produces a shallow overview of everything and a real account
of nothing. Instead:

1. **Cut the material into 2 regions** along its real seams. Cover it completely: every
   part belongs to exactly one region. Cross-cutting concerns — what grows over time, what
   is observable, what survives a restart — fall between regions, so assign each of them
   explicitly to one region rather than leaving them to whichever pass notices.

2. **Take one region at a time.** For each, work as if that region is all that exists:
   *"I own only this region. I will be exhaustive within it and ignore everything else —
   the other regions are covered separately. I will go deeper here than I normally would;
   the job of this pass is coverage of this region, not a balanced overview."*
   Keep the passes visibly separate in your answer. Do not merge them into a summary.

3. **Do the cross-region work last**, once all passes are done: interactions between
   regions, contradictions between them, and the overall conclusion. Nothing that owns a
   single region can see those — which is exactly why no pass may end in a summary of the
   whole.

4. **Combine by union, not by vote.** Keep everything each pass found. In a search,
   majority rule deletes the one real finding that only one pass reached.

Two things not to do, both measured to backfire:

- **Do not use roles or perspectives to vary the passes** — "as a security engineer", "as
  an SRE", "forward from the entry point", "backward from the failure". These change
  vocabulary, not search order, and they funnel every pass into the same central narrative.
  If you want passes to differ, change *what they look at*, not *how they look at it*.

- **Do not split into more than 2 or 3 regions.** Going from two regions to four bought
  +0.01 coverage for double the cost. Count the material's real seams, not your budget.
  Over-splitting announces itself: each pass returns much less while the combined result
  stands still — the regions have become smaller than the phenomena inside them.

Skip all of this when the material fits in one glance, or when the question has a single
correct answer. It buys nothing there and costs about a quarter more output.

---

**Where the numbers come from.** Measured across code, a prose plan and a physical design,
scored on how much of what is verifiably true about each system the answer actually stated:
one sweep 0.46, region by region 0.69, at +24% tokens. It removes variance more than it
raises the mean — one-sweep answers ranged 0.35–0.52, region-by-region answers 0.67–0.73.
Full evidence, including what failed: https://github.com/stilletto/analyzing-by-region
