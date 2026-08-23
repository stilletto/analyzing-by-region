# Warehouse cutover plan — Northfield site

Prepared by the operations lead. Six weeks, starting Monday 6 October.

The Northfield warehouse currently runs on the legacy stock system (green screens, one
Oracle box in the corner office, maintained by a contractor who visits quarterly). We are
moving it to the platform the other four sites already use.

**Week 1 — Survey.** Two engineers on site for three days. Photograph the racking, export
the current stock table to CSV, interview the three shift supervisors about how they
actually work, write it all up. Warehouse keeps operating normally.

**Week 2 — Data cleanup.** Take the CSV, dedupe SKUs, map legacy location codes
(aisle-bay-level, one string) onto the platform's three separate fields. The contractor
says roughly 4% of rows have malformed location codes; we will fix those by hand. Load
the cleaned file into the platform staging environment.

**Week 3 — Parallel run.** Both systems live. Pickers scan into the legacy terminals as
usual; a temp worker re-keys each transaction into the platform within the hour. At end
of week we compare stock levels between the two systems; if they agree we proceed.

**Week 4 — Training.** Two half-day sessions per shift, all 40 warehouse staff. New
handheld scanners arrive Monday of this week and are handed out during training.

**Week 5 — Cutover.** Friday evening after the last van leaves: freeze the legacy system,
take a final stock export, load it into production, switch the label printers over.
Saturday morning a skeleton crew does a 200-item spot count against the platform.
Monday the site runs on the platform only.

**Week 6 — Hypercare.** Both engineers on site all week. Legacy system stays powered on
but read-only, in case we need to look something up.

Notes agreed with the site manager: peak season starts the second week of November, so
this must be finished by end of October. The contractor is available for questions but is
on another engagement and cannot come on site. Two of the three shift supervisors have
been at Northfield over fifteen years; the third started in August. Staff turnover among
pickers is high — about a third of the team has joined in the last six months. There is
no test environment that mirrors Northfield's racking layout.
