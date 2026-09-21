# Data sources, licenses and terms

Every dataset this project reads, what it is used for, and what its publisher
actually says about reuse. **License fields were read on 2026-09-20**, not
inferred from the fact that a source sits on an open-data portal.

This matters more here than for a project that only displays data, because
this repository **redistributes derived data publicly**:
`outputs/heatmap.html` is committed and served, and carries 4,120 business
records paired with precise coordinates; `outputs/*.csv` carry aggregate
statistics; and the station coordinates and rail alignment are republished as
map geometry. "Is redistribution of derived data permitted" is therefore a
description of something already happening, not a hypothetical.

**This is a record of what each source states, not legal advice.** Where terms
are ambiguous the entry says so rather than resolving it.

---

## Summary

| Source | License as stated | Redistribution | Status |
|---|---|---|---|
| Seattle business licenses (CSV) | **Public Domain** + portal terms | permitted, **non-commercial condition** | clear |
| Seattle Business License (GIS layer) | covered by the portal terms | as above | resolved |
| Seattle land use zoning | **PDDL** | permitted | clear (not redistributed) |
| Sound Transit GTFS | limited, **revocable** | permitted **with flow-down** | note added |
| Sound Transit ridership dashboard | website terms: informational use only | **prohibited without prior permission** | **conflict** |
| US Census geocoder | API terms require a notice | not restricted | **notice missing** |
| OpenStreetMap tiles | ODbL (data), attribution required | see entry | attribution present |

**The one that needs a decision:** Sound Transit's ridership figures were
transcribed from a page on `soundtransit.org`, which its website terms treat
as "Website Content" and license for informational use only, prohibiting
republication "without prior permission." This project republishes those
figures. See source 5.

---

## 1. Active Business License Tax Certificate — the project's spine

- **Publisher:** City of Seattle, Department of Finance and Administrative
  Services, via `data.seattle.gov` (Socrata dataset `wnbq-64tb`)
- **Used by:** `step2_clean_businesses.py`; every analysis on the site
- **Obtained:** manual CSV export, snapshot `2026-09-06`
- **License:** `"Public Domain"` (`licenseId: PUBLIC_DOMAIN`), stated in the
  dataset's own Socrata metadata
- **Attribution:** the metadata carries
  `attribution: "Department of Finance and Administrative Services"` and
  `attributionLink: http://www.seattle.gov`. Public domain does not compel
  credit, but the publisher supplies an attribution string, so crediting it
  is the publisher's own expectation.
- **Redistribution of derived data:** permitted.
- **Note:** this is the source whose records are republished as named map
  pins. It is also the one with the cleanest grant, which is fortunate given
  how much of the site rests on it.

### The portal terms, which govern every Seattle dataset here

`data.seattle.gov`'s Terms of Use bind anyone "using data made available
through this site," so they cover sources 1, 2 and 3. Three clauses matter:

- **A non-commercial condition, and it reaches this data.** *"To the extent
  the data consists of a list of individuals or can be readily sorted,
  filtered, or configured as a list of individuals, it is not to be used for
  a commercial purpose."* The business register is not a list of individuals
  on its face, but it demonstrably **can** be configured as one — that is
  precisely what `scripts/check_personal_exposure.py` does, and it found 41
  such rows. So the condition applies. A portfolio piece is not a commercial
  purpose on any ordinary reading, so the project is within it today; the
  constraint would bite if this were ever monetised.
- **Attribution is not required.** *"Unless otherwise indicated, data on this
  site does not require specific attribution."* The Methodology page credits
  Seattle anyway, since the dataset supplies an attribution string and
  crediting sources is good practice regardless.
- **No warranty**, and the City reserves the right to discontinue any dataset
  without notice — which is a reason the snapshot dates recorded here matter.

## 2. Seattle Business License — GIS layer (geometry donor)

- **Publisher:** City of Seattle ArcGIS Online (`SeattleCityGIS`), cataloged
  on `data.seattle.gov` as `wmtg-dzy4`
