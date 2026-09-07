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

## Working with this user

Introductory Python, no GIS background. Explain geospatial concepts as they
come up rather than only producing working code.

Do not write the prose in the `TODO — write this up` blocks in
`pages/2_Findings.py`. That analysis is the user's and is the point of the
project. Discuss the numbers with them; let them write the interpretation.

Scope is locked (see `initialscript.md`). Flag scope additions rather than
building them.

## Commands

```bash
source .venv/bin/activate
python src/step1_stations.py    # then 2, 3, 4, 5 in order
streamlit run app.py
```

Commit after each step that succeeds. Prompt the user to fill in
`DECISIONS.md` after each session.
