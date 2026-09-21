# Decisions log

Every judgment call, recorded when you make it. The methodology page is
assembled from this file, and reconstructing these choices a week later is
guesswork.

Format: what you chose, why, and what it rules out.

---

## Changes

Macro-level deviations from the original project design, newest first. One line
each; detail lives in the sections below.

### 2026-09-20 — Between sessions

- **Moved the project's documentation into `docs/`.** `DECISIONS.md`,
  `PLAN.md`, `initialscript.md`, `Development Process Insights.md` and
  `Visual Design & Heatmap Review.md` now live there; `README.md` and
  `CLAUDE.md` stay in the root, because GitHub renders the first and Claude
  Code reads the second. The root had seven markdown files competing with
  the code for a reader's attention, which is the wrong first impression for
  a portfolio repo. Moved with `git mv` so each keeps its history as a
  rename rather than a delete-plus-add. No Python reads a `.md` at runtime,
  so the app and the deploy were never at risk; the 21 references that did
  need rewriting are all prose mentions in code comments, `CLAUDE.md`,
  `README.md` and `data/raw/README.md`, plus 28 more in the local-only
  `.claude/` skills.
  **The dated entries in this file and the checked-off items in `PLAN.md`
  were deliberately not rewritten**, per the `safe-rename` skill's rule that
  they are records of what was true when written. That turned out to cost
  nothing: every reference between the moved files is a bare filename, and
  since they all moved together they still resolve. Only references from
  files that stayed behind needed the `docs/` prefix.
- **A file was published to the public repo before anyone had read it, and
  was purged.** A portable privacy-check write-up passed over from the
  sibling multi-city project was sitting in the repo root; a blanket
  `git add -A` swept it into a commit, which was then pushed, before it had
  been opened. Caught roughly twenty minutes later while auditing the root
  directory. Purged from history with a third `git filter-repo` pass and
  force-pushed; kept locally and gitignored, with a copy in `.backups/`.
  The content was harmless — it is the project owner's own working notes —
  but "harmless in hindsight" is not the standard, since nothing about the
  sweep depended on the file being harmless. **The practice that caused it:
  staging with `git add -A` rather than naming paths.** Worth not repeating,
  particularly in a repo that had spent the same day having unreviewed
  internal material removed from it.