- **Used by:** `step3_geocode.py`, geometry only, joined by account number
- **Obtained:** manual GeoJSON download
- **License at dataset level:** none. The metadata's `license` field holds an
  accuracy *disclaimer* — "The City of Seattle makes no representation or
  warranty as to its accuracy..." — not a grant of rights, and there is no
  `licenseId`.
- **Resolved at portal level.** The Seattle Open Data Terms of Use apply "by
  using data made available through this site," without carving out
  individual datasets, and this layer is catalogued and served through
  `data.seattle.gov`. Those terms are the grant the dataset entry lacks; see
  the portal terms under source 1.
- **Attribution:** `"City of Seattle ArcGIS Online"`. The portal states
  attribution is not required.
- **Residual ambiguity, small:** the catalogue entry lives on
  `data.seattle.gov` while the file itself is served from ArcGIS Online. The
  natural reading is that a dataset reached through the portal is "made
  available through this site." If certainty is ever needed,
  `mapgis.mapgis@seattle.gov`.

## 3. Current Land Use Zoning Detail

- **Publisher:** City of Seattle ArcGIS Online (`n8h3-r7is`)
- **Used by:** `scripts/check_personal_exposure.py` only — a developer check,
  never the pipeline
- **Obtained:** ArcGIS REST query, paged at 2000, 2026-09-20
- **License:** **PDDL** — Open Data Commons Public Domain Dedication and
  License, `https://opendatacommons.org/licenses/pddl/summary`
- **Redistribution:** permitted. Moot in practice: the layer is gitignored and
  nothing derived from it is published.

## 4. Sound Transit GTFS feed

- **Publisher:** Sound Transit, Open Transit Data (OTD)
- **Used by:** `step1_stations.py` (16 station coordinates),
  `step5_map.py` (the real rail alignment, shape `N23:S07`)
- **Obtained:** manual download, feed dated `2026-08-28`
- **License:** *"Each of the Transit Agencies grant to you a limited,
  revocable license to use, and display the Data in accordance with these
  terms."* Not public domain, and revocable.
- **Attribution:** data may be identified as provided "AS IS" by the
  contributing agencies. Agency names **may not** be used "in the name of a
  business or application" — this project's name does not, so that is fine.
- **Redistribution — the clause that matters:** *"You agree to provide these
  Terms to all users who receive the Data from you"* and *"If you provide the
  Data to others, you agree to include provisions substantially similar to
  these Terms in the term of use that apply to your provision of Data to
  others."*
- **Usage metrics:** *"You agree to provide relevant usage metrics to Sound
  Transit... on request."*
- **Commercial use:** not restricted.
- **The gap, now closed:** GTFS-derived geometry is republished in
  `heatmap.html` and `outputs/`, and for a while nothing in this repository
  passed those terms on. The Methodology page's "Attribution and terms" note
  now names Sound Transit OTD as the source of the station and alignment
  geometry, links the OTD terms, and states that they travel with the data —
  which is what the flow-down clause asks for.
- **Terms read at:** `soundtransit.org/help-contacts/business-information/open-transit-data-otd/transit-data-terms-use`

## 5. Sound Transit System Performance Tracker — ridership

- **Publisher:** Sound Transit
- **Used by:** `step4_rings.py` → `station_stats.csv`; Graph 3, Graph 4,
  Table 2 and the correlation figures
- **Obtained:** **manually transcribed** from an embedded Power BI dashboard —
  screenshots of twelve 2025 months, into a document, into a CSV. No export
  endpoint exists.
- **License: resolved, and it conflicts with what this project does.** The
  dashboard is a page on `soundtransit.org`, so it is governed by Sound
  Transit's **website** Terms of Use, not the OTD Transit Data Terms. Those
  website terms state:

  > *"Sound Transit grants you a personal, royalty-free, non-assignable, and
  > non-exclusive license to use the Website Content in the United States only
  > as an informative resource. Any other use, including the reproduction,
  > modification, distribution, transmission, republication, framing, display
  > or performance of Website Content, without prior permission of Sound
  > Transit, is strictly prohibited."*

  and separately:

  > *"You may not download, print, copy, distribute, or otherwise use Website
  > Content for commercial purposes, including publication, sale, or personal
  > gain."*

  They do **not** distinguish data, statistics or reports from other content.
