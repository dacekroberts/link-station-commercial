# Project summary: commercial density around Seattle's light rail stations

A complete account of what this project built, measured, used and taught,
organized by concept rather than by date. Written 2026-10-01, when the
site reached its final version. Figures are current as of that date; the
dated records in `docs/DECISIONS.md` keep the history of how each one got
there.

- **Live site:** https://link-station-commercial-daceroberts.streamlit.app
- **Repository:** github.com/dacekroberts/link-station-commercial (public)
- **Author:** Dace Roberts

## Contents

1. [The project in one page](#1-the-project-in-one-page)
2. [Research design](#2-research-design)
3. [Data sources and licensing](#3-data-sources-and-licensing)
4. [The pipeline, step by step](#4-the-pipeline-step-by-step)
5. [Findings](#5-findings)
6. [Methodology and limitations](#6-methodology-and-limitations)
7. [The website](#7-the-website)
8. [The heatmap in detail](#8-the-heatmap-in-detail)
9. [Privacy and data ethics](#9-privacy-and-data-ethics)
10. [Quality control and verification](#10-quality-control-and-verification)
11. [Errors found and corrected](#11-errors-found-and-corrected)
12. [Repository and deployment](#12-repository-and-deployment)
13. [Tools and technologies](#13-tools-and-technologies)
14. [Concepts learned](#14-concepts-learned)
15. [How the project was built](#15-how-the-project-was-built)
16. [Decided against, and out of scope](#16-decided-against-and-out-of-scope)
17. [Open items](#17-open-items)
18. [Timeline](#18-timeline)

---

## 1. The project in one page

**Question.** Do businesses cluster near Seattle's light rail stations, and
what does the pattern of that clustering say about how businesses choose
locations near transit?

**Scope.** The sixteen Link 1 Line stations inside Seattle city limits,
Northgate through Rainier Beach. Seattle-only because each additional city
would need its own business-license dataset. The 2 Line and 1 Line stations
outside Seattle are out of scope.

**Method.** Concentric rings (0.1, 0.2, 0.3 and 0.6 miles) around each
station, built as annuli so each ring excludes the one inside it. Business
density is measured per ring, then compared across rings, across stations,
against ridership, and for chains versus other businesses.

**Deliverable.** A six-page Streamlit site aimed at hiring managers:
Overview & Introduction, Heatmap, Findings & EDA, Methodology & Limitations,
Flowchart, and About.

**Headline results.**
- Business density falls **62.9%** from ring 1 to ring 4 (837 to 310
  businesses per square mile), with a slight **+0.9%** rise from ring 2 to 3.
- Ridership and nearby business density correlate moderately: **r = 0.684**.
- Businesses spread across stations **1.8x** as unevenly as ridership does.
- Chain share is highest at the platform: **9.5%** in ring 1, falling to
  **6.8%** by ring 3, then level.
- **4,120 of 11,409** geocoded Seattle businesses (36.1%) sit within 0.6
  miles of a station.

**What it can't answer.** Whether transit draws businesses or follows
existing commerce. The analysis is correlational and says so throughout.

---

## 2. Research design

### The larger question

Do transit platforms bring businesses into their neighborhoods, or do
cities place transit along preexisting commercial corridors? The project
measures the pattern this produces, not which came first. Much of the 1
Line ran through neighborhoods that already had commercial cores, which
supports the second reading for older stations; University of Washington
station shows a line reaching campus and hospital land instead.

### Three testable questions (stated before any data was pulled)

| Section | Hypothesis | Result |
|---|---|---|
| Concentric ring gradient | Does commercial density drop off with decreased proximity to transit hubs? | **Supported** in aggregate (−62.9%), though half the stations deviate individually |
| Ridership | Does station boarding volume track commercial density? | **Loosely supported** (r = 0.684, but leaning on Westlake) |
| Chains | Do multi-location brands appear at more stations than independents? | **Both supported**, see below |

The chain question shifted mid-analysis to a sharper one: **does chain share
rise approaching the platform, as commercial density does?** The Findings
page states both questions and says the second came up during the work,
rather than presenting it as a starting hypothesis. Doing otherwise would be
HARKing (hypothesizing after the results are known).

### Why rings

A single buffer says how many businesses are near a station but gives
nothing to compare against. Rings supply that comparison (is ring 1 denser
than ring 4?), and they expand 16 station observations to 64 station-ring
observations. The 0.3-mile mark is the walkshed of interest (a five-to-six
minute walk); the 0.3 to 0.6 band is the comparison baseline. The outer
edge was checked against Yang and Diez-Roux (2012), a national study of
walking-trip distance by purpose.

---

## 3. Data sources and licensing

| Source | What it supplied | License status |
|---|---|---|
| City of Seattle, Active Business License Tax Certificate (CSV, `wnbq-64tb`) | Every business: name, NAICS code, address, ownership type, start date | Public Domain plus portal terms; canonical source for every analysis |
| City of Seattle, Business License GIS layer | Point coordinates only, joined by account number | Covered by the portal terms; geometry donor only |
| Sound Transit GTFS | Station coordinates and the 1 Line's track shape | Limited, revocable license with a flow-down obligation, discharged on the Methodology page |
| Sound Transit ridership dashboard | Average monthly boardings, Jan to Dec 2025, transcribed by hand | Website terms restrict republication; permission requested 2026-09-20, reply needed no immediate action |
| U.S. Census Bureau geocoder | Coordinates for the 1,121 businesses the GIS layer didn't cover | Required notice added to Methodology |
| OpenStreetMap tiles | The heatmap's basemap | ODbL, attribution present and verified in both light and dark mode |
| Seattle land use zoning | Used once, in the privacy check | PDDL; not redistributed |

**Why the CSV and not the GIS layer as the primary source.** The GIS layer
contains only the roughly 90% of businesses the City's own geocoder placed.
It silently omits about 5,700 businesses, and the missing ones aren't
random (new, home-based, informal-address). Starting from the CSV and
geocoding the rest makes every dropped record visible. The same
coverage-bias reasoning ruled out OpenStreetMap as a business source.

Every source's license was read and logged in `docs/data_sources.md`.

---

## 4. The pipeline, step by step

The pipeline (`src/`) runs locally and writes CSV checkpoints, so a failure
costs one step, not the whole run. It writes only to `outputs/`; the website
only reads `outputs/`.

### Step 1: stations (`step1_stations.py`)
- Reads the GTFS feed and extracts the 16 Seattle stations of the 1 Line.
- Route matching uses the exact `route_short_name == "1 Line"`; a looser
  match picked up the wrong routes.
- Station names are aliased so GTFS, ridership and business data agree:
  16 of 16 matched with zero warnings.

### Step 2: clean the businesses (`step2_clean_businesses.py`)
- 84,390 raw rows, of which 58,774 have a Seattle address (the export also
  lists Seattle-licensed businesses located in Kent, Bellevue and Tacoma).
- Keeps storefront categories by NAICS prefix: `44` and `45` (retail),
  `722` (food service), `812` (personal services).
- Two catch-all codes excluded individually after hand-sampling:
  `812930` Parking Lots and Garages (826 rows) and `812990` All Other
  Personal Services. `459999` was reviewed and kept.
- Deduplicates, validates addresses, and fixes two data-quality bugs found
  in review (blank business names, a `19000101` sentinel start date).
- Result: **11,466** clean businesses.

### Step 3: geocode (`step3_geocode.py`)
- **Pass 1, the GIS donor join:** 90.2% (10,345 of 11,466) get the City's
  own coordinates, joined on City Account Number. The layer arrives in
  EPSG:2926 (Washington State Plane) and is reprojected to EPSG:4326.
- **Pass 2, the Census bulk geocoder** on the 1,121-row remainder: 94.9%
  (1,064 of 1,121).
- **Overall: 99.5%** (11,409 of 11,466). The 57 that failed both passes are
  dropped and disclosed.
- Batches are cached; a cached batch is reused only if each row's echoed id
  and address still match, so stale coordinates can't land on the wrong
  business.

### Step 4: rings and the three analyses (`step4_rings.py`)
- Projects to **EPSG:32610** (UTM zone 10N, meters), builds the four ring
  annuli, and spatially joins businesses into them: **6,847** business-ring
  matches.
- **Gradient:** density per ring per station. Empty rings (Northgate and
  UW ring 1, Rainier Beach ring 3) count as zero density rather than
  dropping out of the average.
- **Ridership:** joins average monthly boardings to the count of
  businesses within 0.3 miles.
- **Chains:** normalizes brand names, counts each brand's **distinct
  locations** (coordinates rounded to about one meter) and stations. A chain
  is a brand with two or more distinct locations. Three corporate
  food-service contractors (Compass One, Bon Appetit Management, Flik
  International) are excluded from the chain analysis only.
- Writes `ring_stats.csv`, `station_stats.csv`, `chain_stats.csv`,
  `chain_ring_stats.csv` and `citywide_coverage.csv`.

### Step 5: the map (`step5_map.py`)
- Builds the Folium heatmap and saves it as `outputs/heatmap.html`.
  Section 8 covers it in detail.

---

## 5. Findings

### Concentric ring gradient
- Average density by ring: **837 → (ring 2) → (ring 3, +0.9%) → 310**
  businesses per square mile, a net decline of **62.9%**.
- **Graph 2** splits the stations evenly: eight follow the declining
  pattern and eight run against it. Six of sixteen stations show a ring 2
  to 3 rise, and four of those six are in the against-pattern group.
- Two explanations recur:
  - **Geographic limits.** Northgate, UW, Stadium, SODO and Rainier Beach
    sit beside parks, campus, industrial land or water rather than
    commercial cores.
  - **Downtown buffer overlap.** Westlake, Symphony, Pioneer Square and
    International District/Chinatown sit 0.27 to 0.41 miles apart, so their
    rings overlap. One storefront can count toward several stations, and a
    station's outer ring can reach the next station's close-in commerce.

### Ridership
- **r = 0.684** between average monthly boardings and businesses within 0.3
  miles. Because every station's walkshed is the same area (0.282 sq mi),
  the count and the density give identical results.
- **Westlake is a high-leverage point:** removing it drops r to 0.431. The
  rank-based Spearman correlation is 0.555.
- **Graph 4 (dot plot)** and **Table 3 (coefficient of variation):**
  businesses vary 1.8x as much as ridership relative to their averages.
  Westlake and Symphony sit about two standard deviations above the mean on
  the business side (z = 2.40 and 1.98); every other station is within one.
- UW and Northgate rank fifth and seventh by ridership but have few
  businesses (5 and 17), a reminder that not every station serves a
  commercial purpose.

### Chains
- **116 brands** have two or more distinct locations near the stations,
  accounting for **6.7%** of locations. Subway leads with seven locations
  within range of eight stations.
- **Original question:** chains appear near **2.95** stations on average
  against **1.66** for single-location businesses. Partly built in: more
  locations mean more chances to sit near different stations.
- **Refined question:** chain share by ring is **9.5% / 7.5% / 6.8% /
  6.8%**. Per square mile, chain density falls **73.6%** from ring 1 to
  ring 4 against **61.8%** for other businesses, so chains lean into
  platform proximity harder than other businesses.
- **The ring 3/4 tie** (6.82% vs 6.77%) is consistent with downtown buffer
  overlap: Westlake and Symphony show no fall-off between those rings and
  hold 39% of ring 4's chain locations. It is stated as "possibly", because
  removing the downtown stations doesn't restore a clean decline.

### In summary
Commercial density, ridership and chain share all point the same way, and
the pattern is consistent across three views of the same data. Locational
choice near public transit is a corridor-wide opportunity for a Seattle
business. Downtown buffer overlap and per-station geography explain most
exceptions and cap how precisely any single station's figures should be
read.

---

## 6. Methodology and limitations

The Methodology & Limitations page covers, in order: Method, Data Sources
(with attribution and terms), What Was Filtered Out, Citations, AI Use, and
these limitations:

- **What "commercial space" means here.** Establishment counts, not floor
  area: an office tower and a food cart each count once.
- **Geocoding failures aren't random.** The 57 dropped businesses likely
  skew toward hard-to-place addresses.
- **Survival can't be measured.** The export lists active licenses only,
  with no closed businesses and no expiration column.
- **Self-imposed privacy restrictions.** See section 9.
- **Ridership as a foot-traffic proxy.** Boardings don't record trip
  purpose; the dashboard figures are transcribed by hand.
- **Temporal misalignment.** Business data from September 2026, ridership
  from calendar 2025.
- **Spatial interpretation.** Downtown buffer overlap double-counts
  businesses; the chain definition had to exclude it (section 11).
- **Empty rings.** Counted as zero, with the corrected figures shown.
- **Duplicate licenses.** One storefront holding several licenses counts
  more than once in the density figures (about 2% of business-ring
  matches). Fixed for chains, open for density.
- **Inference.** Sixteen stations is a small sample, rings within a station
  aren't independent, there is no non-transit control corridor, and every
  finding is an association, not a cause.

---

## 7. The website

Built with Streamlit, deployed on Streamlit Community Cloud. Dark "Warm
charcoal" theme (`#171412` background, orange accents), with Inter for
prose and the default font kept for chart text.

| Page | What it holds |
|---|---|
| **Overview & Introduction** | Three-column overview (what it provides, workflow, key takeaways); Introduction; headline metrics; **What I Asked** (the larger question and the three hypotheses); **What I Found** (headline numbers); Why Seattle?; Starting Assumptions |
| **Heatmap** | The interactive map (section 8) |
| **Findings & EDA** | Three analysis sections, each opening with a Hypothesis block and closing with a verdict-first Result block; Graphs 1 to 5, Tables 1 to 5, per-station notes, In Summary |
| **Methodology & Limitations** | Section 6 |
| **Flowchart** | A Mermaid diagram of how the pipeline was built, including two real pivot points |
| **About** | Background, education, what I'm looking for, why this project, skills demonstrated |

**Charts** are Altair: bar charts in a four-step orange ring palette
matching Schematic 1, a per-station line graph with against-pattern
stations in red, a scatter with trendline, a stacked dot plot, and chain
share by ring. Graph 5's caption is computed from the data, so it can't go
stale.

**Layout values that are measured, not guessed** (each has a re-measure
warning in the code):
- The heatmap embed is a fixed 1000 x 650 px, which works around a
  Leaflet.heat initialization race that crashed the map at percentage sizes.
- The flowchart frame is 925 px: the diagram is 886.8 px at 0.6 scale, plus
  padding and border, for 913 px. Its contents can't be measured from the
  page, so it is re-measured by temporarily adding a reporting line.
- Graph 4 reserves 12 px of left padding so the "Businesses" axis label
  isn't clipped.

---

## 8. The heatmap in detail

- **Basemap:** OpenStreetMap tiles. CartoDB Positron (the original plan) had
  shut down, and Esri's license terms were unstable.
- **Density layer:** Leaflet.heat with a single-hue orange gradient
  (`#FBB878` → `#F97316` → `#DE6412` → `#C0570F` → `#8F3A05`), radius 8,
  blur 10, minimum opacity 0.35. Single-hue because the default
  blue-to-red ramp made low density read as "cold". The low end is a step
  more saturated because Leaflet.heat fades opacity with density, which made
  the palest stop invisible on light tiles. Two versions: businesses within
  station range (default) and all Seattle businesses.
- **Business pins:** colored by category (Retail `#2a78d6`, Food service
  `#C2185B`, Personal services `#1baf7a`), clustered when zoomed out, with
  toggleable sub-layers for the top NAICS codes in each group. Food service
  was recolored from orange to magenta when the density layer turned orange:
  the old color sat 6° of hue from the ramp, and magenta sits 47° from it.
- **Tooltips:** business name, NAICS code, nearest station, and which
  ring band the business falls in. Names that
  are a sole proprietor's own identity show *Name withheld (sole
  proprietor)* in italics (section 9).
- **Transit layers:** the 1 Line track drawn from its GTFS shape, a "1 Line"
  label, station markers with hover tooltips, and the concentric ring
  boundaries.
- **Light/dark mode:** a two-position switch below the layer control. Dark
  mode is a CSS filter (invert, hue-rotate 180°, then brightness, contrast
  and saturation tuned) on the tiles, plus restyled controls, legend and
  tooltips. The map opens in the visitor's own system theme and follows live
  OS theme changes until the switch is used. Toggling makes zero new tile
  requests.
- **Layer control:** collapsed by default, ordered retail, food service,
  personal services, with sub-categories grouped under each.

---

## 9. Privacy and data ethics

- **The risk.** The registry lists home-based sole proprietors alongside
  storefronts, so a pin could put a person's own name on their house.
- **The test.** A pin's published name is withheld when it matches the
  legal entity name and the entity is a sole proprietorship. That flags
  **41 pins**. Narrowed to residentially zoned addresses and read by hand,
  **7 are genuinely someone's name** (0.17% of the map), 3 of them on
  single-family land.
- **The rule over-reaches on purpose.** All 41 are withheld, because a
  hand-written list of seven would go stale against a newer export without
  saying so. The pin, its location, category and ring all stay, so no
  figure on the site changes.
- **The gate.** `scripts/check_personal_exposure.py` checks the published
  map itself, every pin's coordinates and name (8,240 entries, 0 leaks).
  It must pass before the map is published.
- **Repository privacy.** A personal email address was purged from the
  entire git history, and internal build notes were removed from it.
- **Licensing.** Every source's terms were read and logged (section 3).

---

## 10. Quality control and verification

### Automated checks (`scripts/`)
- **`check_published_numbers.py`.** The same number is typed on several
  pages. This recomputes every cited figure from `outputs/` and confirms
  each copy matches (28 citations across four files), and lists the figures
  it can't verify so they're a known gap rather than a forgotten one.
- **`check_personal_exposure.py`.** The privacy gate (section 9).
- **`check_no_em_dashes.py`.** Enforces the comment style rule.

### Project skills (`.claude/skills/`)
Reusable procedures: `pipeline-drift-check` (re-run the pipeline and diff
against committed outputs, normalizing Folium's random element IDs first),
`business-name-privacy-check`, `safe-rename`, `decisions-entry`,
`new-transit-line` (every file that hardcodes "16 Seattle 1 Line
stations"), and `cleanup-session`.

### Verification practices
- **From-scratch pipeline runs** before deploy and again in cleanup: zero
  drift from the committed outputs.
- **Deploy-only environment test:** a venv installed from `requirements.txt`
  alone renders every page, matching what Streamlit Cloud installs.
- **Headless page tests** with Streamlit's `AppTest` before each commit.
- **Measurement over eyeballing:** colors checked with contrast ratios,
  layout checked in the rendered page, numbers checked against the data.
- **Independent review:** a separate cleanup session audited the code
  line by line and reviewed the Findings prose.
- **Live-site checks** after every push.

---

## 11. Errors found and corrected

Each was caught by checking, not assuming, and each is logged with before
and after figures.

| Error | Wrong | Right | How it was caught |
|---|---|---|---|
| "Chain" defined as present at 2+ stations | 45.7% of locations were "chains" | Required 2+ locations: 8.8% at the time | Hand-checking the top chains: two single-location shops reached four stations through downtown overlap |
| Chains counted license records, not storefronts | 152 brands, 8.5% | 116 brands, 6.7% | Line-by-line code audit: one storefront with three licenses counted as three locations |
| Empty rings dropped from averages | Ring 1 957/sq mi, decline 67.5%, ring 2→3 +7.6% | 837, 62.9%, +0.9% | Cleanup audit: an empty ring is a real zero, not missing data |
| Walkshed density averaged three ring densities | Othello 454 | 230 | Code audit: ring 1 is a fifth of ring 3's area but was weighted equally |
| Double rounding | Ring 4 311, ring 1 957 | 310 (true mean 310.48), 956.49 | Cleanup audit: a value printed to one decimal (310.5) was rounded a second time; step 4 now prints two decimals |
| The ring 3→4 chain "reversal" | Explained as SODO/Stadium effect (8.3% → 8.5%) | No reversal after the recount; a 6.82%/6.77% tie | Recount made the old caption describe data that no longer existed |
| Leaflet.heat crashed the whole map | Blank map at percentage sizes | Fixed pixel dimensions | Opening the saved HTML directly |
| Garbled characters on the Heatmap page | The saved map read without an encoding, so Windows fell back to cp1252 | Read as UTF-8 explicitly | Seen on the rendered page, traced to the file read |
| Flowchart scrollbar | 905 px frame, 913 px content | 925 px | A node gained a line; re-measured |
| Graph 4 label clipped | "Businesses" cut off at x = −5 | 12 px padding | Measured in the rendered page |
| Census cache could misplace coordinates | Batches reused by file name only | Each row's id and address must match | Code audit (no current effect) |

Several sentences on the site were also corrected for overclaiming:
"earnings potential" (no earnings data), "significant" (no significance
test), "advantage" (a causal claim), and "nearly as hard as independents"
(it reads backwards; chains lean in harder).

---

## 12. Repository and deployment

- **Two halves sharing a directory.** The pipeline does the geospatial work
  locally; the app reads `outputs/` and nothing else.
- **Lean deploy.** `requirements.txt` holds only streamlit, pandas and
  altair, with upper-bounded pins. Keeping geopandas out avoids the compiled
  GDAL/GEOS/PROJ dependencies that most often break a Streamlit Cloud
  deploy. The geo stack lives in `requirements-pipeline.txt`.
- **`outputs/` is committed** because the deployed app can't regenerate it.
- **Deprecated APIs replaced:** `st.components.v1.html` → `st.iframe`, and
  `use_container_width` → `width="stretch"`, both past their announced
  removal dates.
- **Line endings** normalized to LF by `.gitattributes`, since the deploy
  runs on Linux.
- **Documentation** lives in `docs/`: `DECISIONS.md` (every judgment call,
  dated, append-only), `PLAN.md`, `initialscript.md` (the locked scope),
  `data_sources.md`, the two review documents, `Development Process
  Insights.md`, and this summary.
- **History rewrites** with `git-filter-repo` to purge the email address and
  internal notes, verified afterward. Lesson recorded: stage files by name,
  never with `git add -A`.

---

## 13. Tools and technologies

| Area | Tools |
|---|---|
| Language and environment | Python 3.12 (the system's 3.14 was too new for the geo wheels), `uv`, a single `.venv` holding both requirement sets |
| Data | pandas |
| Geospatial | GeoPandas 1.1.4, Shapely 2.1.2, pyproj 3.8.0; EPSG:4326, EPSG:32610, EPSG:2926 |
| Geocoding and APIs | U.S. Census Bureau batch geocoder via `requests`; City of Seattle open data portal |
| Mapping | Folium 0.20.0, Leaflet, Leaflet.heat, MarkerCluster, OpenStreetMap tiles, custom JavaScript and CSS |
| Charts and diagrams | Altair 6.3.0 (Vega-Lite), Mermaid (loaded from a CDN in an iframe) |
| Web app | Streamlit 1.64.0, Streamlit Community Cloud, Google Fonts (Inter) |
| Testing | `streamlit.testing.v1.AppTest`, custom check scripts, browser-based DOM measurement |
| Version control | git, GitHub, `git-filter-repo` |
| Statistics | Pearson and Spearman correlation, coefficient of variation, z-scores, leave-one-out leverage checks |
| AI-assisted development | Claude Code across several models (most recently Opus 5 and Opus 5.5): project skills, subagents, persistent memory, a separate cleanup session, cross-session messaging, an in-app browser for previews |

---

## 14. Concepts learned

### Geospatial
- **Coordinate reference systems.** Latitude/longitude (EPSG:4326) is in
  degrees, and a degree of longitude shrinks toward the poles, so distance
  can't be measured in it. Projecting to UTM zone 10N (EPSG:32610) gives
  meters; buffers and distances are computed there, then converted back for
  display.
- **Buffers and annuli.** A buffer is the area within a distance of a
  point. Subtracting each ring's inner disc makes rings that don't overlap,
  without which the gradient would double-count.
- **Polygon approximation.** Shapely draws a buffer as a 64-sided polygon,
  0.16% smaller in area than the true circle.
- **Spatial joins.** Assigning points to the polygons they fall inside.
- **Geocoding.** Turning addresses into coordinates, and why a geocoder's
  failures can bias a dataset.
- **Basemaps and tile policies.** Tile providers come and go, and their
  terms matter as much as their look.

### Statistics and analysis
- **Pearson vs Spearman** correlation, and what a high-leverage point does
  to each.
- **Coefficient of variation:** spread relative to the average, which lets
  two variables on different scales be compared.
- **Scale invariance:** dividing every value by the same constant changes
  no correlation, rank or CV, which is why the walkshed count and density
  are interchangeable here.
- **Shares vs densities:** a larger area grows both parts of a share
  together, so area alone can't move a share.
- **Sampling noise:** a 0.05-point gap is a tie when the noise is ±0.7.
- **Correlation vs causation,** and stating claims at the strength the data
  supports ("consistent with", "possibly", "loosely supported").
- **HARKing,** and why hypotheses must be the ones set before the data.
- **Defining a metric carefully:** "chain" changed the headline figure more
  than fivefold depending on its definition.

### Engineering and process
- **Pipeline and app separation** as a deploy strategy.
- **Checking a deploy against the environment that actually runs it.**
- **Committing generated outputs** when the runtime can't regenerate them.
- **Git history is public and permanent** until rewritten, and rewriting
  renumbers every later commit.
- **Measured layout values** need re-measure warnings, or they go stale
  silently.
- **One source of truth per number,** with a script that finds every
  stale copy.
- **A decision log** written at the time of each judgment call.

---

## 15. How the project was built

- **Nine planned sessions** (2026-09-06 to 09-17), roughly 14 hours, each
  with a checklist in `docs/PLAN.md`: environment and data, stations,
  cleaning, geocoding, ridership by hand, rings, the map, the write-up, and
  deploy.
- **Polish days** (2026-09-19/20): theme, colors, dark mode, the switch,
  layer control, a site-wide theme decision.
- **An independent verification pass** (2026-09-20) on a new model, which
  found the stale figures, the email in history, the privacy question and
  the licensing gaps.
- **Cleanup sessions** (2026-09-23 and 09-30): empty-ring fix, the numbers
  check, a comment style pass, and a line-by-line code audit.
- **Final writing** (2026-10-01): explicit hypotheses, the chain prose, a
  prose review, and the About page.
- **Working rules that held.** Explain concepts, not just code. Draft prose
  in chat before it touches a file. The Findings analysis is the author's.
  Scope is locked, and additions get flagged rather than built. Commit after
  each step; push only when told. Keep the sister project separate.
- **Authorship.** The questions, original write-ups and every decision are
  the author's. Claude Code wrote and debugged code, built pages, caught
  bugs, and edited writing; some sentences were drafted at the author's
  request and chosen by them, and the commit history records which.

---

## 16. Decided against, and out of scope

**Decided against, with reasons logged:**
- **A site-wide light/dark toggle.** The ring palette runs bold to pale for
  near to far, and the palest ring disappears on white.
- **Assigning each business to its nearest station** to remove overlap. A
  rider can get off at Symphony and shop near Westlake.
- **The GIS layer, or OpenStreetMap, as the business source** (coverage
  bias).
- **A zoning join in the pipeline** (not needed for any analysis).
- **A dynamic, code-based map reconfiguration** and a keyed tile provider.
- **Address parsing with `usaddress`** (geocoding already reached 99.5%).
- **Renaming "density" to "count"** for the ridership walkshed (identical
  results).

**Out of scope, listed on the site as what a fuller version would add:**
- Control corridors (Ballard, Fremont) with no light rail.
- The 2 Line, which needs Bellevue and Redmond license data.
- A before-and-after design around the October 2021 Northgate, Roosevelt
  and U District openings, the closest this data could get to a causal
  claim.
- Continuous distance-decay weighting instead of flat rings.

---

## 17. Open items

- **About page: résumé link and photo** (still being decided).
- **Presentation:** a slide deck plus screen capture of the live heatmap,
  with a 3 to 5 minute narration recorded by the author. Planned for a new
  session.
- **Duplicate licenses in density figures** (about 2%), deferred as a
  documented limitation: fixing it in step 2 forces a fresh geocoding run.
- **`.backups/pre-rewrite-backup.bundle`**, the local backup from before the
  history rewrites, can be deleted once no longer wanted.
- **Basemap availability:** OpenStreetMap's tile policy offers no uptime
  guarantee, so an outage would blank the map's background.

---

## 18. Timeline

| Date | Milestone |
|---|---|
| 2026-09-06 | Session 1: environment, downloads, data inspected, CSV-plus-donor decision |
| 2026-09-13 | Sessions 2 to 7: stations, cleaning, geocoding (99.5%), ridership, rings and the chain-definition fix, the map |
| 2026-09-15 to 17 | Session 8: the write-up, page renames, contractor exclusion |
| 2026-09-17 | Session 9: from-scratch run, public repo, deployed |
| 2026-09-19/20 | Visual polish, dark mode, verification pass, privacy check, licensing, history purge, docs to `docs/` |
| 2026-09-21 | Flowchart and Graph 4 embed fixes |
| 2026-09-23 | Cleanup: empty rings, numbers check, privacy gate, drift check |
| 2026-09-30 | Comment style pass; code audit: chain recount (152 → 116) |
| 2026-10-01 | Hypotheses, chain prose, Findings review, What I Asked, About page; final version |
