# Development Process Insights

A macro-level look at how this project actually unfolded versus how it was
planned, written at the end of Session 7. For speaking to the process —
in an interview, a portfolio writeup, or just your own memory of how this
went — not for the analytical findings themselves (those are in
`DECISIONS.md`'s Observations section and, eventually, `pages/2_Findings.py`).

---

## The shape of it: a tight plan that flexed in the right places

`PLAN.md` and `initialscript.md` laid out nine sessions, ~14 hours, with
explicit bail-out triggers at the riskiest points (environment setup,
GTFS parsing, geocoding match rate). That discipline mostly held — the
scope stayed locked (Seattle 1 Line only, business licenses not OSM,
manual ridership, no control corridors), and none of the hard bail-outs
actually triggered, because the underlying work came in under budget almost
everywhere. What *didn't* hold to the letter was the specific shape of a
few sessions — and every one of those deviations was a considered decision,
not scope creep for its own sake.

## Where the plan was right to be cautious, and wasn't needed

The plan pre-flagged three real risks: environment setup, the GTFS
station join, and geocoding match rate. All three surfaced exactly as
predicted, and all three resolved faster than budgeted:

- **Environment**: the system Python (3.14) was too new for the geo
  stack's compiled wheels — exactly the kind of thing the plan's "switch to
  conda after 45 minutes" gate anticipated. The actual fix (a `uv`-managed
  Python 3.12) took under a minute once identified, no conda needed.
- **GTFS join**: `step1_stations.py`'s route matching had a real bug
  (a bus-bridge shuttle route was accidentally included), producing 17
  "stations" instead of 16. Diagnosed and fixed inside the session's own
  60-minute budget, nowhere near the hand-build fallback.
- **Geocoding**: the plan expected to possibly need `usaddress` parsing to
  clear an 80% match-rate bar. The actual pipeline — reworked mid-project to
  donor-join against the City's own GIS layer first — hit 99.5% overall
  without ever touching the fallback.

The lesson underneath all three: the plan's risk assessment was accurate.
What made the actual execution faster wasn't luck — it was verifying each
assumption immediately rather than building on top of it, which is also
the thread running through everything below.

## The real story: three deliberate architecture pivots

### 1. Business-license data: CSV plus a geometry donor, not either alone

The original plan assumed one CSV, geocoded via the Census bulk geocoder.
Partway through, the user surfaced a second City-published dataset (a
pre-geocoded GIS layer of the same businesses) and asked which was
better. The answer took real investigation, not a guess: the GIS layer
turned out to be a strict *subset* of the CSV, silently missing ~10% of
Seattle businesses with no way to characterize the gap — structurally the
same coverage-bias problem that had already gotten OpenStreetMap rejected
in the original scope decision. The resolution split the difference
correctly: CSV as the canonical source (so every drop stays visible and
reportable), GIS layer as a geometry donor joined in behind the scenes,
collapsing the geocoding risk from "hope the Census geocoder clears 80%"
to "90% comes pre-solved, Census only touches the leftover 10%." That's a
better architecture than either the original plan or the naive "just use
the nicer dataset" instinct would have produced alone.

### 2. Ridership: from one month to a validated year

The plan wanted one month's ridership, read off a dashboard by hand. The
user proposed capturing all twelve months instead — more manual reading,
but a full-year average instead of a single arbitrary snapshot. That
alone would have been a reasonable scope increase. What made it a genuinely
better decision was the follow-up: the dashboard also showed a second
number ("average boardings per day"), and rather than assume it was
redundant with the monthly total (a very reasonable assumption — division
by days-in-month, right there in the data), it got checked against all 192
actual station-months. The assumption was wrong — it wasn't a simple
derivation at all. But the underlying instinct (it wouldn't add real signal
for this analysis) turned out right anyway, confirmed at r=0.998 once
aggregated to the station level. Two lessons compound there: a plausible
assumption is still worth checking, and being wrong about the mechanism
doesn't mean you were wrong about the conclusion.

### 3. The map: from "generate the file" to a real, tested deliverable

Session 7 was budgeted at 1.5 hours for "render the map, tune two
parameters, commit." What it actually required: diagnosing a dead
third-party tile provider, tracking down a genuinely obscure, still-open
upstream bug in a bundled JS plugin that was silently breaking the whole
map (not just the part that looked broken), and then — across several
rounds of the user's own follow-up requests — building out a full
NAICS-category pin system with clustering, the real rail alignment from
GTFS geometry, and enriched hover tooltips tying every pin back to the
ring analysis. None of that was in the original plan. All of it shipped
because each addition was evaluated on its own merits rather than waved
through by momentum — including one dynamic-filter idea that got a clear
no (real complexity, marginal value, competing with Session 8's higher-value
hours) in favor of a cheaper version that delivered most of the same
value with none of the new risk.

## The pattern underneath all of it: verify, don't assume

The single most repeated move across all seven sessions wasn't a technical
technique, it was a discipline: **when something looked right, it still got
checked before being trusted or documented as fact.** A partial list of
things that looked correct on first pass and turned out not to be, caught
specifically because they were checked rather than assumed:

- The GTFS route match (looked like 16 stations, was actually 17 with 3
  bogus entries from a shuttle route).
- "Seattle's business license dataset stops at the city line" — a claim
  baked into the original project brief, disproven the moment the actual
  CSV was inspected (30% of rows are non-Seattle).
- The "average boardings per day" redundancy claim (right conclusion,
  wrong reasoning, caught by checking the actual numbers).
- The chain analysis's `station_count > 1` definition — plausible, used
  without question until the plan's own required "verify a handful by hand"
  step surfaced two single-location businesses masquerading as
  multi-station chains. That one bug, left unfixed, would have put a
  >5x-overstated headline number (45.7% vs. the real 8.8%) directly into
  the portfolio's Findings page.
- Multiple map bugs that *looked* like they'd rendered fine in a
  screenshot and turned out, on actually reading the browser console, not
  to have.

None of these were exotic failures. Every one of them was the kind of thing
that would have shipped quietly wrong if the answer had been assumed
instead of checked. That's arguably the most transferable lesson from this
project, more than any individual technical decision: a plausible-looking
result and a correct one are not the same thing, and the gap between them
is usually cheap to close if you look.

## Where scope stayed disciplined

Worth naming explicitly, because it's easy to lose track of restraint amid
a list of things that got built: several ideas were raised, evaluated, and
declined, not because they were bad ideas but because they didn't earn
their cost against the time remaining. The dynamic NAICS-filter control is
the clearest example — technically straightforward, explicitly weighed
against Session 8's write-up (the plan's own "highest-value hours"), and
set aside in favor of a cheaper alternative that captured most of the same
value. That's the same discipline the original plan asked for
("do not chase beauty — this is illustration") applied correctly under
real pressure to keep adding features, not just stated as a principle
upfront.

## What this means for how the finished project should be described

The honest framing isn't "the plan was wrong" or "the plan was followed
exactly" — it's that **the plan was a good starting estimate that got
revised in public, with reasons, every time new information arrived**,
and every revision is traceable in `DECISIONS.md`. That's a more accurate
and more defensible story for a portfolio piece than either extreme: not
"I never deviated," and not "I improvised the whole way" — but "I had a
plan, I hit exactly the friction points I expected to hit, I found some I
didn't expect, and every departure from the original design is written
down with the reasoning, including the one real bug that would have
overstated a headline finding by 5x if a required verification step hadn't
caught it."