- **What this project does with it:** the transcribed figures are committed in
  `outputs/station_stats.csv`, rendered on the Findings page in Graph 3,
  Graph 4 and Table 2, and underpin the published r = 0.684 correlation and
  the 1.8x variance comparison. That is reproduction and republication of
  Website Content, which the terms condition on prior permission this project
  does not have.
- **Not a legal conclusion.** Whether those terms are enforceable against
  numerical facts is a real question — facts are generally not copyrightable,
  while a site's terms operate as contract, and the two do not resolve each
  other. **That judgment is not mine to make**, and nothing here should be
  read as advice. What is certain is the gap between what the page says and
  what this repository does.
- **Options, cheapest first:**
  1. **Ask.** The terms invite it: *"Sound Transit welcomes requests from
     the media or other organizations to use Website Content. Sound Transit
     must approve all uses in advance in writing."* The designated route is
     **postal, to the Marketing Division**, Union Station, 401 S. Jackson
     St., Seattle, WA 98104 — no email is given for it.
     `main@soundtransit.org` is **not** that route; the terms list it for
     intellectual-property complaints, unsubscribing, and general website
     feedback. The practical approach is to email that address asking to be
     forwarded to the Marketing Division, since it is the published channel
     for website communications, and to post the same request if a written
     reply is wanted. A non-commercial portfolio analysis citing them as the
     source is an easy case for a transit agency to approve.
  2. **Ask which terms apply.** Sound Transit may well regard published
     performance statistics as freely usable despite the blanket website
     terms, in which case a one-line answer settles it.
  3. **Re-source it.** Ridership does not appear as an OTD dataset, but
     Sound Transit publishes performance reports and responds to public
     records requests; Seattle Transit Blog obtained directional counts that
     way. Records obtained by PRR carry a different status.
  4. **Remove it.** This would cost Graph 3, Graph 4, Table 2 and one of the
     project's three analyses. Listed for completeness, not recommended
     before options 1-3 are tried.
- **Terms read at:**
  `soundtransit.org/help-contacts/business-information/terms-use`

## 6. US Census Bureau — Geocoding Services API

- **Publisher:** US Census Bureau
- **Used by:** `step3_geocode.py`, for the 1,121 rows the GIS donor missed;
  1,064 matched
- **Obtained:** batch API, cached under `data/raw/geocode_cache/`
- **License: nothing on the service itself**, but the Census Bureau publishes
  API Terms of Service covering its data APIs. Those permit use "to search,
  display, analyze, retrieve, view and otherwise 'get' information from
  Census Bureau data", place no commercial restriction, and require one
  thing this project does not currently do:

  > *"All services, which utilize or access the API, should display the
  > following notice prominently within the application: 'This product uses
  > the Census Bureau Data API but is not endorsed or certified by the Census
  > Bureau.'"*

- **Does it apply here?** Genuinely unclear. The batch geocoder at
  `geocoding.geo.census.gov` is a different endpoint from the data API those
  terms are written for, and it publishes no terms of its own. **The cheap
  move is to display the notice regardless** — it costs one line on the
  Methodology page, removes the question entirely, and is accurate either way.
- **Redistribution:** not restricted. The coordinates it returned are
  published in `heatmap.html`.
- **Copyright:** US federal government works are generally not subject to
  domestic copyright. A reason to expect no problem, still not a stated term.

## 7. OpenStreetMap — basemap tiles

- **Used by:** `step5_map.py`, as the Leaflet base layer in both light and
  dark modes
- **License:** OSM **data** is ODbL — share-alike, attribution required. Tile
  imagery is served under the OSM Foundation's tile usage policy.
- **Attribution:** present and verified — Folium emits
  `© OpenStreetMap contributors` into the map, and it renders.
