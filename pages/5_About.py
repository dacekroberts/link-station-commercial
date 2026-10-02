"""About page: who built this project and why.

Personal material lives here rather than in the Overview's "Why Seattle?"
and "Starting Assumptions" sections, which stay about the city and the
argument. The prose is the author's own; reword it only with their
approval.
"""

import streamlit as st

from components import (
    render_sidebar_nav_label,
    render_social_links,
    set_base_font,
    set_sidebar_width,
)

st.set_page_config(page_title="About", page_icon="👤", layout="wide")

set_base_font()
set_sidebar_width()
render_sidebar_nav_label()
render_social_links()

st.title("About")

st.subheader("Background")
st.markdown(
    """
Seattle is where I was born, raised, and have become accustomed to, and
that familiarity is part of why I chose it for this case study. I am
currently based in the Seattle area.
"""
)

st.subheader("Education")
st.markdown(
    """
I studied Philosophy, Politics and Economics (PPE) at the University of
Southern California (USC), graduating in 2025. Through my
relevant education and research, particularly my collegiate Urban
Economics and Philosophy of Economics courses, I formed the starting
assumptions this project is built on. Previously, I obtained a Python
course certification from Noble Desktop in 2024, and before starting this
project, I completed five Skilljar courses on Claude Code over about a
month.
"""
)

st.subheader("What I'm Looking For")
st.markdown(
    """
I'm looking for roles in data analytics, particularly ones built on
exploratory data analysis and the insights it draws out of data. This
project reflects the other half of that work too: presenting data and
findings in a way a general audience can digest. After my experiences at
two AI-centric startups, AI has become integral to my workflow, as this
project's own development shows. The GitHub and LinkedIn links at the top
of every page are the best way to reach me.
"""
)

st.subheader("Why This Project")
st.markdown(
    """
After studying urban density and transit in my PPE coursework, I felt
compelled to drive an investigation into the commercial opportunities one
could find near newly established transit hubs in a built-out urban
environment. Seattle, with its rapid growth and a Link light rail network
that has expanded significantly this decade, offered the right setting to
start.
"""
)

st.subheader("Skills This Project Demonstrates")
st.markdown(
    """
- **Geospatial analysis:** GeoPandas, Shapely and pyproj; projecting to a
  meter-based coordinate system (EPSG:32610) before measuring distance;
  concentric-ring buffers built as annuli; spatial joins.
- **Data sourcing and cleaning:** City of Seattle business-license and GIS
  data, Sound Transit's GTFS feed, and the U.S. Census geocoder as a
  fallback; NAICS filtering, brand normalization, and counting distinct
  locations rather than license records.
- **Statistics:** density gradients, Pearson and Spearman correlation,
  coefficients of variation, z-scores, and leverage checks on outliers.
- **Visualization:** an interactive Folium/Leaflet heatmap on
  OpenStreetMap tiles, with layer controls, marker clustering and a dark
  mode; Altair charts; a Mermaid
  flowchart.
- **Web app and deployment:** a multipage Streamlit site on Streamlit
  Community Cloud, with a lean deploy kept separate from the pipeline's
  geospatial stack.
- **Reproducibility and quality checks:** a five-step pipeline with
  committed outputs, plus scripts that verify every published figure
  against the data and screen the map for personal names before it's
  published.
- **Data ethics and licensing:** a source-by-source license review, and
  withholding names where a sole proprietor's business name is their own.
- **AI-assisted development:** built with Claude Code, with the analysis
  and its judgment calls kept as my own.
"""
)
