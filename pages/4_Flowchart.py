"""Flowchart page - how the pipeline actually got built.

Renders via Mermaid loaded from a CDN inside an iframe component, not a new
pip dependency - keeps requirements.txt lean (see CLAUDE.md). Diagram
content is drawn from Sessions 1-7 Context.md and the src/step*.py scripts,
not hardcoded from memory.
"""

import streamlit as st
import streamlit.components.v1 as components

from components import render_social_links, set_base_font, set_sidebar_width

st.set_page_config(page_title="Flowchart", page_icon="🔀", layout="wide")

set_base_font()
set_sidebar_width()
render_social_links()

st.title("Flowchart")

st.markdown(
    """
This page exists so you can see how this project actually got built, not
just the finished result. A data pipeline looks clean once it's done, but
this one had real dead ends and real bugs along the way, and I wanted a
couple of the more interesting ones visible here instead of buried in a
decisions log.

The diagram below follows the same five-step pipeline used throughout this
project, starting from the manual data downloads and ending at the
Streamlit app you're looking at right now. Two of the pipeline's real
pivot points are called out directly: a bug in how I first defined a
"chain" business that would have overstated the true figure by more than
five times had a required hand-verification step not caught it, and a
string of basemap problems that forced three separate fixes before the
heatmap page actually rendered correctly.
"""
)

# Mermaid loaded from a CDN inside an iframe, not st.graphviz_chart - keeps
# requirements.txt at streamlit/pandas/altair rather than adding a new pip
# dependency for one diagram. Fixed height with scrolling=True, same
# workaround as the heatmap embed above (percentage-sized iframes have
# already caused one real rendering bug in this project - see
# step5_map.py's Leaflet.heat fix).
_MERMAID_SOURCE = """
flowchart TD
    subgraph INPUTS["Manual data collection"]
        GTFS[/GTFS feed<br/>Sound Transit Open Data/]
        LIC[/business_licenses.csv<br/>84,390 rows, City of Seattle/]
        GIS[/GIS geocoded layer<br/>geometry donor only/]
        RID[/Ridership dashboard<br/>12 months, hand-transcribed/]
    end

    GTFS --> S1["step1_stations.py<br/>Extract 16 station coordinates"]
    LIC --> S2["step2_clean_businesses.py<br/>Filter Seattle + NAICS, dedupe"]
    S2 --> S3["step3_geocode.py<br/>GIS donor join + Census fallback"]
    GIS --> S3
    S3 --> GEO[("11,409 geocoded<br/>businesses")]
    S1 --> S4["step4_rings.py<br/>Buffer rings, spatial join,<br/>3 analyses"]
    GEO --> S4
    RID --> S4

    S4 --> DCHAIN{"'Chain' defined as<br/>station_count > 1 -<br/>does hand-verification hold up?"}
    DCHAIN -- "no - single location<br/>touching 4 stations isn't a chain" --> FIX["Redefine as location_count >= 2<br/>(45.7% -> 8.5% of locations)"]
    FIX --> OUT[("outputs/*.csv<br/>committed to git")]

    S1 --> S5["step5_map.py<br/>Build heatmap"]
    GEO --> S5
    S5 --> DBASE{"Basemap + heat layer<br/>work on the first try?"}
    DBASE -- "no - CartoDB needs an API key,<br/>Esri's license is unstable,<br/>Leaflet.heat silently crashes the map" --> HFIX["OpenStreetMap tiles +<br/>fixed pixel map dimensions"]
    HFIX --> MAP[("heatmap.html")]

    OUT --> APP["Streamlit app<br/>reads outputs/ only"]
    MAP --> APP
    APP --> PAGES["4 pages:<br/>Intro &middot; Heatmap &middot; Findings &middot; Methodology"]
"""

_FLOWCHART_HTML = f"""
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
<style>
  html, body {{
    margin: 0;
    padding: 0;
    background: #0e1117;
  }}
  .wrap {{
    overflow-x: auto;
    padding: 12px 4px;
    border: 1px solid #30363d;
    border-radius: 10px;
    box-sizing: border-box;
  }}
  .mermaid {{
    display: flex;
    justify-content: center;
  }}
</style>
</head>
<body>
<div class="wrap">
  <div class="mermaid">
{_MERMAID_SOURCE}
  </div>
</div>
<script>
  mermaid.initialize({{ startOnLoad: true, theme: "dark", securityLevel: "loose",
    flowchart: {{ useMaxWidth: false, htmlLabels: true }} }});

  // Mermaid renders the SVG async after startOnLoad, so poll for it rather
  // than hooking a callback - v10's promise-based mermaid.run() API isn't
  // used here since startOnLoad already triggers its own render pass.
  // Scaling the SVG's own width/height attributes (not a CSS transform)
  // shrinks the box it occupies in the page too, so there's no leftover
  // blank space below the diagram at the smaller size.
  const _scaleInterval = setInterval(() => {{
    const svg = document.querySelector(".mermaid svg");
    if (!svg) return;
    clearInterval(_scaleInterval);
    const w = svg.width.baseVal.value;
    const h = svg.height.baseVal.value;
    svg.setAttribute("width", w * 0.75);
    svg.setAttribute("height", h * 0.75);
  }}, 100);
</script>
</body>
</html>
"""

components.html(_FLOWCHART_HTML, height=940, scrolling=True)
