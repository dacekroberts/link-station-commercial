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
from config import HEATMAP_HTML, LICENSE_SNAPSHOT, RING_EDGES_MILES

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
    "**Pick a station and see how many shops, restaurants and services sit "
    "within a short walk of the platform.**"
)

# The map sits directly under the purpose line so it is on screen when the
# page opens; the tasks and the control notes follow it.
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
    # Required wherever the station boardings figure is shown (permission
    # terms recorded in docs/data_sources.md, source 5).
    st.caption("Ridership: Sound Transit System Performance Tracker, 2025.")
else:
    st.info("No map yet. Run `python src/step5_map.py` to generate it.")

# Short tasks that each use a control already on the map. Rendered twice
# and switched by CSS at Streamlit's 640px column breakpoint: a plain list
# on wide screens, a collapsed expander on phones to keep the page short. Layer names quoted here must match step5_map.py.
TRY_HEADING = "Four things to try"
TRY_LIST = """
1. **Compare two stations.** Zoom in on Westlake, then on Othello, and
   compare the numbered circles inside the innermost ring at each.
2. **Filter to one kind of business.** Open the layer control (top left)
   and untick Retail and Personal services so only Food service is left.
   Follow the line south and see where the restaurants thin out.
3. **Check a station's foot traffic.** Hover over (or tap) any blue station
   dot to see its average monthly boardings, then look at how many
   storefronts surround it.
4. **Compare with the rest of the city.** Tick "Commercial Density (All
   Seattle Businesses)" to see how the station areas compare with
   everywhere else.
"""
st.markdown(
    """
    <style>
    @media (max-width: 640px) { .st-key-try_wide { display: none; } }
    @media (min-width: 641px) { .st-key-try_narrow { display: none; } }
    </style>
    """,
    unsafe_allow_html=True,
)
with st.container(key="try_wide"):
    st.markdown(f"**{TRY_HEADING}**\n{TRY_LIST}")
with st.container(key="try_narrow"):
    with st.expander(TRY_HEADING):
        st.markdown(TRY_LIST)

# Ring distances and the snapshot date come from config.py so these notes
# cannot drift from the pipeline. Colours named here match NAICS_GROUPS in
# step5_map.py.
_inner = ", ".join(f"{m:g}" for m in RING_EDGES_MILES[1:-1])
_outer = f"{RING_EDGES_MILES[-1]:g}"
with st.expander("How to read this map"):
    st.markdown(
        f"""
- **Blue dots** are the 16 stations. Hover over one (or tap it) to see its
  average monthly boardings.
- **Thin circles** mark {_inner} and {_outer} miles from each station.
- **Coloured dots** are single businesses: blue for retail, pink for food
  service, green for personal services. Hover over one to see its name,
  category, nearest station and ring.
- **Numbered circles** are nearby businesses added together. Each colour is
  counted separately, so a station's total is the sum of its circles, not
  any single one.
- **The orange glow** shows roughly where businesses bunch up. Both the
  glow and the numbered circles change as the map zooms, so compare two
  stations at the same zoom level.

Only businesses within {_outer} miles of a station are pinned. A few pins
read "Name withheld (sole proprietor)": the business is real, but the name
is a person's own.
"""
    )
with st.expander("Where to trust it, and where not"):
    st.markdown(
        f"""
**Good for:** seeing where shops, restaurants and services cluster around
each station, which kinds are there, and how one station compares with
another.

**Not good for:**

- **Whether a place is open today.** The licence list is a snapshot from
  {LICENSE_SNAPSHOT}, so closures and openings since then don't show.
- **Whether a pin is a shopfront.** The list records registered businesses,
  so a home-based business looks the same as a shop on the street.
- **How far the walk is.** The rings are straight-line distances. A
  freeway, a hill or water inside a ring is ignored.
- **How many people walk past.** Boardings count people getting on the
  train, including those who arrive by bus or car and never pass a
  storefront.
- **What could open here.** Zoning is not accounted for.

Each of these is covered in full on:
"""
    )
    st.page_link(
        "pages/3_Methodology_&_Limitations.py",
        label="Methodology & Limitations",
        icon=":material/arrow_forward:",
    )

st.markdown(
    f"""
<b>Concentric ring boundaries and NAICS/GIS geocoded storefronts are
toggleable via the layer control in the top left, and the button beneath
it switches between light and dark mode.</b> <img src="{LAYER_CONTROL_ICON_DATA_URI}" width="18"
height="18" style="vertical-align: middle;" alt="Layer control icon"/>

The heat layer is illustrative. Leaflet applies a visual blur rather than a
statistical density estimate, so read the color as "roughly where things
cluster" and take the numbers from the findings page.
""",
    unsafe_allow_html=True,
)

# Closing bridge to the follow-on project. The city count is that project's
# figure (given by the author, 2026-10-12), not derivable from outputs/; it
# is listed under NOT_CHECKED in scripts/check_published_numbers.py. No link
# yet: add one here when that project has a public address.
st.divider()
st.markdown(
    "**The same map, in 237 cities.** Storefronts Near Transit applies this "
    "method to other transit systems."
)

render_footer()
