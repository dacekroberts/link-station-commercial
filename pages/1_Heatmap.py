"""Heatmap page - embeds the pre-rendered Folium HTML.

Reading the saved file as a raw component is faster than re-rendering the
map through streamlit-folium, and avoids pulling folium into the deployed
app's dependencies. Switch to st_folium only if you later want click and
pan events flowing back into Python.
"""

import streamlit as st
import streamlit.components.v1 as components

from config import HEATMAP_HTML

st.set_page_config(page_title="Heatmap", page_icon="🗺️", layout="wide")

st.title("Commercial density around station areas")

st.markdown(
    """
Each point is a licensed business in a storefront category. Circles mark the
ring boundaries; toggle them in the layer control at the top right.

The heat layer is illustrative. Leaflet applies a visual blur rather than a
statistical density estimate, so read the colour as "roughly where things
cluster" and take the numbers from the findings page.
"""
)

if HEATMAP_HTML.exists():
    # folium always saves this file as UTF-8. On Windows, Path.read_text()
    # without an explicit encoding falls back to the OS codepage (cp1252),
    # which mangles every multi-byte character (em dashes in particular) -
    # not a bug in the saved file, only in how it's read back here.
    heatmap_html = HEATMAP_HTML.read_text(encoding="utf-8")
    # Matches the Folium map's own fixed pixel size (width=1000, height=650
    # in step5_map.py) exactly - the iframe previously had no explicit width
    # (defaulting to the full page container, wider than the 1000px map) and
    # a taller height=700 than the map's own 650, leaving dead white space
    # to the right and below the map itself. scrolling stays on as a safety
    # net against a stray pixel of overflow, not because it's expected to
    # trigger.
    components.html(heatmap_html, width=1000, height=650, scrolling=True)
    st.download_button(
        "Download the map",
        data=heatmap_html,
        file_name="heatmap.html",
        mime="text/html",
    )
else:
    st.info("No map yet. Run `python src/step5_map.py` to generate it.")
