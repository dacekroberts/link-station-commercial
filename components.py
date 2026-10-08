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


# One three-section articulated light rail vehicle, cabs at both ends, in a
# 250 x 40 box. Shape follows Link's cars; colors are the site theme's
# (.streamlit/config.toml), with no Sound Transit stripe, logo or livery.
_LRV_SHAPES = """
<path d="M14 8H98V33H3Q1 33 1 30V20Q1 12 8 9Q11 8 14 8Z" fill="#F0801F"/>
<path d="M102 8H148V33H102Z" fill="#F0801F"/>
<path d="M152 8H236Q239 8 242 9Q249 12 249 20V30Q249 33 247 33H152Z" fill="#F0801F"/>
<rect x="98" y="10" width="4" height="21" fill="#6B6259"/>
<rect x="148" y="10" width="4" height="21" fill="#6B6259"/>
<path d="M3 26H98V33H3Q1 33 1 31V26Z" fill="#C2500A"/>
<rect x="102" y="26" width="46" height="7" fill="#C2500A"/>
<path d="M152 26H249V31Q249 33 247 33H152Z" fill="#C2500A"/>
<path d="M12 8H98V10H6Q8 8.5 12 8Z" fill="#FBB878"/>
<rect x="102" y="8" width="46" height="2" fill="#FBB878"/>
<path d="M152 8H238Q242 8.5 244 10H152Z" fill="#FBB878"/>
<g fill="#171412">
  <path d="M2.5 21Q3 14 9 11.5L16 11.5V21Z"/>
  <rect x="22" y="13" width="12" height="8" rx="1.5"/><rect x="51" y="13" width="12" height="8" rx="1.5"/><rect x="80" y="13" width="14" height="8" rx="1.5"/>
  <rect x="38" y="12.5" width="9" height="18.5" rx="1"/><rect x="67" y="12.5" width="9" height="18.5" rx="1"/>
  <rect x="106" y="13" width="17" height="8" rx="1.5"/><rect x="127" y="13" width="17" height="8" rx="1.5"/>
  <rect x="156" y="13" width="14" height="8" rx="1.5"/><rect x="187" y="13" width="12" height="8" rx="1.5"/><rect x="216" y="13" width="12" height="8" rx="1.5"/>
  <rect x="174" y="12.5" width="9" height="18.5" rx="1"/><rect x="203" y="12.5" width="9" height="18.5" rx="1"/>
  <path d="M247.5 21Q247 14 241 11.5L234 11.5V21Z"/>
</g>
<g stroke="#3A322B" stroke-width="1"><path d="M42.5 13V31M71.5 13V31M178.5 13V31M207.5 13V31"/></g>
<rect x="2.5" y="27.5" width="3" height="2" rx="0.5" fill="#FDD0A2"/>
<rect x="244.5" y="27.5" width="3" height="2" rx="0.5" fill="#FDD0A2"/>
<g fill="#6B6259"><circle cx="16" cy="35.5" r="3"/><circle cx="28" cy="35.5" r="3"/><circle cx="125" cy="35.5" r="3"/><circle cx="222" cy="35.5" r="3"/><circle cx="234" cy="35.5" r="3"/></g>
<g stroke="#A39A90" stroke-width="1.2" fill="none" stroke-linejoin="round"><path d="M118 8L125 2.5L132 8M121 2.5H129"/></g>
"""


