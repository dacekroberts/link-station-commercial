# Development Process Insights

A session-by-session look at how this project actually unfolded versus how
it was planned, written at the end of Session 7. For speaking to the
process — in an interview, a portfolio writeup, or just your own memory of
how this went — not for the analytical findings themselves (those are in
`DECISIONS.md`'s Observations section and, eventually,
`pages/2_Findings.py`).

Each session below: what the plan expected, what actually happened, and the
insight that came out of the gap between them (or, where there was no gap,
why the plan's caution turned out to be exactly right).

---

## Session 1 — Environment and data

**Planned:** venv, install the geo stack, confirm Streamlit boots, `git
init`, download three files by hand. A 60-45-minute conda bail-out gate for
environment setup specifically.

**What happened:** the bail-out trigger the plan wrote for was almost
exactly right — the system Python (3.14) was too new for the geo stack's
compiled wheels, precisely the failure mode the gate anticipated. The fix
came in far under the 45-minute budget once diagnosed: a `uv`-managed
Python 3.12, no conda needed. Separately, the user did their own research
alongside the planned downloads and surfaced a second City-published
dataset (a pre-geocoded GIS layer of the same businesses) that wasn't in
the original plan at all.

**Insight:** the plan's risk assessment for environment setup was accurate
down to the specific failure mode, which is worth noticing — pre-flagging
"this will probably break" and pre-committing to a fallback made the actual
break a non-event instead of a derailment. Separately, the GIS-layer
discovery set the tone for the rest of the project: bringing in outside
information didn't get adopted on the spot, it got investigated (see
Session 3) before being trusted.

---

## Session 2 — Station coordinates

**Planned:** parse GTFS, get 16 station coordinates, 60-minute bail-out to
hand-building the file if the join didn't work cleanly.

**What happened:** the join produced 17 "stations," not 16 — a bus-bridge
shuttle route (`1-SHUTTLE`) had been swept in alongside the real train
because the original route-matching logic substring-searched a field where
"1 Line" also appeared in the shuttle's own long name. Diagnosed and fixed
well inside the session's budget: exact match on `route_short_name`
instead. Zero unmatched-station warnings after the fix, and a
double-check (NE 130th/Pinehurst) confirmed it genuinely wasn't in this
GTFS snapshot, closing an open question from the original brief.

**Insight:** "the join ran without an error and produced a plausible-looking
number" is not the same bar as "the join is correct." 17 is close enough to
16 that it could have looked right at a glance; only checking the actual
row count against the known-correct answer (16 real stations) caught it.
This is the first appearance of a pattern that recurs through the rest of
the project.

---

## Session 3 — Clean the business data

**Planned:** fill `COLUMN_MAP`, run the NAICS filter, hand-sample the
result, adjust the filter if the sample says so.

**What happened:** the sample review did exactly what the plan intended —
and then some. Two categories got individually excluded after review
(parking lots, and NAICS's own "everything else" catch-all within personal
services), one structurally similar catch-all got reviewed the same way and
explicitly *kept* because the sample told a different story. Also caught
along the way, not originally planned for: the project brief's own claim
that "Seattle's business license dataset stops at the city line" turned out
to be false the moment the actual file was opened — about 30% of rows are
non-Seattle addresses.

**Insight:** the same review process produced two opposite outcomes on
structurally similar data (two NAICS catch-all codes, one dropped, one
kept), which is itself the point — the process was doing real
discrimination, not rubber-stamping a predetermined "catch-alls are bad"
rule. And a claim that had been sitting unquestioned in the project's own
founding document since before Session 1 didn't survive five minutes of
actually looking at the data. Written documentation is not automatically
more reliable than an assumption; it's just an assumption someone wrote
down earlier.

---

## Session 4 — Geocode

**Planned:** send addresses to the Census bulk geocoder, accept anything
≥75%, add `usaddress` parsing if below 80%.

**What happened:** the Session 1 discovery (the GIS geometry layer) paid
off here specifically — rather than geocoding from scratch, the clean CSV
was joined against the City's own pre-geocoded points first, and only the
~10% that didn't match went to the Census geocoder. Result: 90.2% solved
without an API call, 94.9% of the remainder from Census, 99.5% overall.
The `usaddress` fallback was never needed.

**Insight:** this is the clearest example in the project of a Session 1
decision paying compound interest three sessions later. The GIS layer had
already been ruled out as the *primary* source (Session 1 — it hides ~10%
of businesses with no way to characterize the gap), but that same
investigation is what made it obvious it could still be useful as a
*secondary* input. Rejecting a data source for one purpose and reusing it
for another isn't a contradiction — it's what actually understanding a
dataset's shape, rather than just accepting or rejecting it wholesale,
makes possible.

---

## Session 5 — Ridership

**Planned:** one month, read off the dashboard by hand, ~30 minutes.

