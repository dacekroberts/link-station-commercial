# Working plan

Nine sessions, roughly 14 hours. Ordered so that anything capable of killing
the project surfaces in the first three hours, while it's still cheap to
change course.

**Progress:** Session 1 complete (2026-09-06). Deviations from this plan are
tracked in `DECISIONS.md` under "Changes" — notably Python 3.12/`uv` instead
of 3.11/conda, the CSV-spine + GIS-geometry-donor split for business licenses,
and `COLUMN_MAP` filled early.

Two rules that make the rest work:

- **Commit after every green step.** Each script writes a CSV checkpoint. A
  commit turns that checkpoint into something you can return to.
- **Log every judgment call in `DECISIONS.md` as you make it.** The
  methodology page needs these, and you will not remember them on Thursday.

---

## Session 1 — Environment and data (1.5 h) — DONE 2026-09-06

The goal is to hit every failure mode while they're cheap.

- [x] venv — `uv venv --python 3.12` (system Python 3.14 lacks geo wheels)
- [x] `uv pip install -r requirements-pipeline.txt` (+ `requirements.txt`)
- [x] `geopandas.__version__` → 1.1.4; reprojection 4326→32610 verified
- [x] conda not needed
- [x] `streamlit run app.py` — all four pages render empty states, no errors
- [x] `git init` + commits (identity `tykwondo`, repo-local)
- [x] Downloads in `data/raw/`: GTFS, license CSV, GIS donor geojson, ST GIS
      shapefiles
- [x] CSV inspected: columns confirmed; **no** status/expiration column
      (active-only → tenure not survival); **no** employee count
- [x] Answers + download date recorded in `DECISIONS.md`
- [x] `LICENSE_SNAPSHOT = "2026-09-06"` in `config.py`
- [x] `COLUMN_MAP` filled (pulled forward from Session 3)
- [x] Business-license source decided: CSV spine + GIS geometry donor

**Gate:** if geopandas won't install after 45 minutes, switch to conda and
move on. Do not debug a build toolchain — it is not what this project is
teaching you.

---

## Session 2 — Station coordinates (1.5 h) — DONE 2026-09-13

- [x] `python src/step1_stations.py` — printed `routes.txt` and stops
- [x] Fixed route matching to exact `route_short_name == "1 Line"` — the
      substring match had also pulled in the shuttle bus-bridge route
- [x] Re-ran; **16 of 16** Seattle stations, zero unmatched warnings
- [x] NE 130th / Pinehurst checked — **not in this feed**, not added
- [x] Eyeballed three coordinates (Northgate, Westlake, Rainier Beach) against
      known locations
- [x] Commit

Took well under budget once the route filter was fixed — see `DECISIONS.md`.

**Bail at 60 minutes.** Fallback ladder: (1) pull points from
`LINKStations.shp` in `data/raw/st_gis_shapefiles.zip` (authoritative Sound
Transit layer, no route matching); (2) hand-build
`data/processed/stations.csv` with columns `station,latitude,longitude`,
sixteen rows. Note which in `DECISIONS.md` and move on — both are completely
defensible and cost you nothing analytically.

---

## Session 3 — Clean the business data (2 h)

- [x] Fill in `COLUMN_MAP` in `src/step2_clean_businesses.py` (done Session 1)
- [ ] Wire the deferred step-2 work: filter to `City == "SEATTLE"` (~30% of
      rows are out-of-city), carry `City Account Number` + `License Start
      Date`, dedupe on account number not UBI (UBI is 8% blank)
- [ ] `python src/step2_clean_businesses.py`
- [ ] Read the drop counts at each filter stage. A stage that drops 90% of
      rows is a bug, not a filter — investigate before continuing
- [ ] Sample 20 surviving rows by hand. Do they read like storefronts, or are
      you looking at consultants at home addresses?
- [ ] Adjust `NAICS_STOREFRONT_PREFIXES` if the sample says so, and record
      both the final list and your reasoning in `DECISIONS.md`
- [ ] Commit

This filter is the most consequential choice in the project. Everything
downstream inherits it. Spend the time here rather than regretting it later.

---

## Session 4 — Geocode (1.5 h, likely less)

- [ ] Wire the donor join in step 3: left-join geometry from
      `business_licenses_geocoded.geojson` on `City Account Number`
      (reproject `EPSG:2926` → `EPSG:32610`), send only the unmatched
      remainder to the Census geocoder
