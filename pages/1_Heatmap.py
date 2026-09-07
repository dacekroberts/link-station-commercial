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
    components.html(HEATMAP_HTML.read_text(), height=700, scrolling=False)
    st.download_button(
        "Download the map",
        data=HEATMAP_HTML.read_text(),
        file_name="heatmap.html",
        mime="text/html",
    )
else:
    st.info("No map yet. Run `python src/step5_map.py` to generate it.")
