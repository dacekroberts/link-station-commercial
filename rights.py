"""Rights notices: the owner credit and the machine-readable rights tags.

Kept out of config.py on purpose. Streamlit Community Cloud keeps
already-imported modules in memory across a redeploy, so pages that import
a name newly added to config.py fail with ImportError until the app is
rebooted. A module that did not exist before the deploy has no stale copy.
"""

# One source for the owner credit drawn inside figures and for the
# machine-readable rights tags in the HTML this project writes itself (the
# map and the flowchart document). Streamlit owns each page's <head>, so
# page-level tags are not possible there; the visible footer in
# components.py covers the pages. Third-party data is not claimed: its
# terms are in docs/data_sources.md.
RIGHTS_HOLDER = "Dace Roberts"
RIGHTS_YEAR = "2026"
SITE_ADDRESS = "link-station-commercial-daceroberts.streamlit.app"
FIGURE_CREDIT = f"© {RIGHTS_YEAR} {RIGHTS_HOLDER} · {SITE_ADDRESS}"
_RIGHTS_TEXT = (
    f"Map design, text and figures © {RIGHTS_YEAR} {RIGHTS_HOLDER}. "
    "All rights reserved. Code under the MIT License."
)
RIGHTS_META_TAGS = (
    f'<meta name="copyright" content="{_RIGHTS_TEXT}">\n'
    f'<meta name="dcterms.rights" content="{_RIGHTS_TEXT} Third-party data '
    "remains under its publishers' terms; see docs/data_sources.md in the "
    'project repository.">\n'
    f'<meta name="dcterms.rightsHolder" content="{RIGHTS_HOLDER}">'
)