def render_train_banner(page_key):
    """Two-car light rail train that pulls in and parks above the page title.

    Decorative only, so the wrapper is aria-hidden. Pure SVG and CSS, no
    JavaScript. The vehicle is inlined twice rather than referenced through
    <symbol>/<use>, so it never depends on an SVG id staying unique in the
    page or on Streamlit's markdown keeping <use>.

    Every widget interaction reruns the page script and redraws this
    element, which would restart the arrival. A session_state flag per
    page_key plays the arrival on the first render of each page in a
    visitor's session; later reruns render the train already parked.
    Visitors with prefers-reduced-motion always see it parked.
    """
    flag = f"_train_banner_seen_{page_key}"
    state = "parked" if st.session_state.get(flag) else "arriving"
    st.session_state[flag] = True

    stations = "<i></i>" * 16  # one tick per station on the 1 Line
    # One line: st.markdown dedents its body by the common indent, and
    # unindented SVG lines would cancel that and turn the rest into a
    # markdown code block.
    shapes = "".join(line.strip() for line in _LRV_SHAPES.splitlines())
    vehicle = f'<g>{shapes}</g><g transform="translate(256 0)">{shapes}</g>'

    # Sizes: 44px banner, 39px train (28px under 600px wide). The banner
    # sits in empty space above the page content, so nothing below it moves.
    # Streamlit's top padding is 96px at desktop and phone width; the three
    # style-only elements before the banner render 0px tall but each takes
    # a 16px gap, so the first visible element starts at 144px. A -54px top
    # margin on the banner's element container puts the banner at 90-134px,
    # clear of the 60px header, and the 10px bottom margin keeps the social
    # icons at 144px and the title at 170px, where they were before the
    # banner. Measured on Streamlit 1.64; re-measure if Streamlit's padding,
    # the element gap, or the calls before this one change. Browsers
    # without :has() push the page down by the banner height instead.
    st.markdown(
        f"""
        <style>
        [data-testid="stElementContainer"]:has(.train-banner) {{ margin: -54px 0 10px; }}
        .train-banner {{ position: relative; height: 44px; overflow: hidden; }}
        .train-banner-wire {{ position: absolute; left: 0; right: 0; top: 2px;
            height: 1px; background: #3A322B; }}
        .train-banner-track {{ position: absolute; left: 0; right: 0; bottom: 3px;
            height: 2px; background: #3A322B; }}
        .train-banner-ties {{ position: absolute; left: 0; right: 0; bottom: 0; height: 3px;
            background: repeating-linear-gradient(90deg, #3A322B 0 2px, transparent 2px 14px); }}
        .train-banner-stations {{ position: absolute; left: 2%; right: 2%; bottom: 3px;
            display: flex; justify-content: space-between; }}
        .train-banner-stations i {{ width: 3px; height: 8px; background: #6B6259;
            border-radius: 1px; transform: translateY(5px); }}
        /* Full-width row that centers the train. On a banner narrower than
        the train (phones under about 390px), max-width shrinks it to fit,
        and xMidYMax keeps the wheels on the track. */
        .train-banner-train {{ position: absolute; left: 0; right: 0; bottom: 5px;
            display: flex; justify-content: center; }}
        .train-banner-train svg {{ height: 39px; width: auto; max-width: 100%; display: block; }}
        /* Starts half a viewport plus one train length to the left, out of
        view at any width; the easing brakes into the stop. */
        .train-banner-arriving .train-banner-train {{
            animation: train-banner-arrive 3.4s cubic-bezier(.18, .7, .25, 1) both; }}
        @keyframes train-banner-arrive {{
            from {{ transform: translateX(calc(-50vw - 520px)); }}
            to {{ transform: translateX(0); }} }}
        @media (max-width: 600px) {{
            .train-banner-train svg {{ height: 28px; }} }}
        @media (prefers-reduced-motion: reduce) {{
            .train-banner-arriving .train-banner-train {{ animation: none; }} }}
        </style>
        <div class="train-banner train-banner-{state}" aria-hidden="true">
          <div class="train-banner-wire"></div><div class="train-banner-ties"></div><div class="train-banner-track"></div>
          <div class="train-banner-stations">{stations}</div>
          <div class="train-banner-train"><svg viewBox="0 0 506 40" preserveAspectRatio="xMidYMax meet">{vehicle}</svg></div>
        </div>
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


def render_footer():
    """Copyright and license notice, last on every page.

    Visitors to the site never see the README, so the license split it
    states (code MIT, writing all rights reserved, data under each source's
    terms) is repeated here in one line, linking to the full statement.
    """
    st.markdown(
        """
        <style>
        .site-footer { margin-top: 3rem; padding-top: 0.75rem;
            border-top: 1px solid #3A322B; color: #A39A90; font-size: 0.8rem;
            line-height: 1.5; }
        .site-footer a { color: #A39A90; text-decoration: underline; }
        .site-footer a:hover { color: #F3EDE6; }
        </style>
        <div class="site-footer">
          © 2026 Dace Roberts. Code released under the MIT License; writing all
          rights reserved; data remains under each source's own terms.
          <a href="https://github.com/dacekroberts/link-station-commercial#license"
             target="_blank" rel="noopener noreferrer">License details</a>
        </div>
        """,
        unsafe_allow_html=True,
    )
