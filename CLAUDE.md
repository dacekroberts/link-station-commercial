# Project conventions

Seattle Link light rail / commercial density analysis. Full context in
`initialscript.md` — read it at the start of a new session. Working plan in
`PLAN.md`.

## Invariants

- **Never buffer or measure distance in EPSG:4326.** Project to EPSG:32610
  (metres), do the geometry, project back to 4326 for display.
- **Keep `requirements.txt` lean** (streamlit, pandas only). Streamlit Cloud
  installs from it; geopandas there breaks the deploy. Pipeline dependencies
  go in `requirements-pipeline.txt`.
- **`outputs/` is committed to git.** The deployed app cannot regenerate it.
- **Rings are annuli** — each subtracts the disc inside it. Without that the
  gradient is meaningless.
- Pipeline writes `outputs/`; the Streamlit app only reads it. Nothing else
  crosses that boundary.
- **Business-license data:** the CSV (`business_licenses.csv`) is canonical for
  every analysis. The GIS layer (`business_licenses_geocoded.geojson`) is a
  geometry donor only — joined by account number in step 3. Do not swap the
  pipeline to the GIS layer as its primary source (it hides a ~10% coverage
  gap). See `DECISIONS.md`.

## Working with this user

Introductory Python, no GIS background. Explain geospatial concepts as they
come up rather than only producing working code.

Do not write the prose in the `TODO — write this up` blocks in
`pages/2_Findings.py`. That analysis is the user's and is the point of the
project. Discuss the numbers with them; let them write the interpretation.

Scope is locked (see `initialscript.md`). Flag scope additions rather than
building them.

## Commands

Venv is `.venv` on Python 3.12 (system Python is 3.14, too new for the geo
wheels). Built with `uv`; plain `venv`/`pip` is equivalent.

```powershell
.venv\Scripts\Activate.ps1        # Windows; macOS/Linux: source .venv/bin/activate
python src/step1_stations.py      # then 2, 3, 4, 5 in order
streamlit run Introduction.py
```

Commit after each step that succeeds. Prompt the user to fill in
`DECISIONS.md` after each session.
