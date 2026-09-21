"""Flowchart page - how the pipeline actually got built.

Renders via Mermaid loaded from a CDN inside an iframe, not a new pip
dependency - keeps requirements.txt lean (see CLAUDE.md). Diagram content is
drawn from DECISIONS.md, the local build-context notes, and the
src/step*.py scripts, not hardcoded from memory.
"""

import base64

import streamlit as st

from components import (
    render_sidebar_nav_label,
    render_social_links,
    set_base_font,
    set_sidebar_width,
)

st.set_page_config(page_title="Flowchart", page_icon="🔀", layout="wide")

set_base_font()
set_sidebar_width()
render_sidebar_nav_label()
render_social_links()

st.title("Flowchart")

st.markdown(
    """
This flowchart is for site visitors to understand how this project
actually got built, not just the finished result. A data pipeline looks
clean once it's done, but this one had dead ends and bugs along the way,
and I wanted a couple of the more interesting ones visible here.

The diagram below follows a five-step pipeline used throughout this
project, starting from the manual data downloads and ending at the
Streamlit app you're looking at right now. Two of the pipeline's real
pivot points are called out directly in the corresponding diamond shapes.
This version is intentionally simplistic for accessibility, beyond this
visual more decisions and workflow items went into this project.
"""
)

# Mermaid loaded from a CDN inside an iframe, not st.graphviz_chart - keeps
# requirements.txt at streamlit/pandas/altair rather than adding a new pip
# dependency for one diagram. Fixed pixel height, same workaround as the
# heatmap embed (percentage-sized iframes have already caused one real
# rendering bug in this project - see step5_map.py's Leaflet.heat fix).
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
    DCHAIN -- "no - single location<br/>touching 4 stations isn't a chain" --> FIX["Redefine as location_count >= 2<br/>(45.5% -> 8.5% of locations)"]
    FIX --> OUT[("outputs/*.csv<br/>committed to git")]

    S1 --> S5["step5_map.py<br/>Build heatmap"]
    GEO --> S5
    S5 --> DBASE{"Basemap + heat layer<br/>work on the first try?"}
    DBASE -- "no - CartoDB needs an API key,<br/>Esri's license is unstable,<br/>Leaflet.heat silently crashes the map" --> HFIX["OpenStreetMap tiles +<br/>fixed pixel map dimensions"]
    HFIX --> MAP[("heatmap.html")]

    OUT --> APP["Streamlit app<br/>reads outputs/ only"]
    MAP --> APP
    APP --> PAGES["5 pages:<br/>Intro &middot; Heatmap &middot; Findings &middot;<br/>Methodology &middot; Flowchart"]
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
    background: #171412;
  }}
  .wrap {{
    overflow-x: auto;
    padding: 12px 4px;
    border: 1px solid #3A322B;
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
  // "base" theme with warm-charcoal variables (matching .streamlit/config.toml),
  // not Mermaid's built-in "dark", which is a cool gray-blue that clashes with
  // the site's warm background.
  mermaid.initialize({{ startOnLoad: true, theme: "base", securityLevel: "loose",
    themeVariables: {{
      background: "#171412",
      primaryColor: "#2A231E",
      primaryTextColor: "#F3EDE6",
      primaryBorderColor: "#F0801F",
      secondaryColor: "#221D19",
      tertiaryColor: "#1D1916",
      lineColor: "#A39A90",
      textColor: "#F3EDE6",
      clusterBkg: "#1D1916",
      clusterBorder: "#3A322B",
      edgeLabelBackground: "#171412"
    }},
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
    svg.setAttribute("width", w * 0.6);
    svg.setAttribute("height", h * 0.6);
  }}, 100);
</script>
</body>
</html>
"""

# st.iframe, not the deprecated st.components.v1.html (removal was
# announced for 2026-06-01). st.iframe takes a src rather than an HTML
# string, so this document goes in as a base64 data: URL - it is generated
# here in Python, not saved anywhere on disk. st.html would take the string
# directly but renders it INLINE rather than in an iframe: tested, and this
# document's `html, body { background: ... }` rule and Mermaid's own
# injected styles then leak out into the Streamlit page itself. The iframe
# keeps them contained, and Mermaid still loads from its CDN inside it.
#
# Scale (0.6) and height (905) chosen together, live-tested in the
# rendered DOM: at 0.6 the diagram's own content is ~899px tall, fitting
# inside 905px with a small margin - large enough that no scrollbar
# appears at all (905 was previously 940, sized for the old 0.75 scale).
_FLOWCHART_DATA_URL = "data:text/html;base64," + base64.b64encode(
    _FLOWCHART_HTML.encode("utf-8")
).decode("ascii")
st.iframe(_FLOWCHART_DATA_URL, width="stretch", height=905)