**What happened:** reconfigured mid-session at the user's initiative — all
twelve months instead of one, still fully manual (screenshots, not
automation), for a full-year average instead of one arbitrary snapshot.
Then a second, more specific decision: the dashboard showed a second
number ("average boardings per day") that looked like it would obviously be
redundant with the monthly total — a simple division, not worth
transcribing. That assumption got checked against all 192 actual
station-months instead of taken on faith, and it was **wrong** — the two
numbers don't relate by any simple arithmetic. But checked a different way
(correlating the two metrics once averaged to the station level), the
original instinct to skip it turned out right anyway: r = 0.998.

**Insight:** this session is the cleanest illustration in the whole project
of the difference between a right answer and a right reason. "Don't
bother transcribing the second number" was correct. "Because it's just
total ÷ days" was not. Reaching the right conclusion by checking, rather
than by a plausible-sounding shortcut, is what makes the conclusion
trustworthy enough to write into a methodology page — a right answer
reached by an unverified guess is not distinguishable, from the outside,
from a wrong answer that hasn't been caught yet.

---

## Session 6 — Rings, and the first real numbers

**Planned:** run the ring analysis, read the gradient, check the three
stations with known explanations (Rainier Beach, SODO, Stadium), hand-verify
the chain output.

**What happened:** the required hand-verification step on the chain output
— "do brand names normalize correctly?" — surfaced something well beyond a
normalization typo. Two genuinely single-location businesses were showing
up as "present at 4 stations" each, because the downtown buffer overlap
(already known and disclosed for the density numbers) turned out to
contaminate the chain metric far more severely. Checked systematically
rather than patched for just the two examples found by chance: 41% of all
normalized brands showed the same pattern. The metric as originally defined
would have told the portfolio's Findings page that 45.7% of locations near
stations are chains; the corrected figure is 8.8%.

**Insight:** "verify a handful by hand" is easy to treat as a formality —
a box to check before moving on to the interesting part. Here it was the
step that caught a bug that would have put a headline number in a public
portfolio piece off by a factor of five. The gap between "spot-checked a
few examples and they looked fine" and "checked systematically once a
pattern was suspected" is where this bug lived; the first pass (two
examples) found the smell, but it took the second pass (all 3,907 brands)
to find the actual scope of the problem and fix it correctly rather than
just patching the two cases that happened to be noticed.

---

## Session 7 — The map

**Planned:** render the heatmap, tune two rendering parameters by eye,
confirm it embeds in Streamlit, commit. Budgeted 1.5 hours.

**What happened:** the most-expanded session in the project, across two
distinct phases. First, fixing what was actually broken — a dead
third-party tile provider (CartoDB now requires a paid key) and a
genuinely obscure, still-open upstream bug in a bundled JS plugin that was
silently preventing the *entire* map from rendering, not just the part
that looked visibly wrong. Second, several rounds of the user's own
follow-up requests building well past the original scope: a
NAICS-category pin system with clustering and a legend, the real GTFS rail
geometry with a label, enriched hover tooltips tying individual businesses
back to the ring analysis, station-level ridership tooltips. One request —
a dynamic, code-driven filter control — got a considered no, not a
reflexive one: technically straightforward, but weighed explicitly against
Session 8's higher-value remaining hours and declined in favor of a
cheaper alternative (more static toggle layers, reusing an already-proven
pattern) that delivered most of the same value without new untested
complexity.

**Insight:** two lessons, not one. First: a bug can be invisible in exactly
the way that makes it dangerous — the map "looked" like it might be
loading a plain white basemap, but the real failure (an uncaught JS
exception killing every layer added after the heat layer) wouldn't have
been found without actually reading the browser's own console rather than
judging by the screenshot. Second: scope discipline under real pressure to
keep adding features looks like saying yes to several genuinely good ideas
and no to at least one, on the merits, each time — not like a blanket rule
against changes, and not like accepting everything a session's momentum
carries in.

---

## Looking back across all seven sessions

Two patterns show up repeatedly enough to name directly, because they're
more transferable than any single technical decision above.

**Verify, don't assume, even when the assumption is plausible.** Every
session from 2 through 7 has at least one moment where something that
looked correct — a row count, a stated fact in the project's own founding
document, a metric that seemed obviously derivable, a filter definition
that had been running without complaint — turned out not to be, and was
only caught because it got checked rather than trusted. None of these were
exotic failures requiring special expertise to find; every one was found by
the same move: look at the actual number, the actual console output, the
actual sample, before writing the conclusion down.

**Scope discipline is a series of individual decisions, not one upfront
rule.** The project absorbed a real amount of change from its original
plan — a second data source, a full year of ridership instead of one
month, a much richer map than originally specified — and stayed
disciplined anyway, because each addition was evaluated against what it
actually cost and actually bought, right up through the last session, where
a plausible feature request got turned down explicitly because something
more valuable was waiting. "Protect the highest-value hours" is easy to
agree with as a principle; the useful version of it shows up in the
specific moments where an idea gets set aside in favor of something else,
with the reasoning written down.