- [ ] `python src/step3_geocode.py`
- [ ] Note **both** figures in `DECISIONS.md`: donor-join coverage (~90%
      expected) and Census match rate on the remainder
- [ ] If the remainder's Census rate is poor: add `usaddress` parsing to
      `normalize_address` in step 2, re-run (batches are cached)
- [ ] Spot-check five points from each source against a map
- [ ] Commit

**Bail:** the donor join alone should clear ~90% with authoritative City
coordinates, so overall coverage is not the risk it was. Accept the Census
remainder at whatever it lands and document it — an honestly reported rate
beats a higher unreported one.

---

## Session 5 — Ridership by hand (0.5 h)

- [ ] Open the Sound Transit dashboard, filter to Link / 1 Line / one month
- [ ] Try the three-dot menu → Export data. If absent, type the numbers
- [ ] Save as `data/raw/ridership_by_station.csv` with columns
      `station,avg_weekday_boardings`
- [ ] **Match station names to `data/processed/stations.csv` exactly** — this
      is the single most common silent failure in the pipeline
- [ ] Record the month, any filters, and the access date in `DECISIONS.md`
- [ ] Set `RIDERSHIP_SNAPSHOT` in `config.py`
- [ ] Commit

---

## Session 6 — Rings, and your first real numbers (2 h)

The moment of truth. Everything before this was plumbing.

- [ ] `python src/step4_rings.py`
- [ ] Resolve any unmatched-station warnings before reading results
- [ ] Look at the mean gradient. Is it monotonic? How steep?
- [ ] Look at the per-station table. Which stations break the pattern?
- [ ] Check Rainier Beach, SODO, and Stadium specifically — you have
      independent explanations for all three
- [ ] Check the chain output: do brand names normalize correctly? Verify a
      handful by hand
- [ ] Write your three main observations into `DECISIONS.md` while fresh
- [ ] Commit

**If the gradient is flat**, that is a finding, not a failure. Businesses
cluster in commercial corridors that stations were routed through, and
distance from the platform within a third of a mile may not be the thing
that varies. Write that up honestly — a null result you explain well reads
better than a weak positive you oversell.

---

## Session 7 — The map (1.5 h)

- [ ] `python src/step5_map.py`
- [ ] Open `outputs/heatmap.html` directly in a browser
- [ ] Tune `radius` and `blur` until the pattern is legible. Do not chase
      beauty — this is illustration, and the ring stats carry your claims
- [ ] Confirm it embeds correctly on the Heatmap page
- [ ] Commit, **including `outputs/`** — the deployed app cannot regenerate it

---

## Session 8 — Write it up (2.5 h)

The highest-value hours in the project. Protect them.

- [ ] Fill the three `TODO` blocks in `pages/2_Findings.py`
- [ ] Fill `[FILL IN]` and `[Confirm which applies]` in `pages/3_Methodology.py`
- [ ] Transfer everything from `DECISIONS.md` into the methodology page
- [ ] Trim the limitations to what's true for your actual run — remove any
      that don't apply, keep access mode, the temporal gap, and siting
- [ ] Rewrite the intro on `app.py` to state what you actually found
- [ ] Commit

Write claims you can defend. "Density declines 40% between the inner and
outer ring" beats "transit drives commercial development," and only one of
them survives a follow-up question.

---

## Session 9 — Deploy (1 h)

- [ ] Push to a public GitHub repo
- [ ] Confirm `outputs/` is committed and `requirements.txt` is the lean one
- [ ] Deploy on Streamlit Community Cloud, pointing at `app.py`
- [ ] Watch the build log. If it fails, it is almost always a dependency that
      leaked into `requirements.txt`
- [ ] Open every page on the deployed URL
- [ ] Add the link to the repo description

---

## If you fall behind

Cut in this order:

1. **Chain analysis** — interesting, not load-bearing
2. **Ridership** — the ring gradient stands alone as a finding
3. **Deployment** — a notebook plus a committed `heatmap.html` still shows well

Never cut the writeup. A clean map with no interpretation is a screenshot.
An honest analysis with a modest finding and a real limitations section is a
portfolio piece.

---

## Out of scope, on purpose

Documented in the methodology as future work rather than attempted:

- Control corridors (Ballard, Fremont)
- The 2 Line — needs Bellevue and Redmond license data
- Before/after around the October 2021 Northgate–U District openings
- Commercial foot-traffic data (Placer.ai, Advan)