- **Recoloured the Food service pins from orange to magenta `#C2185B`.**
  Turning the heat layer orange earlier today left the Food service pins
  and clusters (`#eb6834`, the Cove palette's orange) sitting **6 degrees
  of hue** from the heat ramp, so they sank into the densest areas —
  exactly where food service is most worth reading. Magenta sits 47 degrees
  off the ramp while staying 123 from the retail blue and 177 from the
  personal-services aqua, so it separates from the heat without crowding
  either sibling category, and it lifts the white numeral contrast on a pin
  from 3.2 to 5.9. Compared plum `#8E24AA` and violet `#7C4DFF` against it
  on a side-by-side render of the same downtown view, generated from the
  real pipeline rather than judged from swatches. Violet was ruled out on
  measurement before the render even mattered: 43 degrees from the retail
  blue, and the two do read alike at cluster size. Plum separated best on
  paper; magenta was chosen by eye, keeping the legend warm. Checked on
  both the light and dark base maps. One line in `NAICS_GROUPS` in
  `step5_map.py` — the legend swatch and the cluster icons both read from
  it — plus the regenerated map.
- **Purged `Initial Build Development Context.md` from git history
  entirely**, superseding the entry below that merely stopped tracking it.
  Delisting left the file readable in every commit before today, which
  achieved the tidiness goal but not the removal one. Second
  `git filter-repo` pass of the day, this time `--invert-paths` on that one
  path, then force-pushed. The file is kept locally and gitignored, with
  copies in `.backups/` first, since it is still the fastest way to
  reconstruct the Sessions 1-9 build context. The cost, paid knowingly: a
  second rewrite of every commit hash, so the hashes cited in
  `Visual Design & Heatmap Review.md` were remapped a second time, and
  anyone holding a clone of this repo has to re-clone rather than pull.
- **Migrated off two Streamlit APIs that were already past their announced
  removal dates.** `st.components.v1.html` (removal announced for
  2026-06-01) and `use_container_width` (2025-12-31) were both still in use
  while the site was live, and `requirements.txt` pinned `streamlit>=1.40`
  with no upper bound — Streamlit Cloud re-resolves that file on every
  rebuild, so a future release would have taken the heatmap and flowchart
  pages down with no code change on my part. The heatmap now uses
  `st.iframe(HEATMAP_HTML)`, which takes the `Path` directly and reads it as
  UTF-8, retiring the explicit `encoding=` that Windows needed to stop it
  mangling the em dashes in the layer names. The flowchart builds its HTML
  in Python, so it goes through `st.iframe` as a base64 `data:` URL. I
  tested `st.html`, which takes a string directly and would have been
  simpler, and rejected it: it renders **inline rather than in an iframe**,
  so the document's own `html, body { background }` rule and Mermaid's
  injected styles leak into the Streamlit page. Ten `use_container_width=True`
  on the Findings page became `width="stretch"`. `requirements.txt` now
  carries upper bounds (`streamlit<2`, `pandas<4`, `altair<7`), verified
  against what the deploy actually resolves: pandas 3.0.6, Streamlit 1.64.0,
  altair 6.3.0. Server log went from 14 deprecation warnings to zero.
- **Purged my email address from the whole git history.** `Initial Build
  Development Context.md` carried my personal email in plaintext, in a
  public repo — which defeated the point of the repo-local GitHub noreply
  identity chosen precisely so no personal email would sit in history. It
  was in two commits, not one (`90ae9af` as well as `04e9cc0`). Rewrote all
  190 commits with `git filter-repo --replace-text` and force-pushed.
  Verified the diff between the old remote tip and its rewritten twin is
  exactly that one line, with commit count and both author identities
  intact. The rewrite changed every commit hash from `90ae9af` onward, which
  invalidated the six hashes cited in `Visual Design & Heatmap Review.md`;
  those were remapped from filter-repo's `commit-map`. Chose this over
  simply deleting the line going forward, which would have left the address
  readable in history.
- **Fixed two stale figures a reader of the live site could see.** The
  flowchart diagram said the app has "4 pages" while the reader was standing
  on the fifth, and quoted the chain correction as `45.7% -> 8.5%` — the
  pre-contractor-exclusion number. Recomputed from `chain_stats.csv`:
  **45.5%**, not 45.7%. Also dropped the "4,116" total from the Methodology
  page's overlap paragraph. It was correct for its own computation (unique
  businesses in step 4's spatial join) but disagreed with the Overview's
  **4,120**, which comes from step 5's distance-based count — the gap is
  four businesses sitting 965.399 m from their nearest station, 20.7 cm
  inside the true 0.6-mile circle but outside the 64-sided polygon
  `shapely.buffer()` actually draws. The `1,767 (42.9%)` the sentence exists
  to report is unchanged.
- **Verified the project from scratch against a deploy-only environment.**
  Re-ran all five pipeline steps: the five `outputs/*.csv` came back
  byte-identical, and `heatmap.html` matched after normalising Folium's
  random element IDs. Confirmed the app reads only `outputs/` by deleting
  `data/` entirely and loading all five pages in a venv installed from
  `requirements.txt` alone — zero errors, which rules out a repeat of the
  Session 9 `FileNotFoundError`. Re-derived every headline figure from the
  committed CSVs: ring densities 957/550/592/311 and the 67.5% fall,
  r = 0.684, the 1.8x variance ratio (1.757), 152 chain brands at 8.5%, and
  16/16 station names matching across every file.
- **The map now opens on the visitor's own light/dark setting** rather than
  always light, and follows later OS changes until they work the switch
  themselves, at which point their choice wins until reload. Nothing is
  stored. I verified both initial directions and that a manual choice
  survives a system flip; live mid-session following is **not** verified,
  because the browser's media emulation updates `matchMedia().matches`
  without dispatching a `change` event inside the iframe, and a known-good
  probe listener saw none either.
- **Confirmed a site-wide light/dark toggle is possible, and deferred it.**
  Adding `[theme.light]` and `[theme.dark]` blocks to
  `.streamlit/config.toml` does bring Streamlit's System/Light/Dark control
  back, and the choice follows in-app navigation — so the earlier "an
  explicit theme removes the toggle permanently" is only true of a single
  `[theme]` block. Not adopting it, because light mode breaks three colours
  hardcoded outside the theme: the sidebar "Pages" label renders at
  **1.01:1** contrast (invisible), the flowchart's Mermaid iframe stays a
  dark box on a white page, and the social icons fall to **2.77:1**. With
  the ring-ramp retune already known about, that is four pieces of work, not
  a config flip. Experiment reverted; `config.toml` is byte-identical.
- **Stopped tracking `Initial Build Development Context.md`.** A
  session-by-session build log is working material rather than part of a
  portfolio deliverable, and this repo is public and read by hiring
  managers. Kept locally and gitignored; it remains reachable in history
  before today, which I'd purge too if it should be gone entirely rather
  than just delisted.
- **Added a Dark Mode option to the heatmap.** The layer control now has
  two base maps, "Light Mode" (default) and "Dark Mode", replacing the old
  single "Seattle 1 Line Business Density Heatmap" label. Dark Mode is the
  same OpenStreetMap tiles recoloured with a CSS filter (invert +
  hue-rotate) on that layer's tile container, so there is no new tile
  provider or API key (CartoDB and other dark styles were already ruled out
  on licensing/keys). A `baselayerchange` handler puts a `dark-base` class on
  `<body>`; CSS under that class lightens the ring outlines (the slate
  `#2c3e50` was invisible on dark) and restyles the legend, zoom buttons,
  layer control, attribution and pin hover tooltip in the site's warm
  charcoal palette. Overlays (heat, rings, pins) sit outside the filtered
  pane, so they are unchanged. Not persisted: visitors start on Light.
  The Heatmap page's underlined sentence now names Dark Mode.
- **Light/dark control moved out of the layer control into its own
  switch.** Both tile layers are now `control=False`, so the layer control
  lists only overlays; a custom Leaflet control (a `MacroElement`) sits
  top-left directly under the layer icon and swaps the tile layers itself,
  toggling the `dark-base` class on `<body>`. Top-left, not the top-right
  first asked for, because the map is a fixed 1000px wide and a top-right
  control can sit past the visible edge (same reason the layer control is
  top-left). Drawn as one opaque 30x60 two-position switch (sun over moon)
  with a thumb behind the active mode - top in light, bottom in dark -
  rather than a single icon that changes, after the first version's icon
  looked off-centre and the box looked cut off. The dark border keeps
  Leaflet's own width (only the colour changes) so controls don't shift a
  pixel when the mode changes. The Heatmap page's underlined sentence now
  mentions the button instead of listing Dark Mode among layer-control items.
- **Layer-control order:** the three bold group layers (Retail, Food
  service, Personal services) now sit together, with each group's
  subcategories grouped by umbrella below them. Same layers and defaults.
- **Heatmap density layer changed from red to orange.** `HEAT_GRADIENT`
  in `step5_map.py` now runs `#FBB878` -> `#F97316` -> `#DE6412` ->
  `#C0570F` -> `#8F3A05`, the same family as Schematic 1 and the ring bars.
  First attempt used the exact ring colors (`#FDD0A2` at the low end), but
  Leaflet.heat's opacity follows density, so the palest stop nearly vanished
  on the light OSM tiles. Shifting the ramp one step more saturated (the
  "B: fading outward" sample) keeps it readable. Known tradeoff: the Food
  service pins/clusters (`#eb6834`) are now close in hue to the heat layer;
  they stay distinguishable by their white outlines and numerals.
- **AI Use sentence now reads "based in HTML & Python and was built in
  tandem with Claude Code."**

- **Switched the site from Streamlit's default dark theme to a "Warm
  charcoal" theme in `.streamlit/config.toml`.** Page `#171412`, sidebar
  and widgets `#221D19`, text `#F3EDE6`, borders `#3A322B`, so the new warm
  ring ramp on the Findings page reads as part of the design instead of
  an orange accent on Streamlit's stock blue-black. Chosen over a cool
  "Midnight slate" mainly because Graph 2's dimmed blue lines and Graph 4's
  blue dots would have blended into a navy background, and over a light
  "Paper" theme because it would have needed the ring palette retuned and
  the dark-only Flowchart and heatmap reworked. `primaryColor` and links
  are the soft peach `#FBB878`, not the vivid orange, on purpose: the strong
  orange stays reserved for the ring bars, and a quiet accent keeps Graph 2's
  red from competing with an orange UI. Hardcoded dark colors outside the
  theme were matched by hand: the sidebar "Pages" label and social icons
  (`components.py`), and the Flowchart iframe, whose Mermaid diagram moved
  from the built-in cool gray-blue "dark" theme to a "base" theme with warm
  variables (brown nodes, orange borders). Graph 2's old hardcoded dark
  legend fill was already gone from the earlier Graph 2 fix.
  Red check, done as planned: the "against the pattern" red `#e45756` was
  kept unchanged after rendering Graph 2, Table 1 and the station write-up
  headers on the new background, where it stays clearly red and distinct
  from the orange ramp (about 5:1 contrast). It now lives in one
  `AGAINST_RED` constant in `pages/2_Findings_&_EDA.py` instead of four
  hardcoded copies, so shifting it toward crimson later is a one-line
  change if it ever looks weak. Setting an explicit theme still removes
  Streamlit's light/dark toggle, so the site remains dark-only.

### 2026-09-19 — Between sessions

- **Recolored Schematic 1, and Graph 1/Graph 5's bars with it, from four
  categorical hues (green/blue/purple/teal) to one warm orange ramp, and
  moved Graph 4's Ridership dots from orange to gold.** The old palette
  read flat, with no sense that density falls off with distance. The new
  ramp goes ring 1 `#C2500A` (burnt orange) to `#F0801F`, `#FBB878`,
  `#FDD0A2` (soft peach) at ring 4, so the bars and rings read as
  bold-to-pale with distance. Two constraints shaped it: red is off limits
  (Graph 2's against-the-pattern lines and Table 1's highlight already use
  it), and orange on the ring/bar colors would have collided with Graph
  4's orange Ridership dots on the same page, so those became gold
  `#F2C94C`. The ramp deliberately never reaches true yellow, so the gold
  stays distinct from ring 3's peach and ring 4's peach-cream. Numerals
  inside the rings are white on ring 1 and dark brown `#3B1505` on rings
  2-4 for contrast.
  Ring 4 was tuned after seeing it on the dark page: the first cream
  (`#FDE3C8`) read as a near-white, the brightest thing on screen, the
  reverse of the usual dark-mode "more is brighter" convention. The
  alternative of fading outer rings toward the background (ring 4 at 3.1:1
  contrast) was previewed and rejected as less faithful to the bold-to-pale
  intent. Darkening ring 4 by 15% was also previewed and rejected, since it
  made rings 3 and 4 equal in lightness and erased the step between them.
  What shipped raises ring 4's saturation 15 points (21% to 36%) instead:
  still lighter than ring 3, about 13:1 against the page (was 15:1), at
  the cost of narrowing the ring 3 to ring 4 lightness gap from about 12
  points to about 7. Any future light theme would need this ramp retuned,
  since ring 4 nearly vanishes on a light background.
- **Graph 2 now fills its container width instead of a fixed 900px, with
  its legend above the plot.** Measured at a 375px phone viewport: the
  fixed 900px chart overflowed a 343px container with nothing to scroll
  it, cutting off Rings 2-4 entirely. The fixed width was a deliberate
  laptop-window choice (wider than the ~810px container-fill size); that
  is traded back, and on a wide desktop the chart now fills the container
  (990px at a 1400px window) with no page-level horizontal scroll. The
  legend moved above the plot, which also removed its hardcoded dark fill
  (a copy of the theme background) and the leftover 90px bottom padding
  from when the axis labels were long and rotated. Full-screen mode was
  not tested.

### 2026-09-17 — Between sessions

- **Ran the full pipeline from scratch (step1 through step5) before Session
  9, to check for drift between committed `outputs/` and what the pipeline
  actually produces today.** Every step ran with zero warnings and matched
  the committed figures exactly: 16/16 stations; 11,466 clean businesses
  (84,390 -> 58,774 -> 14,728 -> 11,478 -> 11,466); geocoding at 99.5%
  overall (90.2% donor, 94.9% of the Census remainder); 6,847 business-ring
  matches with the same gradient (957/550/592/311) and chain figures (152
  brands, 8.5% share, 11.0%/10.1%/8.3%/8.5% by ring); 4,120 of 11,409
  businesses within any ring, matching the Introduction page's own
  citywide-coverage metric. Every regenerated `outputs/*.csv` came back
  byte-for-byte identical to the committed version. `heatmap.html` showed a
  git diff, but only from Folium's random per-render DOM element IDs; after
  normalizing those out, the two files diffed at zero - no real content
  change. Reverted that cosmetic diff rather than committing a no-op.
  **Conclusion: zero drift.** What's committed today is exactly what a
  clean run produces, confirmed rather than assumed before the Session 9
  push.
- **GitHub username changed `tykwondo` -> `dacekroberts`** (same account,
  rename). Updated: repo-local git identity (`user.name`/`user.email` to
  `dacekroberts` / `49654908+dacekroberts@users.noreply.github.com`, same
  numeric account ID); the GitHub icon link in `components.py`; historical
  references in `PLAN.md` and `Sessions 1-7 Context.md`. Since no remote
  had been pushed yet (Session 9 still pending), all 141 existing local
  commits were rewritten via `git filter-branch --env-filter` to the new
  identity as well, rather than leaving old commits under the old name -
  cleanly safe to do since nothing had gone public. Verified after: commit
  count unchanged (141), working tree unaffected, single uniform author/
  committer identity across all history. No content changed, authorship
  only.
- **Renamed `Introduction.py` to `Overview_&_Introduction.py`, and added an
  "Overview" section at the top of that page.** Same mechanism as the
  earlier `app.py` -> `Introduction.py` and `pages/2_Findings.py` ->
  `pages/2_Findings_&_EDA.py` renames above: Streamlit derives each
  sidebar label from its filename, so this one change gets the "Overview &
  Introduction" nav label for free. Unlike those two, this file is the
  app's actual entry point (what `streamlit run` targets, and what
  Streamlit Community Cloud's "main file path" setting points at) rather
  than a `pages/` file, so the user deleted and recreated the Streamlit
  Cloud app after this pushed, rather than trying to edit that setting in
  place - Cloud's own UI only offers it at creation time. Updated
  everywhere the old filename was live documentation: `CLAUDE.md`'s and
  `README.md`'s run commands, `README.md`'s file tree and pipeline/app
  split line, `.devcontainer/devcontainer.json` (`openFiles` and the
  `postAttachCommand`), and `.claude/launch.json`. Left `PLAN.md`'s two
  already-checked-off items and `Sessions 1-7 Context.md` alone, same as
  the earlier renames - those reference the filename that was true when
  each was written. The new "Overview" section itself is three short
  bullet-point columns (what the analysis provides, the project workflow,
  key takeaways) rather than prose, aimed at a visitor who hasn't yet hit
  the denser writing below it; drafted and refined with the user before
  any file was touched, per their standing instruction for this kind of
  content change.

### 2026-09-15 — Session 8

- **Excluded three corporate food-service contractors (Compass One, Bon
  Appetit Management, Flik International) from chain analysis only, not
  density.** User caught Compass One's 11-location count as suspicious
  while reviewing the chains table; verified it wasn't the downtown-
  overlap bug (location_count is structurally correct) but a different
  issue - each is a national contract caterer operating cafeterias
  inside a single client's office buildings (Compass One's 23 addresses
  cluster in South Lake Union, reading as one Amazon-campus footprint),
  not an independent chain making repeated real-estate decisions.
  NAICS 722310 identifies them but doesn't cleanly filter them (misses
  23 of Compass One's 24 records; the code they mostly use, 722514, would
  also wrongly exclude ~30 genuine small independent cafes). Filtered by
  the three specific brand names instead. Chain headline moves 155 -> 152
  brands, 8.9% -> 8.5% share; ring_stats.csv/station_stats.csv untouched
  (confirmed byte-identical after the re-run). Full reasoning in
  `config.py`'s `CHAIN_ANALYSIS_EXCLUDE_BRANDS` and on the methodology
  page.

- **Renamed `app.py` to `Introduction.py`.** Streamlit's file-based
  multipage nav derives each sidebar label straight from its filename
  (the same mechanism that turns `pages/2_Findings.py` into "Findings"),
  and there's no separate display-name setting under that scheme - only
  `st.navigation()`/`st.Page()` (a bigger structural change, not needed
  here) decouples the two. Renamed instead of migrating, since the ask
  was just the one label. Updated everywhere the old filename was live
  documentation: `CLAUDE.md`'s run command, `.claude/launch.json`,
  `README.md` (file tree and run command), and the two still-open
  `PLAN.md` checklist items that reference it (`app.py`'s intro rewrite,
  the Streamlit Cloud deploy target). Left `Sessions 1-7 Context.md` and
  earlier dated entries in this file alone - those are records of what
  was true when they were written, not living docs.

- **New `outputs/citywide_coverage.csv`, and a metric-definition choice for
  the intro page.** Rewriting "Businesses within 0.3 mi" surfaced that this
  project already had two different, valid ways to count "businesses near a
  Link station" on the books: `ring_stats.csv`'s business-ring MATCH count
  (6,847 - a business inside multiple overlapping downtown stations' buffers
  counts once per station, the convention every existing Findings-page stat
  uses) and step5_map.py's unique nearest-station count (4,120 of 11,409,
  36%, first computed and console-printed in the Session 7 heatmap-filter
  work above), which counts each business once regardless of how many
  stations it's near. Presented both to the user rather than picking
  silently; they chose the deduplicated 4,120/11,409 figure as more
  intuitive for a citywide headline stat, accepting the inconsistency with
  the match-counted convention elsewhere on the site as a deliberate,
  known tradeoff for this one number. That count was previously
  console-only, so `step5_map.py` now also writes it to
  `outputs/citywide_coverage.csv` (`businesses_in_rings`,
  `businesses_citywide`) right where it's already computed, rather than
  duplicating the nearest-station logic into `step4_rings.py`, which
  deliberately keeps that computation separate from its own overlap-aware
  ring analysis (see the `nearest_station_and_ring()` docstring). The
  intro page's metric now reads "Businesses within concentric ring area of
  Link stations: 4,120 / 11,409 (36.1%)".

