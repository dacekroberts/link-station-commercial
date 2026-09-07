# Working plan

Nine sessions, roughly 14 hours. Ordered so that anything capable of killing
the project surfaces in the first three hours, while it's still cheap to
change course.

Two rules that make the rest work:

- **Commit after every green step.** Each script writes a CSV checkpoint. A
  commit turns that checkpoint into something you can return to.
- **Log every judgment call in `DECISIONS.md` as you make it.** The
  methodology page needs these, and you will not remember them on Thursday.

---

## Session 1 — Environment and data (1.5 h)

The goal is to hit every failure mode while they're cheap.

- [ ] `python -m venv .venv && source .venv/bin/activate`
- [ ] `pip install -r requirements-pipeline.txt`
- [ ] `python -c "import geopandas; print(geopandas.__version__)"`
- [ ] If that fails: `conda install -c conda-forge geopandas folium`
- [ ] `streamlit run app.py` — confirm all four pages load with empty states
- [ ] `git init && git add -A && git commit -m "scaffold"`
- [ ] Download all three datasets per `data/raw/README.md`
- [ ] Open `business_licenses.csv` and answer three questions:
      exact column names? status/expiration column? employee count column?
- [ ] Record the answers and your download date in `DECISIONS.md`
- [ ] Set `LICENSE_SNAPSHOT` in `config.py`

**Gate:** if geopandas won't install after 45 minutes, switch to conda and
move on. Do not debug a build toolchain — it is not what this project is
teaching you.

---

## Session 2 — Station coordinates (1.5 h)

- [ ] `python src/step1_stations.py` — it prints `routes.txt` and stops
- [ ] Update `ROUTE_NAME_PATTERN` to match what you actually see
- [ ] Re-run; confirm roughly 16 Seattle stations
- [ ] Check whether NE 130th / Pinehurst is in the feed. If it's open, add it
      to `SEATTLE_1LINE_STATIONS` and note the partial-window caveat
- [ ] Eyeball two or three coordinates against a map
- [ ] Commit

**Bail at 60 minutes.** Hand-build `data/processed/stations.csv` with columns
`station,latitude,longitude`. Sixteen rows. Note it in `DECISIONS.md` and
move on — this is completely defensible and costs you nothing analytically.

---

## Session 3 — Clean the business data (2 h)

- [ ] Fill in `COLUMN_MAP` in `src/step2_clean_businesses.py`
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

## Session 4 — Geocode (1.5 h)

- [ ] `python src/step3_geocode.py`
- [ ] Note the match rate. Write it in `DECISIONS.md`
- [ ] If below 80%: add `usaddress` parsing to `normalize_address` in step 2,
      re-run both steps (geocoding batches are cached, so re-runs are cheap)
- [ ] Spot-check five geocoded points against a map
- [ ] Commit

**Bail:** accept anything at 75% or above and document it. Chasing the last
few percent is a poor use of your remaining hours, and an honestly reported
match rate is worth more than a slightly higher unreported one.

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