- **Share-alike:** this project uses OSM as *rendered imagery underneath* its
  own data. It does not extract, derive from, or merge OSM data into
  `outputs/`, so the ODbL's share-alike condition on derived databases is not
  engaged. Recorded explicitly because "we used OSM" and "we built on the OSM
  database" are different acts with different obligations.

### The tile server is a separate question from the data license

Tiles come from `https://tile.openstreetmap.org/{z}/{x}/{y}.png` — the OSM
Foundation's own servers — so the **Tile Usage Policy** applies on top of
ODbL. It is explicit that availability is best-effort with no SLA, and it
forbids bulk or pre-emptive downloading. Checked 2026-09-20:

- **Attribution is visibly rendered, not just present in the source.** The
  control measures 197x14px and reads "Leaflet | © OpenStreetMap
  contributors", linking `openstreetmap.org/copyright`. Contrast is 12.6:1
  in light mode and 6.6:1 in dark — the dark restyle lightens it rather than
  letting the tile filter wash it out.
- **No pre-emptive fetching.** A page load requests 15 tiles, which is the
  visible viewport. The map draws only what a visitor looks at.
- **Dark mode does not double tile load**, which is the one thing this
  project's own implementation could have gotten wrong. Both base layers
  point at the same URLs, and only one is attached to the map at a time.
  Measured: toggling to dark produced **0 new network requests**, all 15
  tiles served from cache.
- **Not near the policy's limits.** Its concerns are bulk downloading, heavy
  commercial traffic, and clients that suppress a User-Agent or Referer. A
  portfolio site rendering a viewport per visit is ordinary use. This project
  has already met the Referer enforcement once, in the other direction: a
  downloadable copy of the map 403'd because a `file://` page sends no
  Referer, and the download button was removed rather than worked around.
- **The real exposure is availability, not compliance.** No SLA means an OSM
  outage or policy change breaks the basemap. The Session 7 decision to use
  OSM — after CartoDB began requiring an API key and Esri's license proved
  unstable — is recorded in `DECISIONS.md` and still holds; a self-hosted or
  keyed provider would only be worth it if this ever carried real traffic.

## 8. Seattle Transit Blog directional boardings — not used

Referenced in `data/raw/README.md` as an optional extra and **never
incorporated**. Obtained by that blog via public records request. No terms
reviewed, because nothing from it reaches this project.

---

## What to do about it

Ordered by how much it matters. Items 1-3 were the three open questions at
first writing; all three are now answered, and two produced actions.

1. **Decide what to do about the ridership figures (source 5).** This is the
   only item where what a source says and what this project does are in
   conflict. Options are listed in that entry; asking is the cheapest.
2. **Add the Census API notice.** One line on the Methodology page: "This
   product uses the Census Bureau Data API but is not endorsed or certified
   by the Census Bureau." Whether it is strictly required here is unclear,
   which is exactly why adding it is easier than deciding.
3. **Pass Sound Transit's GTFS terms on.** *Done* — the Methodology page's
   "Attribution and terms" note carries them, discharging the flow-down
   clause for the station and alignment geometry.
4. **Keep the non-commercial condition in view.** Seattle's portal terms bar
   commercial use of data that can be configured as a list of individuals,
   which this data can. A portfolio is not a commercial purpose; monetising
   the project later would change that.
5. **Re-check on any refresh.** The business license dataset refreshes daily,
   the City may discontinue a dataset without notice, and terms change. This
   log is a snapshot of 2026-09-20.

## Checking these again

Socrata states license terms per dataset in machine-readable metadata, which
is faster and more reliable than reading the portal page — the human-facing
page for `wnbq-64tb` shows nothing useful, while its metadata states the
license outright:

```
https://data.seattle.gov/api/views/<dataset-id>.json
```

Read `license`, `licenseId`, `attribution`, `attributionLink` and
`custom_fields`. ArcGIS feature services expose `copyrightText` and
`licenseInfo` at `<service-url>?f=json`, though Seattle's zoning service
leaves both empty — its license is only in the Socrata catalog entry.
