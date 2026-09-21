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
| Seattle business licenses (CSV) | **Public Domain** | permitted | clear |
| Seattle Business License (GIS layer) | *disclaimer only, no grant* | not stated | **gap** |
| Seattle land use zoning | **PDDL** | permitted | clear (not redistributed) |
| Sound Transit GTFS | limited, **revocable** | permitted **with flow-down** | **action needed** |
| Sound Transit ridership dashboard | not stated for this surface | not stated | **unresolved** |
| US Census geocoder | not stated on the service | not stated | **gap** |
| OpenStreetMap tiles | ODbL (data), attribution required | see entry | attribution present |

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

## 2. Seattle Business License — GIS layer (geometry donor)

- **Publisher:** City of Seattle ArcGIS Online (`SeattleCityGIS`), catalogued
  on `data.seattle.gov` as `wmtg-dzy4`
- **Used by:** `step3_geocode.py`, geometry only, joined by account number
- **Obtained:** manual GeoJSON download
- **License:** **none stated.** The metadata's `license` field holds an
  accuracy *disclaimer* — "The City of Seattle makes no representation or
  warranty as to its accuracy..." — not a grant of rights. There is no
  `licenseId`.
- **Attribution:** `"City of Seattle ArcGIS Online"`
- **Redistribution:** not addressed.
- **Gap.** This is the same underlying business data as source 1, published by
  the same city, marked `Public Access Level: public`. Those are reasons to
  expect permissive terms; they are not the permissive terms themselves. The
  coordinates it donated are published in `heatmap.html`. Worth an email to
  `mapgis.mapgis@seattle.gov` if certainty is wanted.

## 3. Current Land Use Zoning Detail

- **Publisher:** City of Seattle ArcGIS Online (`n8h3-r7is`)
- **Used by:** `scripts/check_personal_exposure.py` only — a developer check,
  never the pipeline
- **Obtained:** ArcGIS REST query, paged at 2000, 2026-09-20
- **License:** **PDDL** — Open Data Commons Public Domain Dedication and
  License, `https://opendatacommons.org/licenses/pddl/summary`
- **Redistribution:** permitted. Moot in practice: the layer is gitignored and
  nothing derived from it is published.

## 4. Sound Transit GTFS feed — needs action

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
- **The gap:** GTFS-derived geometry is republished in `heatmap.html` and
  `outputs/`, and **nothing in this repository passes those terms on.** That
  is a flow-down obligation the project currently does not meet. Closing it is
  cheap: a short terms note naming Sound Transit OTD as the source of the
  station and alignment geometry, linking the OTD terms, in the Methodology
  page's Data Sources section and/or this repository's README.
- **Terms read at:** `soundtransit.org/help-contacts/business-information/open-transit-data-otd/transit-data-terms-use`

## 5. Sound Transit System Performance Tracker — ridership

- **Publisher:** Sound Transit
- **Used by:** `step4_rings.py` → `station_stats.csv`; Graph 3, Graph 4,
  Table 2 and the correlation figures
- **Obtained:** **manually transcribed** from an embedded Power BI dashboard —
  screenshots of twelve 2025 months, into a document, into a CSV. No export
  endpoint exists.
- **License: unresolved.** The dashboard is a public web page on
  `soundtransit.org`, not a dataset on the OTD portal. Whether the OTD
  "Transit Data Terms of Use" reach it is genuinely unclear: those terms
  govern *"the Data"* made available through OTD, and this was read off a
  reporting surface instead.
- **Why this one was checked first:** every other source is a published export
  designed for reuse. This is the only one obtained by reading a rendered
  dashboard by hand, and it is also the source behind the site's most
  prominent secondary figures.
- **To close:** ask Sound Transit directly which terms cover the System
  Performance Tracker's published figures. `main@soundtransit.org`, or the OTD
  contact.

## 6. US Census Bureau — Geocoding Services API

- **Publisher:** US Census Bureau
- **Used by:** `step3_geocode.py`, for the 1,121 rows the GIS donor missed;
  1,064 matched
- **Obtained:** batch API, cached under `data/raw/geocode_cache/`
- **License: not stated on the service.** `geocoding.geo.census.gov` publishes
  no terms-of-use, license or attribution requirement on the geocoder itself;
  it links only to privacy, information-quality and accessibility policies.
- **Redistribution:** not addressed. The coordinates it returned are published
  in `heatmap.html`.
- **Note:** US federal government works are generally not subject to domestic
  copyright, which is a reason to expect this to be unproblematic. As above,
  that is an expectation, not a stated term. Recorded as a gap rather than
  resolved.

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

## 8. Seattle Transit Blog directional boardings — not used

Referenced in `data/raw/README.md` as an optional extra and **never
incorporated**. Obtained by that blog via public records request. No terms
reviewed, because nothing from it reaches this project.

---

## What to do about it

Ordered by how much it matters:

1. **Pass Sound Transit's terms on.** A short attribution-and-terms note
   naming OTD as the source of the station and alignment geometry, linking
   their terms. This is a stated obligation the project does not currently
   meet, and it is the cheapest to fix.
2. **Resolve the ridership dashboard's terms** by asking, since they cannot be
   determined by reading.
3. **Ask about the GIS donor layer**, or note in the methodology that its
   terms are a disclaimer rather than a grant.
4. **Add source attribution to the site.** The Methodology page's Data Sources
   section names the sources but credits none of them in the form their
   publishers ask for.
5. **Re-check on any refresh.** The business license dataset refreshes daily
   and its terms could change; this log is a snapshot of 2026-09-20.

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
leaves both empty — its license is only in the Socrata catalogue entry.
