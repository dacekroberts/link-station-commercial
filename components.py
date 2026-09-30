"""UI pieces shared by every page.

Streamlit has no shared layout: each page is its own top-to-bottom script.
Anything that should look the same on every page lives here once and is
called from each page.
"""

import streamlit as st

# Streamlit's default is 300px. 240px is the narrowest width where the
# longest nav label ("Methodology & Limitations") doesn't clip in Inter;
# it clips at 235px. Re-measure if the base font changes.
SIDEBAR_WIDTH_PX = 240


def set_base_font():
    """Use Inter for page text; keep the default font in charts and code.

    Inter reads as a deliberate choice rather than an unstyled default, and
    it loads from Google Fonts, so requirements.txt stays lean. The change
    covers prose, headers, captions, metrics and tables only: chart text is
    reset to Streamlit's default. The Mermaid flowchart and the Folium map
    render in their own iframes, so this CSS never reaches them.
    """
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

        /* Wildcard, not html/body: Streamlit sets font-family on its own
        text elements, and an inherited value (even !important) loses to a
        rule on the element itself. Scoped to the app container and sidebar,
        not a bare `*`, so the chart and code resets below can still win. */
        [data-testid="stAppViewContainer"] *,
        [data-testid="stSidebar"] *,
        [data-testid="stHeader"] * {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont,
                "Segoe UI", sans-serif !important;
        }

        /* Altair charts (Graphs 1-5) draw SVG text inside the page, not in
        an iframe, so they need an explicit reset. Same specificity as the
        wildcard plus later source order, so this wins for chart text. */
        [data-testid="stVegaLiteChart"] text {
            font-family: "Source Sans Pro", sans-serif !important;
        }

        /* Code stays monospace. Scoped to match the wildcard's specificity;
        a bare `code` selector would lose to it. */
        [data-testid="stAppViewContainer"] code,
        [data-testid="stAppViewContainer"] pre,
        [data-testid="stAppViewContainer"] kbd,
        [data-testid="stAppViewContainer"] samp,
        [data-testid="stSidebar"] code {
            font-family: "Source Code Pro", Menlo, Consolas, monospace !important;
        }

        /* Streamlit's UI icons (the sidebar arrow, etc.) are ligatures in
        the Material Symbols font. Without this reset the wildcard shows
        their raw names ("keyboard_double_arrow_left") instead of icons. */
        [data-testid="stIconMaterial"] {
            font-family: "Material Symbols Rounded" !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def set_sidebar_width():
    """Set the sidebar's starting width to SIDEBAR_WIDTH_PX.

    Only the starting width: Streamlit's drag handle can still widen it.
    """
    st.markdown(
        f"""
        <style>
        [data-testid="stSidebar"] {{
            width: {SIDEBAR_WIDTH_PX}px !important;
            min-width: {SIDEBAR_WIDTH_PX}px !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar_nav_label():
    """Add a small "Pages" label above the sidebar's page list.

    Streamlit generates that list and has no API for inserting above it, so
    the label is a CSS ::before on the nav container. The nav starts at
    76px, below the collapse arrow's bottom edge at 44px, so the label
    can't overlap the arrow. 12px keeps it from looking heavy.
    """
    st.markdown(
        """
        <style>
        [data-testid="stSidebarNav"]::before {
            content: "Pages";
            display: block;
            padding: 8px 0 4px 20px;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            color: rgba(243, 237, 230, 0.5);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_social_links():
    """GitHub and LinkedIn icon links, top right above the page title.

    Streamlit's toolbar has no API for adding items, so these sit in normal
    page flow rather than a fixed overlay that could drift out of line with
    the toolbar across Streamlit versions. The icons are inline SVGs, so
    they need no extra network requests.
    """
    st.markdown(
        """
        <style>
        .social-links { display: flex; justify-content: flex-end; gap: 14px;
            margin-bottom: 0.25rem; }
        .social-links a { color: #A39A90; display: inline-flex; transition: color 0.15s; }
        .social-links a:hover { color: #F3EDE6; }
        </style>
        <div class="social-links">
          <a href="https://github.com/dacekroberts" target="_blank" rel="noopener noreferrer" title="GitHub">
            <svg width="22" height="22" viewBox="0 0 16 16" fill="currentColor">
              <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38
                0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13
                -.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66
                .07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15
                -.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0
                1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56
                .82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0
                1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42
                -3.58-8-8-8z"/>
            </svg>
          </a>
          <a href="https://www.linkedin.com/in/dace-roberts-57381b279/" target="_blank" rel="noopener noreferrer" title="LinkedIn">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="currentColor">
              <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037
                -1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046
                c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337
                7.433a2.062 2.062 0 11.001-4.124 2.062 2.062 0 01-.001 4.124zM7.114
                20.452H3.558V9h3.556v11.452z"/>
            </svg>
          </a>
        </div>
        """,
        unsafe_allow_html=True,
    )