- **Renamed `pages/2_Findings.py` to `pages/2_Findings_&_EDA.py`, and
  `pages/3_Methodology.py` to `pages/3_Methodology_&_Limitations.py`.**
  Same reasoning and mechanism as the earlier `app.py` -> `Introduction.py`
  rename above: Streamlit's file-based nav takes each sidebar label
  straight from its filename, so the labels became "Findings & EDA" and
  "Methodology & Limitations" for free once the files moved, and each
  page's own `st.title()` was updated to match. Live references updated:
  `CLAUDE.md`'s and `initialscript.md`'s `TODO`-block rule (both point at
  the exact path), `README.md` (file tree and the "read before drawing
  conclusions" line), the two still-open `PLAN.md` checklist items, and
  two code comments (`config.py`'s `NAICS_STOREFRONT_EXCLUDE` note,
  `step1_stations.py`'s platform-offset note) that named the old path.
  Left every mention in this file's own earlier dated entries, `Sessions
  1-7 Context.md`, and `Development Process Insights.md` alone - same
  "historical record, not a living doc" reasoning as before. Verified live:
  both pages load at their new URLs (`/Findings_&_EDA`,
  `/Methodology_&_Limitations`) with no exceptions, `&` and all.

### 2026-09-13 — Session 7

- **Also added this session:** finer per-category pin toggle layers (12,
  reusing the proven pattern rather than a dynamic filter — considered and
  declined as out of proportion this late); the real 1 Line rail alignment
  from GTFS `shapes.txt`, on by default, with a large always-visible label;
  and richer hover tooltips (name, NAICS code, nearest station, ring band).
  Full account in "Map rendering" below.
- **CartoDB Positron (the originally intended basemap) is dead** — now
  requires an API key, silently fails to load. Switched to OpenStreetMap
  tiles, which are busier but have a long, stable free-use track record.
  Tested and rejected an Esri "light gray canvas" alternative that looked
  closer to the original intent: its free legacy endpoint is flagged
  mature/deprecated and non-commercial-only, the same fragility class that
  just broke CartoDB. Not worth trading one ticking time bomb for another.
- **Found and fixed a bug that was silently breaking the entire map, not
  just the basemap.** Leaflet.heat throws `IndexSizeError` on init when the
  map container's size isn't resolved yet — a known, still-open upstream
  issue (github.com/Leaflet/Leaflet.heat/issues/95) — and because it was
  uncaught, every layer added after the heat layer in the generated script
  (rings, stations, layer control) silently never rendered. Fixed by giving
  the map fixed pixel dimensions (1000x650) instead of percentage-based
  sizing, which sidesteps the race. One harmless console line can still
  fire on load; verified (zoom, pan, layer toggling all tested) that it
  doesn't recur or affect behavior.
- Heat layer tuned from the untouched defaults (radius=12/blur=18) to
  radius=8/blur=10/min_opacity=0.35 after a 3-way visual comparison — the
  tighter setting keeps individual neighbourhood clusters distinguishable
  at the default city-wide zoom, where the original defaults blended into
  one wash. A smoother candidate (radius=18/blur=25) was tested and
  rejected outright - it washed the whole corridor into one undifferentiated
  blob.
- **Added, beyond the original plan:** a per-business pin layer, one
  clustered group per NAICS category (Retail 44/45, Food service 722,
  Personal services 812 - the same three groups `NAICS_STOREFRONT_PREFIXES`
  already defines, so no new categorization scheme), with a legend. Off by
  default (detail layer, not the primary view). 11,409 individual markers
  made `FastMarkerCluster` a requirement, not a preference - plain markers
  at that volume would be unreadable and much heavier. Verified: toggling,
  clustering, zoom-driven declustering, and individual popups all tested
  working (a popup correctly named "MCDONALDS" at its real Seattle
  location).
- Verified the embed inside Streamlit (`pages/1_Heatmap.py`), not just the
  standalone file - loads cleanly, the two console 404s present are
  Streamlit's own internal routing artifacts, unrelated to the map.
  **Correction, found later the same day:** "loads cleanly" was true of
  that pass's checks (layers render, no console errors) but missed two
  real defects only visible on closer inspection - see the Post-Session-7
  entry below. A page rendering without errors is not the same bar as
  every visible string and control being correct and reachable.
- **Post-Session-7 fix, same day:** two bugs found testing the embedded
  page more closely - `pages/1_Heatmap.py` read the saved HTML with the
  OS default encoding (cp1252 on Windows) instead of UTF-8, mangling every
  em dash into mojibake in the legend and layer names; and the layer
  control, left at Leaflet's default top-right corner, fell outside
  Streamlit's content area once the sidebar was open (the map's fixed
  1000px width, itself required by the Leaflet.heat fix above, doesn't
  always fit). Fixed by reading the file as UTF-8 explicitly and moving
  the control to top-left, where it's always visible. Full detail in "Map
  rendering" below.
- **Also post-Session-7, same day:** the heat layer and every pin layer
  now only plot businesses that fall inside some station's ring (4,120 of
  11,409) instead of all Seattle businesses citywide - the user's idea,
  and a real consistency fix: the Findings-page analysis already only ever
  counts ring-bounded businesses, so the map showing unbounded citywide
  data was the odd one out. Full detail in "Map rendering" below.

### 2026-09-13 — Session 6

- Ran `step4_rings.py` end to end: 6,847 business-ring matches, 16 of 16
  stations resolved with zero unmatched-name warnings anywhere.
- **Fixed a chain-analysis validity bug found during the plan's required
  hand-check:** `station_count > 1` (the original chain definition) is
  inflated by the same downtown buffer overlap already known for density —
  a single location can touch 4 stations without being a chain. Real cost:
  reported 45.7% of locations as chains instead of the true 8.8%. Fixed in
  `step4_rings.py` and `pages/2_Findings.py` to require `location_count >=
  2`. Written up on the methodology page.
- **Observations written up** (below): the aggregate gradient's non-
  monotonicity was traced to a specific, checkable cause — station spacing
  vs. ring radii (Symphony/Westlake 0.268 mi apart, closer than the ring
  system's own reach) — rather than left as an unexplained bump. Also:
  Northgate and UW both have zero businesses in the entire 0-0.1mi ring,
  worth the same attention as the three stations the plan named; UW is the
  sharpest ridership/density outlier (r = 0.684 overall).

### 2026-09-13 — Session 5

- **Ridership reconfigured from one month to twelve.** All twelve months of
  2025 captured as screenshots, collected in a Google Doc (16 stations x 12
  months, PDF export, read via PyMuPDF since Read's PDF path needed
  `poppler`, not installed), transcribed and averaged into
  `avg_monthly_boardings`. Still fully manual — no automation added, just
  more manual reads. `RIDERSHIP_SNAPSHOT` changed from `"May 2025"` to
  `"Jan-Dec 2025 (average of monthly totals)"`.
- **Weekend-inclusive, not weekday-only — and the "redundant column" claim
  was checked, not assumed, and corrected once checked.** Initially assumed
  the dashboard's "average boardings per day" figure was simply
  `total monthly ÷ days in month`. Checked directly against all 192
  station-months: **false** — it matches neither `total ÷ calendar days`
  nor `total ÷ weekdays` (off by roughly +9% and −22% on average
  respectively), so Sound Transit applies some service-day weighting of its
  own; it is a genuinely separate calculation. However, averaged to one
  figure per station across the year, the two metrics correlate at
  **r = 0.998** across all 16 stations (0.998 excluding Stadium too) — for
  the cross-station comparison this project does, close enough to redundant
  that transcribing both would not have changed anything. Not transcribed,
  on that corrected evidence. (The three files that stated the wrong
  "simple derivation" claim before this check — `data/raw/README.md`,
  `pages/3_Methodology.py` — were fixed in this same session.)
- **Found while transcribing: Stadium's April 2025 is a real, large
  outlier** — 193,465 total boardings vs. 21k-95k every other month
  (roughly 3-9x). Very likely a Mariners early-season/home-opener surge
  (Stadium sits at T-Mobile Park/Lumen Field). Kept in the mean like every
  other month — no station gets special-cased — but it pulls Stadium's
  12-month average up substantially above what a "typical" month looks
  like. Worth checking against the Session 6 findings, alongside Rainier
  Beach and SODO (both already flagged with independent explanations).
- `data/raw/ridership_by_station.csv` written: 16 of 16 station names
  matched `stations.csv` exactly on the first try (zero missing, zero
  extra) — no silent join failure.
- Touched: `config.py` (RIDERSHIP_SNAPSHOT), `data/raw/README.md` (schema +
  reasoning, corrected), `PLAN.md` (Session 5 rewritten), `pages/2_Findings.py`
  (chart label), `pages/3_Methodology.py` (temporal-misalignment reframed for
  a year-average; weekday/weekend paragraph corrected with the real numbers).

### 2026-09-13 — Session 4

- Wired the GIS donor join scoped back in Session 1: `step3_geocode.py` now
  joins geometry by City Account Number first (EPSG:2926 -> EPSG:4326,
  90.2% matched), then sends only the unmatched remainder to the Census
  geocoder (94.9% of that remainder). Overall 99.5% geocoded, no bail-out
  needed. Both figures now live in `config.py` (`GEOCODE_*` constants) and
  render on the methodology page — replaced the `[FILL IN]%` placeholder.
- Also resolved a second stale placeholder found in the same file while
  there: "On survival" `[Confirm which applies.]` — already answered in
  Session 1 (active-only, no status column), just never written back.

### 2026-09-13 — Session 3

- Wired the deferred step-2 work: Seattle filter (84,390 -> 58,774), dedupe on
  City Account Number instead of UBI, carried account number + license start
  date through.
- **New methodology structure:** added a "What was filtered out" section that
  renders directly from a new `NAICS_STOREFRONT_EXCLUDE` dict in `config.py` —
  each individually-excluded NAICS code carries its reasoning in one place, so
  the code and the write-up can't drift apart. First entry: `812930` "Parking
  Lots and Garages" (826 rows) excluded — parking is a planned trip decision,
  not the incidental foot traffic this analysis measures. Second entry:
  `812990` "All Other Personal Services" (2,424 rows) — NAICS's residual
  catch-all, sample-characterized as ~90% non-storefront (home-based sole
  proprietors, professional offices, come-to-you services); its ~10%
  plausible-storefront minority is already substantially covered under other
  dedicated codes. Clean dataset now 11,466 rows (was 13,887 before this
  exclusion, 14,728 before any individual exclusions).
- **Reviewed, not excluded:** `459999` "All Other Miscellaneous Retailers"
  (1,190 rows) — same catch-all shape as `812990`, checked the same way,
  opposite result: ~70% plausible storefronts (niche independent shops
  without their own NAICS code), kept. Methodology page now juxtaposes the
  two catch-alls so "checked and fine" is as visible as "checked and
  dropped."

### 2026-09-13 — Session 2

- **Route matching fixed:** `ROUTE_NAME_PATTERN` substring-matched on
  `route_long_name` too, which pulled in the "1 Line Shuttle Bus" replacement
  service alongside the real train. Now an exact match on `route_short_name`.
  Without this, `stations.csv` would have had 17 rows including 3 bus-stop
  duplicates of SODO.
- **GTFS name aliasing added** for two abbreviated stop names ("Univ of
  Washington", "Int'l Dist/Chinatown") so the station-name join key is
  canonical from step 1 onward, not patched later.
- NE 130th/Pinehurst confirmed **not** in this GTFS snapshot — stays out of
  scope for now, 16 stations as planned.

### 2026-09-06 — Session 1

- **Toolchain:** Python 3.12 via `uv`, not 3.11 via pip/conda. System Python is
  3.14 (no geo-stack wheels); the `py` launcher's 3.11 pointed at a deleted
  install. One venv holds both requirement files locally.
- **Business-license data:** split into a CSV spine (canonical, all analyses)
  plus a GIS layer used only to donate point geometry via an account-number
  join. Rejected the GIS layer as primary — it hides a ~10% coverage gap, the
  same bias problem that got OSM rejected.
- **Correction:** "Seattle's business license dataset stops at the city line"
  is not accurate. The CSV carries ~30% non-Seattle rows (licensed here,
  located elsewhere); step 2 filters to `City == "SEATTLE"`. The scope decision
  (Seattle 1 Line only) is unaffected — we still can't get other cities' full
  business populations from this source.
- **COLUMN_MAP** filled in Session 1 rather than Session 3 (the file was
  already in hand).
- **Station coordinates:** `LINKStations.shp` (Sound Transit GIS, in
  `st_gis_shapefiles.zip`) added as a fallback between GTFS parsing and
  hand-building `stations.csv`.

---

## Environment

**Python 3.12.14**, not 3.11 as the plan assumed.
- Why: system Python is 3.14, too new for compiled wheels of the geo stack
  (geopandas/shapely/pyproj/pyogrio). The `py` launcher listed a 3.11 but it
  pointed at a removed install (`Documents\Noble_Desktop\python.exe`).
- 3.12 (a uv-managed CPython build) has wheels for the entire stack and
  installed clean in under a minute. No conda needed.

**Installer: `uv`**, not pip. Same packages, much faster. `.venv` created with
`uv venv --python <3.12 path>`; deps with `uv pip install`.

**One venv holds both requirement files.** `requirements-pipeline.txt` (geo
stack) and `requirements.txt` (streamlit, pandas) are both installed locally.
The lean/heavy split still does its real job — it governs what Streamlit Cloud
installs — but locally a single environment is simpler.

**Versions installed:** geopandas 1.1.4, folium 0.20.0, shapely 2.1.2,
pyproj 3.8.0, streamlit 1.63.0. Reprojection EPSG:4326 -> EPSG:32610 verified
against a known Seattle point.

**Streamlit app:** all four pages (`app.py` + three `pages/`) render their
empty states with no exceptions (checked via `streamlit.testing`).

---

## Data provenance

**Business licenses**
- Downloaded: 2026-09-06
- Source: City of Seattle Open Data — "Active Business License Tax Certificate",
  dataset `wnbq-64tb` (data.seattle.gov). Daily refresh.
- File: `data/raw/business_licenses.csv`
- Row count as downloaded: 84,390 (58,774 with a Seattle address; the rest are
  businesses licensed with Seattle but located in Kent, Bellevue, Tacoma, etc.
  — filtered out in step 2)
- Columns: Business Legal Name, Trade Name, Ownership Type, NAICS Code, NAICS
  Description, License Start Date, Street Address, City, State, Zip, Business
  Phone, City Account Number, UBI
- Status/expiration column present: **no**. This is an active-only snapshot, so
  we can measure **tenure among current licensees** (from License Start Date)
  but **not survival** — closed businesses are absent, not marked. Documented
  limitation.
- Employee count column present: **no**. No business-size proxy available.
- License Start Date: `YYYYMMDD`, 100% parseable, real mass 2018–2026.

**Business license geometry (donor)**
- Downloaded: 2026-09-06
- Source: "Seattle Business License" GIS layer (SeattleCityGIS / ArcGIS Hub;
  catalog stub `wmtg-dzy4` on data.seattle.gov). 54,443 pre-geocoded points,
  `EPSG:2926` (WA State Plane N, feet).
- File: `data/raw/business_licenses_geocoded.geojson`
- Use: **geometry only**. step 3 left-joins these coordinates onto the CSV by
  City Account Number (~53,015 of ~58,774 Seattle rows match), then Census-
  geocodes the remainder. See "Business license source" below for why it is
  not the primary source.

**Ridership**
- Accessed: 2026-09-13. No filters beyond Link / 1 Line and year = 2025
  (evident from the data itself — twelve rows, Jan-Dec 2025, per station).
- Months shown: **Jan-Dec 2025 (all twelve)**, revised from the original
  single-month plan mid-Session-5 — see "Changes" above and
  `data/raw/README.md`.
- Metric: **total boardings per month**, averaged across the twelve months
  into `avg_monthly_boardings`. Deliberately *not* the standard "average
  weekday boardings" — see reasoning below.
- Obtained by: manual screenshots of the Sound Transit dashboard tables (16
  stations x 12 months), collected into a Google Doc by the user, exported
  as PDF, transcribed from there (PyMuPDF rendering, since the standard PDF
  read path needed `poppler`, not installed on this machine). Still fully
  manual — no Power BI automation — just twelve months of manual reading
  instead of one.
- **Metric decision, checked not assumed:** the dashboard tables also show
  an "average boardings per day" figure per month (also weekend-inclusive).
  First assumed to be `total monthly ÷ days in month` and therefore
  redundant with the total - **checked against all 192 station-months and
  that assumption was wrong**: it matches neither `total ÷ calendar days`
  nor `total ÷ weekdays` (off by roughly +9% and −22% on average
  respectively), so Sound Transit applies some service-day weighting of its
  own. It *is* still a defensible thing to skip, but on different grounds:
  averaged to one figure per station across the year, the two metrics
  correlate at **r = 0.998** across all 16 stations — for the cross-station
  comparison this project does, close enough to redundant that transcribing
  both would not have changed the analysis. Not transcribed, on that
  evidence. Full verification script and its output are reproducible from
  the raw 192-row table (kept in this session's scratch files, not the
  repo).
- Using the weekend-inclusive monthly total instead of a weekday-only figure
  is a deliberate choice, not just convenience: weekday ridership is
  disproportionately commute-driven (passing through, not stopping to shop),
  so it would arguably understate pedestrian exposure to the NAICS-filtered
  storefronts this project counts. Cost: not directly comparable to a
  published "average weekday boardings" figure elsewhere. Written up on the
  methodology page under "Ridership as a foot-traffic proxy."
- Averaging twelve months instead of using one (as originally planned)
  smooths seasonality, at the cost of the ridership window possibly spanning
  the Federal Way extension's late-2025 opening internally — also written up
  on the methodology page ("Temporal misalignment").
- **Stadium's April 2025 (193,465 total boardings) is a large, genuine
  outlier** — 3-9x every other month for that station. Very likely a
  Mariners early-season surge (T-Mobile Park/Lumen Field adjacency), not a
  transcription error. Included in the mean like any other month; worth
  checking against the Session 6 ring results.
- Station-name join: **16 of 16 matched `stations.csv` exactly**, zero
  missing, zero extra, on the first attempt.

**GTFS**
- Downloaded: 2026-09-06 (feed dated 2026-08-28 internally)
- Route pattern matched: `route_short_name == "1 Line"` (exact), route_id
  `100479`. Originally substring-matched on both short and long name, which
  also pulled in `1-SHUTTLE` ("1 Line Shuttle Bus" — a bus-bridge replacement
  service) because its route_long_name contains "1 Line" too; that produced 3
  bogus "SODO Busway" bus-stop rows instead of the one real SODO station.
  Fixed to exact match on route_short_name only.
- Two GTFS stop names are abbreviated and were mapped to the canonical names
  used everywhere else: `"Univ of Washington"` -> `"University of
  Washington"`, `"Int'l Dist/Chinatown"` -> `"International
  District/Chinatown"` (`GTFS_NAME_ALIASES` in step 1).
- Stations resolved: 16 of 16, zero unmatched warnings, coordinates spot-
  checked against three known locations (Northgate, Westlake, Rainier Beach)
  and confirmed by the user against a real map for all sixteen.
- Platform-averaging offset measured: 14 m (Capitol Hill) to 72 m (Columbia
  City), mean 48 m from each platform to the averaged station point. Not
  negligible against the innermost 0.1 mi ring (161 m wide). Written up in
  `pages/3_Methodology.py` under "Spatial interpretation".
- NE 130th / Pinehurst included: **no**. Not present anywhere in this feed's
  52 1-Line stops (all cities) — not running as of this snapshot.
- Hand-built instead of joined: no — GTFS join worked once the route filter
  was fixed. Session 2 took well under the 60-minute budget.

---

## Analyst choices

**Business license source: CSV spine + GIS geometry donor**
- Chose: the "Active Business License Tax Certificate" CSV as the canonical
  source for every analysis; the "Seattle Business License" GIS layer used only
  to donate point coordinates (joined on City Account Number).
- Rejected: using the GIS layer as the primary source. It is a strict subset of
  the CSV — it contains only the ~90% of Seattle businesses the City's geocoder
  successfully placed, and silently omits ~5,700 Seattle businesses with no way
  to characterise what is missing. That is the same coverage-bias problem that
  got OpenStreetMap rejected: the gap is not random (new, home-based, informal-
  address businesses) and it correlates with the thing being measured. Starting
  from the CSV and geocoding it ourselves makes every drop visible and
  reportable.
- Rejected: pure CSV with no donor. The account-number join collapses the
  Session 4 geocoding risk — ~53k rows get authoritative City coordinates for
  free, leaving only ~5.7k for the Census geocoder — for no analytical cost.
- Also gained from the CSV: Ownership Type (sole prop / corp / LLC), UBI, split
  address components. Lost vs. GIS: an expiration date (minor — start date
  carries the tenure analysis) and a `BUSINESS_ID` chain link (recoverable via
  the same join if needed).
- Implementation (Session 3/4, not yet wired): step 2 filters to Seattle and
  carries City Account Number + License Start Date; step 3 does the donor join
  before calling Census and reports both match rates.

**NAICS prefixes kept**
- Prefix list unchanged: `44`, `45`, `722`, `812`.
- **Individual exclusion: NAICS `812930` "Parking Lots and Garages" (826
  rows).** Kept by the `812` prefix but excluded on its own. Reasoning
  (also on the methodology page, "What was filtered out" — both read from
  `NAICS_STOREFRONT_EXCLUDE` in `config.py`, one source): paying to park is a
  planned decision made before the trip, not the incidental foot traffic —
  a meal, a purchase — this analysis measures. A commuter who drove and paid
  to park made a different choice than one who walked past a shop from the
  platform; counting both as the same kind of "storefront" would credit
  driving trips to a measure meant to capture walking ones.
- **Individual exclusion: NAICS `812990` "All Other Personal Services"
  (2,424 rows — the single largest category, ~17% of what the prefix filter
  had kept).** This is NAICS's residual catch-all within 812; the
  well-defined personal-service categories (salons, barbers, dry cleaners,
  pet care) already have their own codes and stay in the dataset untouched.
  A hand sample of 40 of the 2,421 category rows: ~10% plausibly walk-in
  storefronts (a dance studio, a massage practice, a dog daycare); the large
  majority were home-based sole proprietors (an individual's name at a
  residential address), professional offices (law/design/consulting/
  investment firms), or services that travel to the customer (hauling,
  pet-sitting, event planning, doula care). Dropped as a category rather
  than triaged row-by-row: no finer NAICS subcode exists to split it, hand-
  reviewing 2,421 rows for ~240 likely storefronts is a poor use of
  remaining hours, and the storefront types in its minority are already
  substantially represented under their own dedicated codes elsewhere — so
  this is a bounded, characterized undercount, not a silent gap.
- **Reviewed and kept: NAICS `459999` "All Other Miscellaneous Retailers"
  (1,190 rows).** Retail's own catch-all, same shape as 812990 above, so
  checked the same way rather than assumed clean. A hand sample of 25 of the
  1,190 rows found the opposite profile: ~70% plausible walk-in storefronts —
  niche independent shops uncommon enough to lack their own NAICS code (a
  violin shop, a comic shop, a record store, a coin shop, a distillery
  tasting room) — against a minority of non-storefront rows (an industrial
  gas supplier, a houseboat-owners' advocacy nonprofit, a couple of
  vague-named LLCs). Kept, unlike 812990: this catch-all's residue is
  dominated by real, if uncommon, retail rather than professional or
  home-based operations. Also on the methodology page, juxtaposed with the
  exclusions — both read from `config.py`
  (`NAICS_STOREFRONT_REVIEWED_KEPT`).
- Effect: NAICS prefix filter 58,774 -> 14,728; parking exclusion
  14,728 -> 13,902; personal-services exclusion 13,902 -> 11,478; final
  clean count after dedup/address validity: **11,466**.

**Ring boundaries**
- Used: 0.1 / 0.2 / 0.3 / 0.6 miles
- Why 0.3 (and 0.6) as the walkshed - three layers, oldest first:
  - **Mechanical reasoning** (recorded in `config.py`'s own comment on
    `RING_EDGES_MILES`): "the 0.3 mile mark is the walkshed of interest;
    0.3-0.6 is the comparison band that gives the gradient something to
    decline against." A conventional ~5-6 minute walk radius, with the
    outer band there specifically as a contrast baseline, not as a second
    walkshed claim of its own.
  - **Conceptual reasoning (the user's own, 2026-09-14):** the ring
    system is measuring the feasibility of a *spontaneous* walkable
    detour outward from the platform, not just physical nearness. A
    business in ring 4 may still see real foot traffic from riders
    walking to/from work or home, but that traffic is structurally
    different from ring 1's - it's a commute passing by, not a
    station-driven impulse stop - so the benefit a ring-4 business
    derives specifically *from the station* should be expected to have
    already dropped off relative to ring 1, even if the business is
    still "walkable" in an absolute sense. This part needs no external
    source - it's the analytical logic behind the ring system, not an
    empirical claim.
  - **Sourced, replacing the earlier unverified "~30-minute" recollection
    (resolved 2026-09-14):** the user located Yang, Yong, and Ana V.
    Diez-Roux, "Walking Distance by Trip Purpose and Population
    Subgroups," *American Journal of Preventive Medicine*, vol. 43,
    no. 1, 2012, pp. 11-19 - a real NHTS-based study of U.S. walking-trip
    distance and duration by purpose, with fitted distance-decay
    parameters `P(d > x) = e^(-βx)` per purpose. Read in full, not just
    summarized. Two things checked directly against the paper's own
    numbers (Table 2, Table 3), not assumed:
    1. **The 0.6 mi outer edge, checked against purpose-matched
       one-way distance decay** (β values for "meals" and "shopping,"
       the closest matches to this project's food-service and retail
       categories): `e^(-2.48*0.6) ≈ 0.226` for meals and
       `e^(-2.14*0.6) ≈ 0.277` for shopping - meaning **~77% of one-way
       meal-purpose walking trips and ~72% of one-way shopping-purpose
       trips nationally are 0.6 mi or less.** Recreation, the purpose
       with the longest trips in the paper, is the clear outlier at only
       ~50% within 0.6 mi - the opposite of what this project needed, so
       this isn't a coincidence of picking a lenient category. This is a
       stronger, more directly relevant validation of the 0.6 mi edge
       than either the original recalled statistic or the walking-speed
       arithmetic below it once was: it's purpose-matched, distance-based
       (not time-and-pace-derived), and sourced to fitted empirical
       parameters rather than a recollection.
    2. **The round-trip ~30-minute framing, checked against purpose-
       matched one-way duration decay** (β for duration: meals = 0.1,
       shopping = 0.087): `e^(-0.1*15) ≈ 0.223` and
       `e^(-0.087*15) ≈ 0.271` - meaning **~78% (meals) and ~73%
       (shopping) of one-way commercial-purpose walking trips are 15
       minutes or less**, i.e. fit inside a 30-minute round trip under
       the user's stated assumption that a spontaneous visitor returns to
       the station to reach their real destination. **What this does NOT
       support:** the original framing that people "naturally experience
       events in ~30-minute time frames" as a typical/average duration.
       The paper's actual all-purpose figures are far shorter - mean
       walking duration 14.9 min, median 10 min - so ~30 minutes round
       trip is better described as a threshold most (not average, not
       all) commercial-purpose trips fall under, not a natural rhythm of
       experience. The revised, defensible claim: **a ~30-minute
       round-trip budget covers roughly three-quarters of real one-way
       walking trips for meal- and shopping-purpose destinations**,
       consistent with, not proof of, the project's ring choice.
    - **Caveat carried forward into methodology, matching this project's
      existing pattern of disclosing survey limitations:** NHTS is
      general U.S. population walking behavior, not transit-station-
      specific and not Seattle-specific. Cited as supporting context for
      the ring boundary choice, not as a claim about how people actually
      behave at these sixteen stations.
    - **Editorial call, 2026-09-14: the round-trip/~30-minute point
      (item 2 above) is kept here in full as the record of how the
      reasoning actually developed, but is deliberately NOT carried into
      `pages/3_Methodology.py`.** The user's original "~30-minute
      discretionary event" recollection was the seed that led to finding
      and reading the Yang and Diez-Roux source in the first place - a
      good brainstorming starting point - but once checked, it turned out
      to be the weaker of the two findings (a threshold most trips fall
      under, not a typical duration, and reliant on an extra
      round-trip-behavior assumption the distance check doesn't need).
      The methodology page now leads with, and rests on, only the
      **distance-based validation** (item 1: ~77%/72% of purpose-matched
      one-way trips within 0.6 mi, recreation correctly the outlier) -
      the stronger, more directly relevant claim, not diluted by a
      secondary point that needs more caveats to hold up. Process
      documented here; final write-up simplified there.
    - **Two final small additions from re-reading the sources in full,
      2026-09-14 - the last pass before tabling source mining:**
      1. Yang and Diez-Roux also note that most travel datasets record
         only trip start/end points, not the route walked, and that
         street-network distance is the more accurate but rarely
         available alternative to straight-line distance - the same gap
         this project's own "Spatial interpretation" limitation already
         disclosed independently (I-5, the Montlake Cut, and grade
         separate a straight-line buffer from a true walkshed). Added as
         a second citation strengthening that existing disclosure, not a
         new limitation - this project's own version is more specific to
         Seattle than the source is.
      2. The same study found 65% of U.S. walking trips exceed the
         conventional 0.25-mile planning assumption, arguing against a
         single flat cutoff generally. Added as explicit support for
         using four ring tiers rather than one boundary, not just for the
         0.6 mi outer edge specifically - a design-level point the
         earlier citation only implicitly covered.
      Both written into `pages/3_Methodology.py`'s Method section
      alongside the existing citation.
- Alternatives tested: none. Unlike the heat radius/blur tuning (Session
  7, a real 3-way visual comparison), the ring edges were set once in
  `config.py` before Session 6's analysis ran and never revisited against
  an alternative set.

**Overlapping downtown buffers**
- Chose: allow overlap, disclose in methodology
- Rejected: nearest-station assignment, because it understates how many
  stations genuinely serve a downtown block
- Effect: **1,767 of 4,116 businesses that fall in any ring (42.9%)** are
  claimed by more than one station's ring set. Computed directly from
  `step4_rings.py`'s own spatial join (grouped business `record_id`s by
  distinct `station` count), not estimated - re-run for this entry, not
  carried over from memory. Distinct from the 6,847 business-ring match
  *rows* already on record above, which counts pairs, not unique
  businesses.

**Brand normalization**
- Method: exact match after normalization, with two narrow, targeted
  patches - confirmed directly from `normalize_brand()` in
  `step4_rings.py`: uppercase, drop apostrophes outright (not replace with
  a space), strip store numbers (`#1234`), strip legal suffixes
  (LLC/INC/CORP/etc.), strip remaining punctuation, collapse whitespace,
  then canonicalize known compound-word variants via a small
  `BRAND_ALIASES` lookup (same pattern as `GTFS_NAME_ALIASES` in
  step1_stations.py). The function's own docstring names `rapidfuzz` as a
  possible follow-up for what exact matching still misses, but it was
  never implemented - every brand key in `chain_stats.csv` is an
  exact-match key (plus the two patches), not a fuzzy one.
- Spot-checked: the two brands that originally surfaced the downtown-
  overlap chain bug (PU POWDER, Saigon Drip Kitchen - both real
  single-location businesses, confirmed by hand in Session 6), plus the
  top real chains from the post-fix list, independently confirmed as
  actual checkable Seattle/PNW brands: Subway, Evergreens Salad, Caffe
  Ladro, Westman's Bagels, Metro by T-Mobile, Great State Burger, Just
  Poke, Dough Zone Dumpling House.
- **Known failures, found and patched (post-Session-7, same day):** a
  quick prefix-collision check against `chain_stats.csv` (not an
  exhaustive audit) surfaced two brands split into separate keys that were
  almost certainly the same real chain: **"RUDYS BARBER SHOP" vs. "RUDYS
  BARBERSHOP"** (a compound-word spacing difference the normalizer didn't
  merge) and **"MOLLY MOON S HOMEMADE ICE CREAM" vs. "MOLLY MOONS
  HOMEMADE ICE CREAM"** (inconsistent source-record apostrophe use
  colliding with the regex's punctuation-to-space rule). Confirmed as the
  user's call to fix rather than just document, since the analysis should
  reflect the real chain, not an artifact of how two different licenses
  happened to be typed. Fixed generally, not by hardcoding these two
  brands: apostrophes are now dropped outright (catches the Molly Moon's case
  and any other apostrophe-inconsistent brand in the dataset, not just
  this one). Checked precisely, not left as a guess: across the full
  11,409-business dataset, 11 distinct brand-name pairs now merge that
  didn't before, including MCDONALD'S/MCDONALDS and several others never
  spot-checked by hand (Baker's, Corry's Fine Drycleaning, Ezell's Famous
  Chicken, Frankie Jo's, Murphy's Pub, Scooter's Burgers). Of those 11,
  only 4 have *both* spelling variants inside a station's ring - Molly
  Moon's, Poquito's, Rudy's Barbershop, and Sam's Tavern - which is
  exactly why the in-ring `chain_stats.csv` brand count dropped by 4
  (3,907 -> 3,903), not 11 or 2; the other 7 pairs are real merges
  citywide but don't affect any figure this project actually reports. The
  compound-word spacing case went into
  `BRAND_ALIASES`, a small explicit lookup rather than a general
  space-stripping rule, since merging all spacing variants automatically
  risks conflating genuinely unrelated brands. **Re-ran step 4 after the
  patch; verified both brands now collapse to one row each**
  (`RUDYS BARBERSHOP`: 5 locations/4 stations; `MOLLY MOONS HOMEMADE ICE
  CREAM`: 3 locations/5 stations - both checked directly against
  `chain_stats.csv`, not assumed from the fix alone). Headline figures
  shifted accordingly: **153 -> 155 brands with 2+ locations, 8.8% -> 8.9%
  chain share of all matched locations.** A small, expected move in the
  more-accurate direction, not a correction of the earlier ~5x bug (that
  fix and this one are unrelated - see "Things that went wrong" above).
  Everything else the collision check surfaced (the various
  "SEATTLE ___" / "PIKE PLACE ___" groups) was unrelated businesses
  sharing a common word, not a normalization miss - left alone.
  **Residual limitation, disclosed on the methodology page:** exact-match
  normalization (even patched) still cannot catch every same-chain
  variant a human would recognize - genuinely different spellings,
  abbreviations, or naming conventions across separately filed licenses
  will still split into different brand keys unless individually found
  and added to `BRAND_ALIASES`. The chain-share figures are a lower
  bound on the true chain share, not an exact count.

---

## Quality metrics

- **Geocoding (Session 4, 2026-09-13), two passes:**
  - GIS donor join (City Account Number against
    `business_licenses_geocoded.geojson`, EPSG:2926 -> EPSG:4326): **90.2%**
    (10,345 of 11,466). 1,405 duplicate donor account numbers dropped first
    (exact-coordinate repeats, not distinct locations).
  - Census bulk geocoder, on the 1,121-row remainder only: **94.9%**
    (1,064 of 1,121). Well above the 80% comfort line and the 75% bail-out —
    no `usaddress` parsing needed.
  - **Overall: 99.5%** (11,409 of 11,466). 57 businesses (0.5%) failed both
    passes and are dropped from the geocoded set.
  - Spot-checked 5 points from each source (donor and Census) against
    Google Maps — both look right for their stated address/neighborhood.
  - `geocode_source` column carried into `businesses_geocoded.csv` so the
    two populations stay distinguishable downstream if needed.
- Points dropped by King County bounding-box sanity check: 0 (from either
  source).
- Businesses in final geocoded dataset: **11,409** (of 11,466 cleaned, of
  84,390 originally loaded).
- Stations with no ridership match: **none** — 16 of 16 matched exactly.
- **Rings (Session 6, 2026-09-13):** 6,847 business-ring matches from 11,409
  geocoded businesses across 16 stations x 4 rings. No unmatched-station
  warnings anywhere in the run (stations.csv, businesses_geocoded.csv, and
  ridership_by_station.csv all agree on names).
- **Share of businesses actually near a station (post-Session-7, same
  day):** of the 11,409 geocoded businesses citywide, only **4,120 (36%)**
  fall within any station's ring at all (nearest station within 0.6 mi);
  the other 7,289 (64%) are more than 0.6 mi from every station. Distinct
  from the 6,847 business-ring matches above, which counts business x ring
  pairs (a downtown business can match more than one station); this is
  unique businesses. **Candidate headline stat for the Session 8 write-up**
  — flagged by the user as worth emphasizing, not written up here per the
  project's own rule that this analysis is the user's to interpret.
- **Chain analysis validity bug, caught and fixed (Session 6):** the chain
  metric's `station_count` can be inflated by the same downtown buffer
  overlap already disclosed for density — one physical location inside the
  4-station overlap zone can register as "present at 4 stations" without
  being a chain at all. Verified by hand (the plan's required step):
  PU POWDER and Saigon Drip Kitchen, each with exactly one real location,
  both initially showed up in the "top chains" table. Checked systematically:
  **1,589 of 3,907 normalized brands (41%)** touch >1 station from a single
  location. The bug's real cost: defining "chain" as `station_count > 1`
  (the first version) reported **45.7%** of locations as chains;
  requiring `location_count >= 2` — the only definition consistent with
  what "chain" means — puts the true figure at **8.8%**, a >5x difference.
  Fixed in `src/step4_rings.py` (chain_stats now sorted so real chains float
  to the top; console output explicitly separates "touches >1 station from
  1 location" from genuine multi-location chains) and
  `pages/2_Findings.py` (the `multi = chains[...]` filter now reads
  `location_count > 1`, not `station_count > 1`). Written up on the
  methodology page under "Spatial interpretation," next to the density
  overlap disclosure it's the sibling of.
  **Updated again, post-Session-7 same day:** a separate brand-
  normalization patch (see "Analyst choices" > Brand normalization above)
  moved these numbers to 3,903 brands and 8.9% chain share. The figures in
  this entry (3,907 / 8.8%) are the Session-6 snapshot, not the current
  one - kept as-is here since they're describing what that specific fix
  found and changed at the time, not a live number.

---

## Map rendering (Session 7, 2026-09-13)

Consolidated from several separate decisions made across the session - the
"Changes" entry above has the compact version; this is the full account.

**Basemap: CartoDB Positron replaced with OpenStreetMap**
- The original design specified `tiles="CartoDB positron"` - a muted,
  minimal basemap chosen deliberately so the heat layer would read clearly
  against it.
- Found broken, not assumed: CartoDB now requires an API key. The preset
  silently fails - confirmed both by a console warning and visually (tiles
  rendered as a tiled "API KEY REQUIRED" watermark instead of a map).
- Considered Esri's free legacy "World Light Gray Base" as a closer visual
  match to the original intent - tested it, and it did look closer. Then
  checked its terms rather than trusting "free": flagged mature/deprecated
  status, a paid/key-gated migration Esri has been urging since 2022, and
  non-commercial-use-only terms. Rejected - the same fragility class that
  just broke CartoDB, not worth trading one ticking time bomb for another
  in a deliverable meant to keep working unattended.
- Landed on OpenStreetMap: busier and more colorful than the original
  design intent, but free/open with a long, stable track record, and the
  standard safe default nearly every mapping library assumes. The heat
  layer still resolves clearly against it - verified at both the default
  city-wide zoom and zoomed into downtown.

**A real bug that was silently breaking the entire map, not just the basemap**
- `HeatMap` (Folium's wrapper around the Leaflet.heat plugin) throws
  `Uncaught IndexSizeError: Failed to execute 'getImageData' ... source
  width is 0` on load. This is a known, still-open upstream bug
  (github.com/Leaflet/Leaflet.heat/issues/95): the plugin reads the map's
  pixel size before the browser finishes resolving a percentage-based
  (100%/100%) container, and `getImageData` throws when that read comes
  back zero.
- Because the exception was uncaught, it silently aborted the rest of the
  generated script - the ring-boundary circles, station markers, and the
  layer control never rendered at all, not just the heat layer. Confirmed
  directly: `map.eachLayer()` showed only 2 layers present (the tile layer
  and a broken heat-layer object) instead of the full set.
- Reproduced deterministically on every reload - not a one-off timing
  fluke - which is what made it worth chasing down rather than dismissing
  as an environment quirk.
- Fixed by giving the map explicit fixed pixel dimensions
  (`width=1000, height=650`) instead of the default percentage-based
  sizing, which resolves synchronously and sidesteps the race. Verified
  after the fix: every layer renders, and interaction (zoom, pan, toggling
  each layer) surfaces no new errors. One harmless residual console line
  (a Canvas2D performance hint, not the exception) can still appear once on
  load; confirmed it does not recur or affect behaviour.
- Checked in both contexts the file needs to work in: standalone (opened
  directly) and embedded inside Streamlit's `components.html` iframe
  (`pages/1_Heatmap.py`) - both load cleanly.

**Heat layer tuning: radius=8, blur=10, min_opacity=0.35**
- The inherited defaults (radius=12, blur=18, min_opacity=0.3) were never a
  deliberate choice - scaffold values, untouched until this session.
- Generated three variants and compared them visually, at both the default
  city-wide zoom and zoomed into downtown, rather than picking numbers by
  feel:
  - Original (12/18): smooth, moderate legibility, but most neighbourhoods
    blend into one continuous wash at the default zoom.
  - **Tighter (8/10/0.35), chosen:** individual neighbourhood clusters
    (Ballard, Fremont, U-District, Capitol Hill) read as distinguishable
    patches rather than one blob. Converges with the original at deep zoom,
    so nothing is lost there.
  - Smoother (18/25): clearly worse - washes the whole corridor into one
    undifferentiated shape, works against the "make it legible" goal the
    plan set. Rejected outright.

**New, beyond the original plan: a per-business pin layer, NAICS color-coded**
- Added at the user's request: individual business markers, colored by
  category, with a legend - not part of the original session design.
- Volume (11,409 businesses) made plain, unclustered markers impractical -
  overlapping and unreadable at any zoom a viewer would actually use, and a
  much heavier file. Used `folium.plugins.FastMarkerCluster` (client-side
  clustering from a compact coordinate array) rather than one full `Marker`
  object per point - a requirement at this volume, not a style preference.
- Categorized using the same three groups `NAICS_STOREFRONT_PREFIXES`
  already defines (Retail 44/45, Food service 722, Personal services 812)
  rather than inventing a new scheme. Every business falls into exactly one
  group by construction: 5,221 / 3,909 / 2,279, summing exactly to the
  11,409 total, so no "Other" bucket was needed.
- Colors drawn from a tested categorical palette (blue / orange / aqua),
  chosen for mutual distinguishability rather than picked arbitrarily.
- Built as three separate toggleable layers (one per category) so a viewer
  can isolate, e.g., "just show restaurants," rather than one mixed layer.
  Off by default - a detail layer, not the primary view.
- `FastMarkerCluster`'s own `show` parameter did not reliably hide the
  layer at load - a real quirk hit during implementation, not assumed.
  Fixed by wrapping each cluster in a `folium.FeatureGroup(show=False)`,
  the same mechanism the ring layers already use reliably.
- Verified by hand: clustering, zoom-driven declustering into individual
  pins, layer toggling, and individual popups all tested working (a popup
  correctly read "MCDONALDS" at its real downtown Seattle location, next to
  OpenStreetMap's own McDonald's icon).
- Resulting file: ~1.25 MB - reasonable for a single self-contained HTML
  artifact carrying ~11,400 named, located points plus the heat and ring
  layers.

**Follow-up, same session: finer per-category splits, and a cosmetic naming fix**
- The legend read `Retail (44/45)` right next to a business count also in
  parens (`(5,221)`) in the layer control - two different kinds of number
  easy to mistake for each other. Fixed by spelling out
  `Retail — NAICS Code: 44/45`, count kept in its own separate parens.
- Considered building a dynamic, JS-driven NAICS-code filter (a dropdown
  reconfiguring the map on the fly) instead of more static toggle layers.
  Technically possible - fully client-side, no backend needed - but judged
  out of proportion for this stage: new, untested JS complexity in a file
  that had already needed two real bug fixes this session, for a polish
  feature on what the plan calls "illustration," while Session 8 (the
  actual write-up) is what the plan calls the highest-value hours left.
  Took the cheaper option instead, reusing the identical proven pattern.
- Added finer, still-static toggle layers within each of the three broad
  groups - real top categories by count, not guessed: Retail split into
  Clothing & accessories (595), Supermarkets & grocery (237), the
  NAICS-459999 catch-all reviewed back in Session 3 (1,188), and an "Other"
  residual (3,201); Food service into Full-service (1,282), Limited-service
  (1,258), Mobile food (385), Other (984); Personal services into Beauty
  salons (1,141), Pet care (261), Barber shops (174), Other (703). Every
  split sums exactly to its parent group's total.
  Sub-layers keep their parent's colour throughout (no new legend rows) -
  they refine *which* businesses of a colour show, not what the colour
  means.
- Renamed the base tile layer from Folium's default "openstreetmap" label
  to "Seattle 1 Line Business Density Heatmap," at the user's request.
- Total business layers: 15 (3 broad + 12 fine-grained), all built with the
  same `add_pin_layer()` helper - one pattern, no new JS. File grew to
  ~1.98 MB (each business now appears in two layers - its broad group and
  one specific sub-category). Verified: layer control shows all 15 with
  correct counts, toggling a sub-layer (tested: "Full-service restaurants")
  shows a visibly smaller, correctly-filtered cluster set, console clean.

**Same session, final round: the rail line itself, and richer pin tooltips**

- **Considered and declined a dynamic, code-based map-reconfiguration
  control** (a JS filter UI letting a viewer pick any NAICS code on the
  fly) before any of this round's work. Technically possible - fully
  client-side, no backend needed - but judged out of proportion this late:
  new, untested interactive JS in a file that had already needed two real
  bug fixes this session, for a polish feature on what the plan calls
  "illustration," while Session 8's write-up is the actual highest-value
  time left. The finer static toggle layers (above) were built instead, as
  the cheaper version of the same idea.
- **Added the actual rail line**, at the user's request - real GTFS route
  geometry (`shapes.txt`, shape_id `N23:S07`, 1,204 points, the most-used
  shape on route_id 100479 - 2,815 of 5,404 trips), not a straight line
  drawn between the 16 station points. Solid green, weight 5, on by
  default (unlike the detail pin layers) since this is core visual context,
  not a detail to opt into.
- **Added a large, high-contrast "1 Line" label**, not a hover tooltip -
  always visible, white-haloed bold text. Took two attempts to place
  correctly: a computed centroid of all 16 stations, and then Beacon Hill
  specifically, both still landed under the layer control panel (which has
  grown tall over the course of this session's additions) - checked
  visually both times rather than assumed correct. Settled on Othello,
  confirmed clear of both the layer control and the legend.
- **Enriched the pin hover tooltip** (switched from click-`popup` to
  hover-`tooltip`, per the request) to show business name, NAICS code,
  nearest station, and which ring band that business falls in relative to
  its nearest station. The nearest-station/ring computation is deliberately
  separate from step4_rings.py's `ring_stats` - that analysis assigns a
  business to *every* station whose buffer contains it (downtown overlap,
  on purpose), which has no single answer for "the" nearest station or
  ring. This is a simpler, single-nearest-station view built only for the
  tooltip, not a re-derivation of or replacement for the ring analysis.
  Verified directly: hovering a business named "Chai Sutra" showed
  `NAICS code: 722513 / Nearest station: Westlake / Ring 3 (0.2-0.3 mi)`,
  and manually confirmed that reads as correct for its location.
- File grew again with the extra tooltip fields: ~1.98 MB -> ~3.23 MB.
  Console clean throughout; verified with the browser's own error log, not
  just "it looks fine."

**Two small follow-ups, same session**

- **Repositioned the "1 Line" label** a second time - from Othello (far
  south) to Westlake's latitude (the heart of the corridor), offset west
  over Elliott Bay. The user asked for it "leftbound of the downtown
  corridor" specifically, not just anywhere clear of the UI.
- **Collapsed the layer control by default and capped its expanded
  height.** 23 toggleable layers (4 rings + 15 business layers +
  heat/stations/rail) had grown the always-open panel large enough to
  cover most of the map. Considered building true nested/collapsible
  groups (a single "Businesses" dropdown holding all 15) - would need a
  custom Leaflet control or a third-party plugin, real new complexity for
  a polish feature, the same class of thing declined earlier this session
  for the dynamic filter idea. Used only Leaflet's own built-in collapsed
  state plus a CSS max-height/scroll cap instead - zero new JS. Verified:
  collapsed by default, map fully visible; expand and collapse both work;
  console clean.
- **Fixed a doubled name the user caught by reading the actual layer
  control text**: the three whole-group business layers read "Businesses:
  Retail — Retail — NAICS Code: 44/45" (name repeated). `add_pin_layer()`
  already prefixes `group_name` onto the label; passing the full
  `naics_label()` string (which also has the name) as the sublabel for
  just that one call site doubled it - the 12 finer sub-category layers
  were already clean. One-line fix.
- **Station markers switched from click-popup (name only) to hover-tooltip
  (name + 2025 avg monthly ridership)**, matching the business-pin tooltip
  pattern. Reused `ridership_by_station.csv` from Session 5 directly - no
  need to re-derive anything from the PDF. Left join (not inner), so a
  station missing a ridership match still gets a marker rather than
  vanishing silently; none were missing here, all 16 matched. Verified
  programmatically via direct Leaflet layer inspection (more reliable than
  chasing pixel-perfect hover in the automated browser pane) - tooltip
  content confirmed correct, e.g. "Capitol Hill" / "278,486 avg. monthly
  boardings (2025)," matching Session 5's numbers exactly.

**Post-Session-7, same day: mojibake in the embed, and an unreachable layer control**

- Caught by the user, testing the actual embedded Streamlit page (not the
  standalone file) at a realistic window width: the legend and layer-control
  labels showed mangled characters (`â€"` etc.) in place of every em dash,
  and the layer control itself couldn't be found at all.
- **Mojibake root cause:** `pages/1_Heatmap.py` read `outputs/heatmap.html`
  with `Path.read_text()` and no explicit encoding. Folium always saves
  that file as UTF-8; on Windows, `read_text()` without an encoding falls
  back to the OS codepage (cp1252), which corrupts any multi-byte UTF-8
  character on read. The saved file on disk was always correct - this was
  a read bug in the embedding page only, not a data or generation problem.
  Fixed by reading explicitly as UTF-8.
- **Layer-control root cause:** `folium.LayerControl()` defaults to
  Leaflet's top-right corner. The map has a fixed 1000px width (needed for
  the earlier Leaflet.heat fix), and Streamlit's content area is often
  narrower than that with the sidebar open, pushing the control past the
  visible/scrollable edge. Fixed by setting `position="topleft"`, where it
  stacks under the zoom control and stays reachable at any width. Also
  enabled iframe scrolling in `pages/1_Heatmap.py` as a defensive fallback
  for any future width overflow.
- Why Session 7's own verification missed both: that pass checked "does it
  load without errors and do the layers render," which it did - neither
  bug throws a console error or breaks a layer. Only reading the actual
  rendered text, and checking control reachability at a realistic (not
  maximized) window width, surfaced them.
- Verified after the fix: layer-control icon visible and expandable at
  800px width; legend and all 15 business-layer names render with correct
  em dashes; regenerated `outputs/heatmap.html` and re-checked inside
  Streamlit, not just the standalone file.

**Post-Session-7, same day: restricted the map to businesses within a station's ring**

- The user's idea: the heat layer and pin layers had been plotting all
  11,409 businesses in the cleaned dataset, with no distance limit at all -
  a business in, say, Ballard (nowhere near a station) showed up exactly
  like one across the street from a platform.
- This was a real inconsistency, not just a display preference:
  `step4_rings.py`'s ring/chain analysis - the numbers actually reported
  on the Findings page - only ever counts a business if it falls inside at
  least one station's buffer. The map was the one place in the project
  still showing the unbounded citywide picture, understating how
  concentrated the analysis's actual universe is.
- Implemented as a filter on nearest-station distance: a business's ring
  band was already being computed (`nearest_station_and_ring()`, used for
  the pin hover tooltip) as one of the four ring bands or "Beyond ring 4."
  Dropping the "Beyond ring 4" rows before building the heat layer and
  pin layers is equivalent to "inside at least one station's 0.6 mi outer
  buffer," because nearest-station distance is a lower bound on distance
  to every other station - if the closest one is already past 0.6 mi,
  every other station is farther. No new spatial computation needed;
  moved the existing one earlier in `main()` so both the heat layer and
  the pin layers draw from one shared filtered set instead of computing
  it separately or drifting out of sync.
- Result: 4,120 of 11,409 businesses (36%) fall within some station's
  ring; the other 7,289 (64%) are now excluded from the map. Printed to
  console on every run for visibility, the same convention as the
  project's other warning/count lines.
- Verified visually: at city-wide zoom, the heat signature is now a tight
  ribbon following the rail alignment itself, with no citywide wash -
  compared directly against the prior screenshot showing heat spread
  across neighbourhoods with no station nearby (Magnolia, West Seattle,
  far North Seattle).

**Post-Session-7, same day: an opt-in "all Seattle businesses" heat toggle**

- The user's idea, immediately after the ring-only filter above: keep the
  ring-only view as the default, but add back a way to see the citywide
  picture on request, as its own checkbox rather than replacing the
  default.
- Implemented as a second `HeatMap` layer plotting the full unfiltered
  11,409-business set, `show=False` by default, alongside
  the within-rings layer (`show=True`). Both use identical
  radius/blur/min_opacity tuning so they're visually comparable, not
  independently tuned versions that could mislead by tuning alone. Two
  lines in the layer control: "Commercial density (within station rings)"
  and "Commercial density (all Seattle businesses)," togglable
  independently of each other.
- Pin layers were deliberately NOT duplicated for the citywide set -
  doubling all 15 business-pin layers would double an already-large
  layer-control menu for a detail view of businesses outside the
  project's actual analysis scope. The heat-layer toggle covers the
  "what does citywide context look like" need well enough on its own
  without that cost.
- Verified visually: toggled on with the within-rings layer also on, the
  heat signature visibly widens beyond the tight rail-corridor ribbon into
  a broader citywide spread (checked zoomed out, city-wide view); toggled
  off, returns to exactly the tight ribbon from the previous fix, with the
  layer-control checkbox state (checked/unchecked) matching what's
  actually drawn in both cases.

---

## Observations

**Gradient**
- Not monotonic. Aggregate density by ring: 957 -> 550 -> **592** -> 311
  businesses/sq mi — a real uptick at ring 3 (0.2-0.3mi). Only 2 of 16
  stations decline cleanly (International District/Chinatown, U District).
- **Root cause identified, not just observed:** station spacing vs. ring
  radii. Symphony and Westlake sit 0.268 mi apart — closer than the ring
  system's own reach — so each one's ring 3 partly samples the *other's*
  core, not its own periphery. Both spike at exactly ring 3 (Westlake
  2519->1498->**2570**->781; Symphony 1467->1265->**2410**->779). Beacon
  Hill/Mount Baker sit right at the boundary (0.659 mi) and show only a weak
  version of the same thing — the effect scales with how close the overlap
  is, which is itself evidence it's real and not noise.
- This sharpens the existing "downtown buffers overlap" disclosure into a
  specific causal claim: the *shape* of the aggregate gradient, not just its
  level, is partly a station-spacing artifact.
- One exception the mechanism doesn't explain: Pioneer Square rises from
  ring 1 to ring 2 (797->1520), not ring 2 to ring 3, and its nearest
  neighbor (ID/Chinatown, 0.354 mi) is too far to be the cause. Reads more
  like a genuine siting effect — its commercial core sitting slightly off
  from the platform — left as an open question, not folded into the
  overlap explanation.
- **Candidate framing for the write-up, marked 2026-09-14, not written
  up - the user's interpretation to make:** Yang and Diez-Roux's own
  model (already cited above for the ring-distance rationale) describes
  walking behavior as a smooth, continuous distance decay. This project's
  actual gradient is a discrete 4-ring step function, and it isn't
  smooth - it dips then spikes at ring 3 before falling again. The gap
  between "what a smooth decay process would predict" and "what the
  4-ring data actually shows" is a sourced way to frame *why* the ring-3
  anomaly is worth explaining (the Westlake/Symphony spacing mechanism
  above) rather than waved off as noise - contrasting an expected smooth
  baseline against an observed irregular one, not claiming the irregular
  shape disproves the decay model.
- **Second candidate framing, marked 2026-09-14, not written up - the
  user's interpretation to make:** Homer Hoyt's Sector Model (Merilus,
  "10: Urbanization," *Cultural Geography (C-ID GEOG 120)*, LibreTexts,
  10.10) describes commercial activity distorting into wedges along
  transit/transportation corridors rather than declining in clean circles
  from a single center. That's a conceptual match for what this project
  found: density along the 1 Line doesn't radiate cleanly outward from
  each station individually - it behaves more like a corridor effect,
  with downtown stations bleeding into each other, which is exactly the
  Westlake/Symphony spacing mechanism above in different language. Usable
  as a name for the pattern, with a caveat that matters: Burgess's
  Concentric Ring Model (the same chapter's own top-ranked concept for
  this project, and the thing the ring methodology superficially
  resembles) is explicitly a single-CBD, land-value/class model, not a
  multi-station pedestrian-walkshed model - the chapter itself notes it
  "accurately describes only a few American cities... most often found on
  the flatlands of the Midwest" (Columbus, Indianapolis), not
  hilly/coastal, single-corridor cities like Seattle. **Use Hoyt's
  critique of pure concentric models to explain why this project's
  gradient distorted; don't claim Burgess's model validates the ring
  methodology itself.**

**Stations against the pattern**
- **Rainier Beach** (13 businesses within 0.3mi): literal zero in the
  0.2-0.3mi ring specifically, not just low. Consistent with the
  documented "commercial core sits several blocks from the platform."
- **SODO** (110): density *rises* through rings 1-3 (287->308->459) before
  falling. Reads as industrial immediately at the platform, real commerce
  only appearing toward Pioneer Square at the buffer's edge.
- **Stadium** (15): 1 business in ring 1, then 373 in ring 4 — largely
  borrowed from International District/Chinatown, 0.416 mi away and inside
  Stadium's outer ring. Not really "Stadium's own" walkshed.
- **Northgate and University of Washington** — not named in the original
  plan, but the data flags them just as starkly: **zero businesses in the
  entire 0-0.1mi ring**, both of them. Plausibly a still-developing
  redevelopment area (Northgate) and a campus/hospital-immediate platform
  (UW), but not independently confirmed the way the other three were.

**Ridership relationship**
- r = 0.684 (avg monthly boardings vs. businesses within 0.3mi), n=16.
  Moderate-to-strong positive.
- **University of Washington is the sharpest outlier**: lowest commercial
  density of any station (5 businesses within 0.3mi) but 5th-highest
  ridership (152,748/month) — a large positive residual. Consistent with
  the access-mode limitation already on the methodology page: a
  campus/hospital population that rides without shopping nearby.

**Chains**
- After the `location_count >= 2` fix (see "Quality metrics" and "Things
  that went wrong" above for the bug itself) and the later brand-
  normalization patch (see "Analyst choices" > Brand normalization):
  **8.9%** of locations belong to a real multi-location chain (155
  brands). The original overlap-only bug would have said 45.7% — over 5x
  too high; the normalization patch on top of that fix moved the number a
  further 0.1 point (8.8% -> 8.9%), a small, expected correction in the
  same direction, not a second version of the same bug.
  **Updated again, Session 8 (2026-09-15):** excluding the three
  corporate food-service contractors (Compass One, Bon Appetit
  Management, Flik International — see "Changes" above) moves this to
  **152 brands, 8.5%**. The 155/8.9% figures here are the pre-exclusion
  snapshot, not the current one.
- Real top chains, verified: Subway (7 locations/8 stations), Evergreens
  Salad (7/5), Caffe Ladro (5/5), Westman's Bagels, Metro by T-Mobile,
  Great State Burger, Just Poke, Dough Zone Dumpling House — all real,
  checkable Seattle/PNW brands, not overlap artifacts.
- **Checked, Session 8 (2026-09-15): chain share does rise toward the
  platform.** 11.0% (ring 1) -> 10.1% (ring 2) -> 8.3% (ring 3) -> 8.5%
  (ring 4) - a cleaner, more monotonic pattern than the main density
  gradient's own ring-3 spike, though not perfectly monotonic itself (see
  below). New pipeline output `outputs/chain_ring_stats.csv`
  (step4_rings.py), same counting convention as `ring_stats.csv` (every
  business-ring-per-station match counts, including downtown-overlap
  duplicates, so the two are directly comparable). Denominator is the
  full joined set, not just brand-matched rows, so blank/unparseable
  names count toward "total businesses" without being excluded from both
  numerator and denominator. Rendered as Graph 4 / Table 4 on the
  Findings page.
- **Session 8 (2026-09-15), same-day follow-up: the ring-3-to-4 chain-share
  tick-up (8.3% -> 8.5%) is the same neighbor-sampling mechanism as the
  gradient's ring-3 spike, one ring later and a different station pair.**
  Checked by re-running the join with a per-station breakdown (not
  persisted as a pipeline output - one-off verification, not a reusable
  stat): SODO and Stadium, two of the four against-the-pattern stations
  already named in the gradient's ring-3 breakdown, are what flips ring 4
  from a continued decline into a small rise. Stadium's ring 4 (0.3-0.6mi)
  carries 31 chain matches out of 373 businesses - consistent with the
  existing "largely borrowed [from International District/Chinatown]"
  finding above, not businesses in Stadium's own walkshed. SODO's ring 4
  carries 18 of 149, consistent with its own "real commerce only appearing
  toward Pioneer Square at the buffer's edge" finding. Remove just those
  two stations and the aggregate ring-3-to-4 move reverts to a clean
  decline (8.7% -> 8.4%). Added as a caption directly below Graph 4 on the
  Findings page, tying the two reversals together for the reader before
  the chains TODO.
- **Candidate framing for that open question, marked 2026-09-14, not
  written up - a hypothesis to test against the data, not evidence that
  already backs a number:** Central Place Theory's *range* (the maximum
  distance customers will travel for a good or service) and *threshold
  population* (the minimum customer base a business needs to survive)
  (Merilus, "10: Urbanization," *Cultural Geography (C-ID GEOG 120)*,
  LibreTexts, 10.9) give vocabulary for the ring-1-vs-ring-4 chain-share
  question above, if it gets checked: chains generally need a larger
  threshold population to sustain a location than an independent shop
  does, which could predict a different distance-decay pattern for chains
  vs. independents. This doesn't back up the 152-brand/8.5% figure
  already on record - it's a lens for a question not yet answered, only
  useful if that ring-by-ring chain check actually gets run.

---

## Things that went wrong

Worth keeping. A limitations section written by someone who hit real
problems reads differently from one assembled from a template.

- **The chain analysis's headline number was wrong by >5x before the
  required hand-check caught it.** `station_count > 1` looked like a
  reasonable definition of "chain" until two single-location businesses
  (PU POWDER, Saigon Drip Kitchen) showed up in the top-15 "most stations"
  table. The downtown buffer overlap — already known and disclosed for
  density — turned out to inflate the chain metric far more severely, in a
  way nothing upstream would have flagged on its own. Full detail under
  "Quality metrics." Lesson: "verify a handful by hand" isn't a formality —
  it's the step that actually catches this class of bug, and a plausible-
  looking top-15 list is not the same as a correct one.
- Earlier in the project: the same lesson showed up with the GTFS route
  match (Session 2) and the "average boardings per day" redundancy claim
  (Session 5) — both were assumed correct until actually checked, and both
  turned out to need correction. Pattern worth remembering for Session 8's
  write-up: check claims against the data before stating them, even ones
  that feel obviously true.

## Open items

Both fixed in step 2, at the source (raw 84,390-row file), rather than
patched on the already-filtered set:

- **Blank `business_name`** — Trade Name empty but Business Legal Name
  populated. Fixed by falling back to Legal Name. Only 2 of these survived
  into the 11,466-row clean set when first spotted, but the fix runs before
  any filtering and caught **22** in the full raw file.
- **`19000101` sentinel `license_start_date`** — a null-date placeholder, not
  a real founding date (would otherwise read as a 126-year-old business).
  Nulled out (set to blank), not dropped — the row itself is fine, just that
  one field. 1 survived into the clean set when first spotted; the fix
  caught **5** in the full raw file.

Verified after re-running step 2: 0 blank `business_name`, 0 `19000101`
values, 1 blank `license_start_date` (the nulled one that happened to survive
filtering) — correctly represented as missing rather than a bogus date. Row
count unchanged at 11,466; these were fixes, not filters.
