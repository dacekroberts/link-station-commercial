# Motion sources

How the outside data in the motion opener films was made. This folder holds
only that: scripts and notes for material that appears in the films and
nowhere else. Nothing here is read by the site or the pipeline, and no
published figure comes from it.

The films themselves and the data these scripts write stay outside git, in
`visuals/`.

| File | What it does |
|---|---|
| `fetch_buildings.py` | Fetches OpenStreetMap building outlines within half a mile of the 1 Line (Northgate to Rainier Beach) through the Overpass API, then filters and simplifies them for the films' drawn city. |

## Why this is public

The building outlines are data taken from the OpenStreetMap database and
then adapted. The Open Database License asks that the adapted data, or the
method that made it, be available when a work built from it is shown
publicly. This script is the method. The adapted files (8,000 simplified
outlines along the line, 879 around Westlake) are available on request.

Credit wherever the outlines are drawn: **© OpenStreetMap contributors**
(Open Database License).

## Running it

From the repo root, with the pipeline environment
(`requirements-pipeline.txt`) and the local `data/` tree in place:

```
python motion_sources/fetch_buildings.py
```

Each source's terms are recorded under source 9 in `docs/data_sources.md`.
