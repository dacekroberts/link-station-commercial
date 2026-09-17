"""Small pieces of UI shared across pages.

Streamlit's multipage app has no shared layout/header mechanism of its own -
each page is its own top-to-bottom script - so anything meant to appear
identically on every page (like the social links below) lives here once and
gets called from each page, rather than duplicated four times over.
"""

import streamlit as st

# Streamlit's default expanded sidebar is 300px. The ask was 2/3 of that
# (200px), but the longest nav label - "Methodology & Limitations" - needs
# at least 218px of sidebar width before it stops clipping under
# text-overflow:ellipsis (measured directly in the rendered DOM, binary-
# searched to the exact pixel: 217px clips, 218px doesn't). 225px is the
# narrowest round number with a small safety margin above that measured
# threshold, so it survives minor font-rendering differences across
# browsers rather than sitting exactly on the edge.
SIDEBAR_WIDTH_PX = 225


def set_base_font():
    """Swaps Streamlit's default typeface for Inter on base page text only.

    Inter, not Streamlit's default Source Sans Pro - a widely-used,
    highly-legible sans-serif on modern data/product interfaces (Notion,
    Vercel, GitHub's newer UI, Figma), which reads as an intentional
    typographic choice rather than an unstyled default for a portfolio site
    aimed at hiring managers. Loaded via Google Fonts rather than a new pip
    dependency, keeping requirements.txt lean.

    Deliberately scoped, not a blanket override: embedded chart/diagram text
    is explicitly excluded and reset back to the original default, so this
    only touches prose, headers, captions, metrics, and tables - not "text
    embedded in other visuals" per the user's own distinction. The Mermaid
    flowchart and Folium heatmap need no such exclusion - both render inside
    their own iframe documents, already isolated from this page's CSS by
    construction.
    """
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

        /* Wildcard, not just html/body: Streamlit sets font-family
        directly on its own text elements (p, headers, etc.), and a plain
        inherited value from an ancestor - even an !important one - always
        loses to any rule that targets the element itself. Scoping the
        wildcard to the app container and sidebar, rather than a bare `*`,
        keeps this from reaching into the chart/code exclusions below at
        a lower specificity than they need. */
        [data-testid="stAppViewContainer"] *,
        [data-testid="stSidebar"] *,
        [data-testid="stHeader"] * {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont,
                "Segoe UI", sans-serif !important;
        }

        /* Altair/Vega-Lite charts (Graphs 1-5) are the one place inline
        SVG text sits inside the page's own DOM rather than an iframe, so
        this needs an explicit reset - otherwise it would inherit the new
        base font too. Same specificity shape as the wildcard above (one
        attribute selector + one type selector) plus source order below
        it, so this wins for chart text specifically. */
        [data-testid="stVegaLiteChart"] text {
            font-family: "Source Sans Pro", sans-serif !important;
        }

        /* Code stays monospace regardless of the base font - scoped to
        match or exceed the wildcard's specificity, not a bare `code`
        selector, which the wildcard above would otherwise outrank. */
        [data-testid="stAppViewContainer"] code,
        [data-testid="stAppViewContainer"] pre,
        [data-testid="stAppViewContainer"] kbd,
        [data-testid="stAppViewContainer"] samp,
        [data-testid="stSidebar"] code {
            font-family: "Source Code Pro", Menlo, Consolas, monospace !important;
        }

        /* Streamlit's own UI glyphs (sidebar collapse/expand arrow, etc.)
        are rendered as ligatures in the Material Symbols icon font, not
        images - the wildcard above was breaking these, showing the raw
        ligature name ("keyboard_double_arrow_left") as literal text
        instead of the arrow icon. Confirmed via the element's own
        pre-existing rule (font-family: "Material Symbols Rounded"). */
        [data-testid="stIconMaterial"] {
            font-family: "Material Symbols Rounded" !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def set_sidebar_width():
    """Shrinks the expanded sidebar from Streamlit's 300px default.

    Not user-resize-proof by design - Streamlit's own drag handle can still
    widen it back out; this only sets the default/initial width.
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


def render_social_links():
    """GitHub/LinkedIn icon links, top-right above the page title.

    Streamlit's own toolbar (hamburger/three-dot menu, Rerun, Always rerun)
    is native chrome with no public API to add elements into it - this sits
    in normal page flow instead of a position:fixed overlay, so it can't
    drift out of sync with that toolbar's height/position across Streamlit
    versions or widths. Inline SVGs (standard GitHub octicon / LinkedIn "in"
    mark), not <img> tags, to avoid any external network fetch on page load.
    """
    st.markdown(
        """
        <style>
        .social-links { display: flex; justify-content: flex-end; gap: 14px;
            margin-bottom: 0.25rem; }
        .social-links a { color: #9aa0a6; display: inline-flex; transition: color 0.15s; }
        .social-links a:hover { color: #d0d3d9; }
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
