"""Shared behaviour for the site's two film players (Overview, Flowchart).

A separate module, not components.py: Streamlit Community Cloud keeps
already-imported modules in memory across a redeploy, so a new name added
to an existing shared module fails on the live site with ImportError.
"""

import streamlit as st

# Hides a playing film's controls and cursor after a short idle spell, as
# most video sites do. Safari keeps native controls on screen while the
# pointer rests over an inline video; dropping the controls attribute hides
# them in every browser. Any pointer movement, touch, key press, pause or end
# brings them back. One observer per browser tab wires every video[controls],
# including ones a page renders later.
_AUTOHIDE_SCRIPT = """
<script>
(() => {
  if (window.__filmAutohide) return;
  window.__filmAutohide = true;
  const IDLE_MS = 2500;
  const wire = (v) => {
    if (v.dataset.autohide) return;
    v.dataset.autohide = "1";
    let timer;
    const hideLater = (ms) => {
      clearTimeout(timer);
      timer = setTimeout(() => {
        if (!v.paused) { v.controls = false; v.style.cursor = "none"; }
      }, ms);
    };
    const show = () => {
      v.controls = true;
      v.style.cursor = "";
      if (v.paused) clearTimeout(timer); else hideLater(IDLE_MS);
    };
    ["mousemove", "touchstart", "keydown", "focus", "play"].forEach(
      (e) => v.addEventListener(e, show));
    ["pause", "ended"].forEach((e) => v.addEventListener(e, show));
    v.addEventListener("mouseleave", () => { if (!v.paused) hideLater(600); });
  };
  const scan = () => document.querySelectorAll("video[controls]").forEach(wire);
  scan();
  new MutationObserver(scan).observe(document.body,
    { childList: true, subtree: true });
})();
</script>
"""


def enable_film_autohide():
    """Adds the controls auto-hide script to the page. Safe to call on
    several pages: the script runs once per browser tab."""
    st.html(_AUTOHIDE_SCRIPT, unsafe_allow_javascript=True)
