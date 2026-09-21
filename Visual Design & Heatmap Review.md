# Visual design and heatmap review

Covers the visual-polish work of 2026-09-19 and 2026-09-20, organized by
concept rather than by date. **This is a map, not the record of truth:**
`DECISIONS.md` is authoritative for exact reasoning and values, and
`git log` for exact changes. Earlier work (the initial build, Sessions
1-9) is in `Initial Build Development Context.md`, kept locally rather
than in the repo.

## Contents

1. [State of the site](#state-of-the-site)
2. [Color system](#1-color-system)
3. [Site theme](#2-site-theme)
4. [Findings page charts](#3-findings-page-charts)
5. [Heatmap density layer](#4-heatmap-density-layer)
6. [Heatmap light/dark mode](#5-heatmap-lightdark-mode)
7. [Heatmap layer control and page copy](#6-heatmap-layer-control-and-page-copy)
8. [Cross-project boundary and handoffs](#7-cross-project-boundary-and-handoffs)
9. [Working practices that held up](#8-working-practices-that-held-up)
10. [Mistakes and corrections](#9-mistakes-and-corrections)
11. [Open items](#10-open-items)
12. [Where things live](#where-things-live)

## State of the site

- **Theme:** Warm charcoal, dark-only.
- **Findings page:** one warm orange ramp for the rings and ring-based bars;
  Graph 2 fills its container; red is reserved for "against the pattern".
- **Heatmap:** orange density layer; a two-position light/dark switch under
  the layer icon; the layer control lists overlays only.
- **Not touched:** the analysis, the pipeline, the `outputs/` CSVs, and the
  user's own `TODO — write this up` prose on the Findings page.
- **Deployment:** the changes described here are pushed to `main` and were
  verified on the live site on 2026-09-20.

Commits, for reference: `7282174` (warm ring palette, responsive Graph 2),
`984a343` (ring 4 tuning), `e2b8034` (Warm charcoal theme), `ffcc3f2`
(orange heat, AI Use wording), `22920a3` (Dark Mode), `0771eff`
(light/dark switch).

---

## 1. Color system

**Rule of the palette:** each color has one job.

| Job | Color | Where |
|---|---|---|
| Ring 1 to ring 4 (bold to pale with distance) | `#C2500A`, `#F0801F`, `#FBB878`, `#FDD0A2` | Schematic 1, Graph 1 and 5 bars, legend swatches |
| Density heat | `#FBB878`, `#F97316`, `#DE6412`, `#C0570F`, `#8F3A05` | Heatmap heat layer |
| "Against the pattern" | `#e45756` (`AGAINST_RED`) | Graph 2 range, Table 1 highlight, station-note headers |
| Ridership | gold `#F2C94C` | Graph 4 dots |
| Quiet UI accent | soft peach `#FBB878` | Theme primary color and links |

**Constraints that shaped it**
- Red is off limits for the ring ramp: Graph 2 and Table 1 already use it
  for "against the pattern". It now lives in a single `AGAINST_RED`
  constant (was four hardcoded copies), so shifting it later is a one-line
  change.
- Ring orange would have collided with Graph 4's orange Ridership dots on
  the same page, so those became gold. The ramp deliberately never reaches
  true yellow so the gold stays distinct from ring 3 and 4.
- Ring numerals are white on ring 1 and dark brown `#3B1505` on rings 2-4
  for contrast.

**Ring 4 tuning (the part worth re-reading).** On the dark page a pale
ring reads as the brightest thing on screen, the reverse of the usual "more
is brighter" convention, so ring 4's color was tuned in stages:
1. The first cream `#FDE3C8` read as near-white.
2. Fading ring 4 toward the background (3.1:1 contrast) was previewed and
   rejected as less faithful to bold-to-pale.
3. Darkening ring 4 by 15% was previewed and rejected: it made rings 3 and
   4 equal in lightness and erased the step between them.
4. What the user actually meant was "15% more orange". Shipped: saturation
   raised from 21% to 36%, giving `#FDD0A2`, still lighter than ring 3
   (about 13:1 against the page, was 15:1; the ring 3 to ring 4 lightness
   gap narrowed from about 12 to about 7 points).

**Caveat:** ring 4 nearly vanishes on a light background, so any future
light theme needs this ramp retuned.

---

## 2. Site theme

**Chosen: Warm charcoal**, via `.streamlit/config.toml`.

| Role | Value |
|---|---|
| Page | `#171412` |
| Sidebar and widgets | `#221D19` |
| Text | `#F3EDE6` |
| Borders | `#3A322B` |
| Primary and links | `#FBB878` |

**Why Warm charcoal:**
- The warm ring ramp reads as part of the design instead of an orange
  accent on Streamlit's stock blue-black.
- Over **Midnight slate**, mainly because Graph 2's dimmed blue lines and
  Graph 4's blue dots would blend into a navy background.
- Over **Paper (light)**, because it would need the ring palette retuned and
  the dark-only Flowchart and heatmap reworked.

**Primary color stays quiet on purpose:** peach, not the vivid orange, so
the strong orange remains reserved for the ring bars and Graph 2's red does
not compete with an orange UI.

**Hardcoded colors that had to be matched by hand:**
- The sidebar "Pages" label and social icons (`components.py`).
- The Flowchart iframe background and border, plus its Mermaid theme, which
  moved from Mermaid's cool built-in "dark" to a "base" theme with warm
  variables (brown nodes, orange borders).

**Red check (done on the new background):** Graph 2, Table 1 and the
station-note headers were rendered in `#e45756`; it stays clearly red and
distinct from the orange ramp, about 5:1 contrast. Kept unchanged. On an
all-warm page it is a slightly weaker "against the pattern" signal than
before, which is the trade-off.

**Streamlit behavior to remember:** setting an explicit `[theme]` removes
Streamlit's light/dark toggle, so the site is dark-only. An earlier claim
that visitors could still toggle was wrong and has been corrected in the
config comment and `DECISIONS.md`.

Adding `[theme.light]` and `[theme.dark]` blocks **does** bring the toggle
back (tested 2026-09-20: System / Light / Dark appear in the main menu, and
the choice follows in-app navigation). It is not adopted, because the app
has dark-only colors hardcoded outside the theme, and light mode breaks
them: the sidebar "Pages" label renders at 1.01:1 contrast, effectively
invisible, the Flowchart's Mermaid iframe stays a dark box on a white page,
and the social icons fall to 2.77:1. Restoring the toggle means fixing
those three first, on top of retuning the ring ramp.

**Midnight slate** was never built; only a mock-up palette exists
(page `#0B1220`, surface `#131C2E`, border `#23304A`, text `#E6EDF7`).

---

## 3. Findings page charts

**Graph 2 on phones.** A fixed 900px chart overflowed a 343px container
with nothing to scroll it, so only Ring 1 was visible (measured at a 375px
viewport, not assumed). Fixed by filling the container width and moving the
legend above the plot (top, horizontal). That also removed a hardcoded dark
legend fill and 90px of leftover bottom padding. Trade-off: the fixed 900px
was a deliberate laptop-window choice, and it is given up. Full-screen mode
was tested afterwards (2026-09-20) and fills correctly at both desktop and
375px, with all four rings visible.

**Ring colors on Graph 1 and Graph 5** follow the shared ramp in section 1.

---

## 4. Heatmap density layer

The heat layer changed from ColorBrewer Reds to an orange ramp of the same
family as Schematic 1: `#FBB878`, `#F97316`, `#DE6412`, `#C0570F`,
`#8F3A05` (stops at 0.3, 0.5, 0.7, 0.85, 1.0).

**Why the exact ring colors did not work.** The first attempt used the ring
colors directly (`#FDD0A2` at the low end). Leaflet.heat's opacity follows
density, so the palest stop nearly vanished on the light OpenStreetMap
tiles. Shifting the ramp one step more saturated (the "B: fading outward"
sample the user pointed to) keeps low-density areas readable.

**Knock-on, since resolved:** going orange left the Food service pins and
clusters (the Cove palette's orange `#eb6834`) only 6 degrees of hue from
the heat ramp, so they sank into the densest areas - exactly where food
service is most worth reading. They are now magenta `#C2185B`: 47 degrees
off the ramp, still 123 from the retail blue and 177 from the
personal-services aqua, with white numeral contrast up from 3.2 to 5.9.
Plum and violet were rendered side by side on the same downtown view
before choosing; violet was ruled out because it sits 43 degrees from the
retail blue and the two read alike at cluster size.

---

## 5. Heatmap light/dark mode

### What it is

A light/dark option built from the same OpenStreetMap tiles, recolored in
the browser with a CSS filter (`invert(1) hue-rotate(180deg)
brightness(0.85) contrast(0.9) saturate(0.7)`). No new tile provider and no
API key: OpenStreetMap has no dark mode and Leaflet has none built in, and
CartoDB and similar providers were already ruled out on keys and licensing.

### How it works

- Two base tile layers, both kept out of the layer control
  (`control=False`); the dark one carries `class_name="dark-osm-tiles"`.
- A custom Leaflet control swaps the two layers and toggles a `dark-base`
  class on `<body>`. Body rather than the map container, because the legend
  sits outside the container.
- CSS under `.dark-base` restyles the map chrome in the warm charcoal
  palette: legend, zoom buttons, layer control and its icon, attribution,
  and the pin hover tooltip. Overlays (heat, rings, pins) live in other
  panes, so the tile filter does not touch them.
- Ring outlines (`#2c3e50`, used nowhere else) are invisible on dark tiles,
  so they are lightened under `.dark-base`.
- Opens on the visitor's own `prefers-color-scheme` rather than always
  light, and follows later OS changes until they work the switch
  themselves, after which their choice wins. Nothing is stored, so a
  reload goes back to following the system.

### The switch (UI design)

One opaque 30x60 box directly under the layer icon: sun on top, moon
below, both always visible, with a thumb behind the active mode. Light mode
has the thumb at the top (gap below); dark mode has it at the bottom (gap
above). It slides over 0.2 seconds, toggles on click or Space, and carries
`role="switch"` and an aria state.

**Placement.** The user first asked for top-right. Top-left was chosen
instead: the map is a fixed 1000px wide (a Leaflet.heat initialization
workaround) and scrolls horizontally when the page is narrower, so a
top-right control can sit past the visible edge. It is the same reason the
layer control is top-left.

**How the design got there.** The first version was a single icon that
changed between moon and sun. Feedback: icons not centered in the box, a
transparent cutoff instead of an opaque background, and the switch in the
same position in both states. The redraft is the two-position switch above.
Centring was verified by measurement (each icon's center matches its cell
and the thumb), and the box positions are identical in both modes.

### Pitfalls worth knowing

| Pitfall | Fix |
|---|---|
| A bare script element renders above the map variable and throws | Use a `folium.MacroElement`, which renders after it |
| Legend styling is inline, so normal CSS cannot override it | `!important` on the dark legend rules |
| A 1px dark border against Leaflet's 2px shifted every control a pixel on toggle | Override `border-color` only, never the width |
| `baselayerchange` does not fire for layers outside the layer control | Toggle the class directly in the switch's click handler |
| Tooltips only appear at high zoom, so they are hard to test | Inject a synthetic tooltip and read computed styles |

### Limits

It is a recolor, not a designed dark map, so labels and road colors are a
bit muddier than a purpose-built dark style. The page around the map stays
dark regardless of which way the map is set, since the site itself is
dark-only.

One caveat on the system-following added 2026-09-20: the initial load is
verified in both directions, and a manual choice is verified to survive a
system flip. Live following of an OS change *mid-session* could not be
verified, because the browser's media emulation updates
`matchMedia().matches` without dispatching a `change` event inside the
iframe - a freshly attached, known-good listener saw zero events too. The
code is the standard `addEventListener('change')` pattern, but it is
untested on a real OS theme switch.

---

## 6. Heatmap layer control and page copy

**Layer-control order.** The three bold group layers (Retail, Food service,
Personal services) now sit together, with each group's subcategories
grouped by umbrella below them. Same 21 layers and defaults. Done with two
loops, because Leaflet lists layers in the order they are added.

**Heatmap page sentence** (underlined). It now reads: "Concentric ring
boundaries and NAICS/GIS geocoded storefronts are toggleable via the layer
control in the top left, and the button beneath it switches between light
and dark mode." It went through two versions, because Dark Mode first
appeared as a layer-control item and then moved to the separate switch.

**AI Use sentence** (Methodology page). The opening now reads: "This
project is based in HTML & Python and was built in tandem with Claude
Code."

---

## 7. Cross-project boundary and handoffs

**Boundary.** This project's agent stays inside `link-station-commercial`
and asks before reading or writing any other directory, including through
junctions or symlinks. Passoffs to the sister project (`expanded-heatmap`)
happen only when the user asks and after the path is confirmed. The
purpose is to keep the two projects segmented while the second develops its
own identity. The rule is saved in the agent's memory.

**Handoffs written.**
- `expanded-heatmap/docs/dark_mode_handoff.md`: written before the boundary
  was set (already in the other repo); the content was fine.
- `.claude/handoffs/switch_ui_handoff.md`: drafted and held. Supersedes the
  first file's layer-control-radio approach with the switch above.
- `.claude/handoffs/midnight_slate_theme_handoff.md`: drafted and held.
  Notes that Midnight slate was never built here, its palette comes from a
  mock-up, and the sister project should pair slate chrome with its own teal
  accent instead of copying the blue.

Both held files are gitignored (`.claude/`) and unsent.

---

## 8. Working practices that held up

- **Draft before writing.** Copy and visual options were shown in chat
  first, and each visual change was previewed on a local server before
  committing.
- **Commit and push.** Commits happen after each approved step; pushes only
  on the user's explicit instruction.
- **Measure, do not eyeball.** Colors, positions and centring were checked
  through DOM and computed styles, not screenshots alone. One gotcha: the
  switch's 0.2s transition lags in a background preview tab, so a computed
  color read too soon reports a mid-transition value.
- **Test hygiene.** Each local server is stopped afterwards and
  `__pycache__` cleared.
- **Confirm 404s are not the map.** The only console errors seen were
  Streamlit's own `_stcore/health` and `host-config` checks at a `/Page`
  path.

---

## 9. Mistakes and corrections

1. Claimed visitors could toggle themes; wrong (an explicit `[theme]`
   removes the toggle). Corrected in the config comment and `DECISIONS.md`.
2. Read "15% darker" for ring 4 where the user meant "15% more orange".
3. First heat gradient reused the exact ring colors and was too faint on
   the light map.
4. First dark handler used a bare script element that threw before the map
   existed.
5. The dark border width difference shifted controls by a pixel.
6. Wrote to the sister project's directory without asking first; the
   boundary in section 7 followed.

---

## 10. Open items

**Checks not yet done**
- Graph 2 on a real phone, as opposed to an emulated 375px viewport.
- The map following a real OS theme switch mid-session (see section 5).
- Midnight slate on a real page (it was never built; see section 2).
- The hand-sampling percentages behind the NAICS exclusions. A 3x sample
  (120 rows of 812990, 75 of 459999, seeded 20260920) was drawn for review;
  the storefront judgments are the analyst's, not automated.

**Checked on 2026-09-20** (previously listed here as untested)
- Live site: up, dark theme, switch and 21 overlays serving correctly.
- Graph 2 full-screen: fills correctly at desktop and 375px.
- `[theme.light]`/`[theme.dark]`: restores the toggle, but three hardcoded
  dark-only colors break in light mode (see section 2).

**Deferred, deliberately**
- **A visitor-facing light/dark toggle for the whole site.** Confirmed
  possible via `[theme.light]`/`[theme.dark]` (see section 2). Deferred
  2026-09-20 because it needs four prerequisites first: the sidebar
  "Pages" label (1.01:1 in light mode, invisible), the Flowchart's
  Mermaid iframe (hardcoded dark), the social icons (2.77:1), and a
  retune of the ring ramp, whose pale ring 4 nearly vanishes on white.
  Revisit as a piece of work in its own right, not a config flip.

**Documentation**
- `DECISIONS.md` has no entry yet for the cross-project boundary or the two
  held passoffs. Its 9/20 entries also describe the earlier Dark Mode radios
  before the switch entry; correct in order, worth a tidy.
- `.claude/skills/new-transit-line/SKILL.md` lists `name="Light Mode"` as
  the base layer's display name. That name no longer appears in any UI, so
  the wording is slightly off. Local-only, low priority.

**Left to the user**
- The Findings page `TODO — write this up` blocks remain the user's own
  analysis to write.
- Whether and when to pass the two held handoffs to the sister project.
  Its config comment about visitor theme switching may be wrong after any
  dark theme.

---

## Where things live

| Concept | File and symbol |
|---|---|
| Ring ramp, `AGAINST_RED` | `pages/2_Findings_&_EDA.py` (`RING_SCHEMATIC_SVG`, `ring_colors`, `AGAINST_RED`) |
| Site theme | `.streamlit/config.toml` |
| Hardcoded dark colors | `components.py`, `pages/4_Flowchart.py` |
| Heat gradient | `src/step5_map.py`: `HEAT_GRADIENT` |
| Light/dark switch, dark CSS | `src/step5_map.py`: `mode_toggle` (`MacroElement`), the `<style>` block, `.dark-osm-tiles`, `.dark-base` |
| Layer-control order | `src/step5_map.py`: the two `NAICS_GROUPS` loops |
| Heatmap page copy | `pages/1_Heatmap.py` |
| AI Use copy | `pages/3_Methodology_&_Limitations.py` |
| Reasoning and exact values | `DECISIONS.md` (entries dated 2026-09-19 and 2026-09-20) |
| Held handoffs (local) | `.claude/handoffs/` |
