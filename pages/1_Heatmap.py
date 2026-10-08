"""Heatmap page: embeds the pre-rendered Folium HTML.

An iframe of the saved file is faster than re-rendering the map through
streamlit-folium and keeps folium out of the deployed app's dependencies.
Switch to st_folium only if click and pan events need to flow back into
Python.
"""

import streamlit as st

from components import (
    render_footer,
    render_sidebar_nav_label,
    render_social_links,
    render_train_banner,
    set_base_font,
    set_sidebar_width,
)
from config import HEATMAP_HTML

# The embedded map's own Leaflet layer-control icon
# (leaflet@1.9.3/dist/images/layers.png, 26x26), inlined as a data URI so
# the page makes no external request, like render_social_links()'s icons.
LAYER_CONTROL_ICON_DATA_URI = (
    "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABoAAAAaCAQAAAADQ4RFAAACf0lEQVR4AY1U"
    "M3gkARTePdvdoTxXKc+qTl3aU5U6b2Kbkz3Gtq3Zw6ziLGNPzrYx7946Tr6/ee/XeCQ4D3ykPtL5tHno4n0d"
    "/h3+xfuWHGLX81cn7r0iTNzjr7LrlxCqPtkbTQEHeqOrTy4Yyt3VCi/IOB0v7rVC7q45Q3Gr5K6jt+3Gl5nC"
    "oDD4MtO+j96Wu8atmhGqcNGHObuf8OM/x3AMx38+4Z2sPqzCxRFK2aF2e5Jol56XTLyggAMTL56XOMoS1W4"
    "pOyjUcGGQdZxU6qRh7B9Zp+PfpOFlqt0zyDZckPi1ttmIp03jX8gyJ8a/PG2yutpS/Vol7peZIbZcKBAEEhe"
    "EIAgFbDkz5H6Zrkm2hVWGiXKiF4Ycw0RWKdtC16Q7qe3X4iOMxruonzegJzWaXFrU9utOSsLUmrc0YjeWYj"
    "CW4PDMADElpJSSQ0vQvA1Tm6/JlKnqFs1EGyZiFCqnRZTEJJJiKRYzVYzJck2Rm6P4iH+cmSY0YzimYa8l0"
    "EtTODFWhcMIMVqdsI2uiTvKmTisIDHJ3od5GILVhBCarCfVRmo4uTjkhrhzkiBV7SsaqS+TzrzM1qpGGUF"
    "u28pIySQHR6h7F6KSwGWm97ay+Z+ZqMcEjEWebE7wxCSQwpkhJqoZA5ivCdZDjJepuJ9IQjGGUmuXJdBFU"
    "ygxVqVsxFsLMbDe8ZbDYVCGKxs+W080max1hFCarCfV+C1KATwcnvE9gRRuMP2prdbWGowm1KB1y+zwMME"
    "NkM755cJ2yPDtqhTI6ED1M/82yIDtC/4j4BijjeObflpO9I9MwXTCsSX8jWAFeHr05WoLTJ5G8IQVS/7vw"
    "R6ohirYM7f6HzYpogfS3R2OAAAAAElFTkSuQmCC"
)

st.set_page_config(page_title="Heatmap", page_icon="🗺️", layout="wide")

set_base_font()
set_sidebar_width()
render_sidebar_nav_label()
render_train_banner("heatmap")
render_social_links()

st.title("Commercial density around station areas")

st.markdown(
    f"""
Stations are represented by blue dots along the 1 Line (thick green line).
<u>Concentric ring boundaries and NAICS/GIS geocoded storefronts are
toggleable via the layer control in the top left, and the button beneath
it switches between light and dark mode.</u> <img src="{LAYER_CONTROL_ICON_DATA_URI}" width="18"
height="18" style="vertical-align: middle;" alt="Layer control icon"/> When
enabled, business density will display as numbered circles summing areas
when zoomed out. Zooming in will show individual dots; hover over those to
see further details.

The heat layer is illustrative. Leaflet applies a visual blur rather than a
statistical density estimate, so read the color as "roughly where things
cluster" and take the numbers from the findings page.
""",
    unsafe_allow_html=True,
)

if HEATMAP_HTML.exists():
    # st.iframe, not the deprecated st.components.v1.html (removal announced
    # for 2026-06-01). It reads the Path itself as UTF-8. Don't swap in
    # Path.read_text() without encoding=: on Windows it falls back to cp1252
    # and mangles multi-byte characters, such as the em dashes in the layer
    # names.
    #
    # width=1000, height=650 match the Folium map's fixed pixel size in
    # step5_map.py (fixed there for the Leaflet.heat init-race fix). A wider
    # or taller iframe leaves dead white space right of and below the map;
    # change both files together. The browser's default scrolling (auto)
    # covers a stray pixel of overflow.
    st.iframe(HEATMAP_HTML, width=1000, height=650)
else:
    st.info("No map yet. Run `python src/step5_map.py` to generate it.")

render_footer()
