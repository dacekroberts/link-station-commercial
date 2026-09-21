# Briefing for a Claude Code session

Read this before touching anything. It covers what the project is, what has
already been settled, and where the boundaries are.

---

## The project

Measure commercial density in concentric rings around the sixteen Link 1
Line light rail stations inside Seattle city limits, and look at what that
says about how businesses choose locations near transit.

The underlying question is about locational choice: do businesses cluster
near transit because transit brings customers, or do transit lines get built
where commerce already exists? The analysis cannot settle that — it is
correlational and says so — but it is designed to produce evidence that
bears on it rather than a map that merely looks suggestive.

Three analyses carry the argument:

1. **Distance gradient.** Does commercial density decline across rings at
   0.1 / 0.2 / 0.3 / 0.6 miles? Rings supply the counterfactual a single
   buffer lacks, and expand ~16 station observations to ~60 station-ring
   ones.
2. **Ridership relationship.** Does station boarding volume track commercial
   density? Heavily caveated — see the access-mode limitation.
3. **Chain footprint.** Do multi-location brands appear at more stations than
   independents? A firm with a real estate department placing eight
   locations near stations is revealed preference about location strategy,
   and is the strongest signal available in this data.

Deliverable: a three-page Streamlit site — heatmap, findings, methodology.
Audience is hiring managers. It is a portfolio piece.

---

## Who you're working with

Introductory Python. No GIS background at all.

That changes how you should help. Explain the geospatial concepts as you
touch them — why buffering in degrees is wrong, what a spatial join does,
why the rings are annuli rather than nested circles. Working code they don't
understand is worth less here than slightly slower progress they can defend
in an interview.

They have roughly 14 hours total. Protect that budget actively; see the time
discipline section.

---

## Read these, in order

1. `README.md` — architecture and the two known failure modes
2. `PLAN.md` — nine sessions with time budgets and bail-out triggers
3. `config.py` — every tunable, with the reasoning in comments
4. `data/raw/README.md` — the manual downloads (GTFS, license CSV, GIS donor,
   ST station shapefile, ridership)
5. `DECISIONS.md` — the running record; "Changes" section up top for
   macro-level deviations, template sections below fill in as work proceeds

---

## Already decided — do not relitigate

These were worked through at length. Reopening them costs hours the project
does not have.

**Scope: Seattle 1 Line only.** The 1 Line runs north to Lynnwood and south
past the airport, and the 2 Line is entirely on the Eastside. A cross-station
comparison outside Seattle would need each city's own business license data,
and sourcing seven more municipal datasets is out of budget. Sixteen stations,
Northgate through Rainier Beach. (Seattle's export does list ~30% of rows at
non-Seattle addresses — businesses licensed here but located elsewhere. Step 2
filters to `City == "SEATTLE"`. This does not widen scope.)

**Commercial data: business licenses, not OpenStreetMap.** OSM was considered
and rejected. Its coverage bias correlates with urban density — the very
thing being measured — so it is fatal to cross-station comparison. More
importantly, licenses carry NAICS codes and issue dates, which the tenure
and chain analyses require and OSM does not have.

**Which license dataset: the CSV, not the GIS layer.** Seattle publishes the
same licenses twice — a tabular CSV ("Active Business License Tax
Certificate") and a pre-geocoded GIS layer ("Seattle Business License"). The
CSV is canonical; the GIS layer is a geometry donor only (joined by account
number in step 3, then Census-geocode the remainder). The GIS layer omits
~10% of Seattle businesses with no way to characterise the gap — the same
bias problem that sank OSM, smaller. Full rationale in `DECISIONS.md`.

**Ridership: manual export.** The Sound Transit dashboard is an embedded
Power BI report. The data is not in the page HTML and there is no CSV
endpoint. Sixteen numbers, needed once. Manual entry is correct.

**Overlapping downtown buffers: allowed and disclosed.** Westlake, Symphony,
Pioneer Square and International District overlap, so businesses there count
for multiple stations. Nearest-station assignment was rejected because it
understates how many stations genuinely serve a downtown block.

**Architecture: pipeline writes `outputs/`, app reads it.** Nothing else
crosses that boundary.

---

## Deliberately out of scope

Documented in the methodology as future work. Do not build these.

- Control corridors (Ballard, Fremont)
- The 2 Line
- Before/after analysis around the October 2021 Northgate–U District openings
- Commercial foot-traffic data (Placer.ai, Advan, SafeGraph)
- Scraping Google Popular Times — no API exists and it violates Google's terms

If the user proposes adding one, the honest answer is usually that it's a
good idea that doesn't fit the hours, and belongs in the future-work section.

---

## Technical invariants

**The CRS rule.** EPSG:4326 measures in degrees; a degree of longitude is
about 75 km at Seattle's latitude. Never buffer or measure distance in it.
Project to EPSG:32610 (UTM 10N, meters), do the geometry, project back to
4326 for Folium. Any new spatial code follows this pattern.

**Keep `requirements.txt` lean.** Streamlit Cloud installs from that filename
automatically. Adding geopandas, folium, or anything with compiled
dependencies to it will break the deploy. Pipeline dependencies belong in
`requirements-pipeline.txt`.

**`outputs/` is committed to git.** The deployed app cannot regenerate it.
This is intentional and `.gitignore` reflects it.

**Rings are annuli.** Each ring subtracts the disc inside it. Without the
subtraction every business counts in every outer ring and the gradient is
meaningless. Verify this survives any refactor of `step4_rings.py`.

**Station names are the join key** between ridership and station data. Step 4
warns about unmatched stations. That warning is never noise.

---

## What only the user can do

Three downloads and one inspection.

- Download the GTFS zip, business license CSV, and ridership numbers
- Open the business license CSV and determine: exact column names, whether a
  status/expiration column exists, whether an employee count exists

**Status as of 2026-09-06 (Session 1):** GTFS zip, license CSV, and the GIS
donor layer are downloaded and in `data/raw/`. The CSV inspection is done —
columns confirmed and mapped, **no status/expiration column** (active-only
snapshot → tenure among survivors is computable, survival is not), **no
employee count**. Ridership numbers are still outstanding (Session 5).

---

## Time discipline

The plan has two hard bail-outs. Enforce them; a beginner will not
spontaneously abandon a problem they're deep into.

**GTFS join: 60 minutes.** If `step1_stations.py` won't produce a sensible
station list, don't grind on it. Fallback ladder: (1) pull station points
from `LINKStations.shp` in `st_gis_shapefiles.zip` — an authoritative Sound
Transit layer, no route-pattern matching; (2) failing that, hand-build
`data/processed/stations.csv`, sixteen rows, three columns. Either way, note
it in `DECISIONS.md`. It costs nothing analytically.

**Geocoding: one improvement attempt.** If the match rate is below 80%, add
`usaddress` parsing in step 2 and re-run once. Then accept 75% or above and
document it. A reported match rate is worth more than an unreported higher
one.

Watch for a third: environment setup. If geopandas won't install via pip
after 45 minutes, switch to conda and move on. Debugging a build toolchain
is not what this project is teaching.

---

## Don't do these

**Don't write the prose in `pages/2_Findings_&_EDA.py`.** Three blocks are marked
`TODO — write this up`. Those are the user's analysis and the reason the
project exists. Help them think it through, ask what they're seeing in the
numbers, react to their draft — but the interpretation has to be theirs.
An agent-written insight section is the thing that makes a portfolio piece
worthless.

**Don't automate the Power BI extraction.** Roughly three hours with a real
chance of failure, for sixteen numbers needed once.

**Don't add scope.** The design is locked and the budget is tight.

**Don't skip `DECISIONS.md`.** Prompt the user to fill it in after each
session. The methodology page is assembled from it, and these choices are not
reconstructable later.

**Don't oversell a weak result.** If the gradient comes out flat, that is a
finding: stations were routed through already-commercial corridors, so
distance within a third of a mile may not be what varies. Help write that up
honestly rather than hunting for a specification that produces a positive.

---

## Useful context

**NE 130th / Pinehurst** was slated to open in 2026. **Checked in Session 2
(2026-09-13, GTFS feed dated 2026-08-28): not present.** It is not in
`SEATTLE_1LINE_STATIONS`, not in `stations.csv`, and stays out of the
analysis — 16 stations, as originally scoped. If the GTFS feed is
re-downloaded later and it has since opened, re-check before assuming this
still holds; if it's running by then, add it and note that a station open for
only part of the window isn't comparable to one open throughout.

**Three stations have known explanations** for looking empty, and they are
worth checking against the results rather than treating as data errors:
Rainier Beach's commercial core sits several blocks from the platform; SODO
is surrounded by industrial uses; the land around Stadium is largely Metro
bus bases.

**Northgate's ridership is transfer- and park-and-ride-heavy.** Those riders
never pass a storefront. It is the clearest illustration of why boardings
overstate pedestrian exposure, and belongs in the findings discussion.

---

## Progress

**Session 1 — done (2026-09-06).** venv + geo stack (Python 3.12 / `uv`),
Streamlit boots with all four empty states, `git init` + commits, all
downloads in `data/raw/`, CSV inspected and `COLUMN_MAP` filled, business-
license source decided. Deviations from the plan are logged in `DECISIONS.md`
under "Changes".

**Session 2 — done (2026-09-13).** GTFS join fixed (route matching was
substring-catching the shuttle bus-bridge route) and re-run: 16 of 16 Seattle
stations, zero unmatched warnings. NE 130th/Pinehurst confirmed absent from
the feed (see "Useful context" above).

**Next: Session 3 — clean the business data.** Wire the deferred step-2 work
(Seattle filter, carry account number + start date, dedupe on account
number), then the NAICS storefront sample review — that judgment call is the
user's.

The point of Session 1 was to hit every environment failure while it cost an
hour instead of a project. It did its job.
