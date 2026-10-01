"""
Injects a full JARVIS/Iron-Man-style visual theme over Streamlit's default
widgets: black background, amber/orange glow, HUD-style borders, monospace
font, corner-bracket frames.

Usage in app.py — call this once, right after st.set_page_config(...):

    from ultron_theme import inject_theme
    inject_theme()
"""
import streamlit as st

_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;600;800&family=Share+Tech+Mono&display=swap');

html, body, [class*="css"] {
    font-family: 'Share Tech Mono', monospace;
}

/* ---- App background: black with a faint amber glow from the top ---- */
.stApp {
    background: radial-gradient(ellipse at top, #1a0d02 0%, #000000 55%);
    color: #ffd8a8;
}

/* ---- Headings ---- */
h1, h2, h3 {
    font-family: 'Orbitron', sans-serif !important;
    color: #ffb15c !important;
    text-shadow: 0 0 10px rgba(255, 140, 30, 0.6);
    letter-spacing: 1px;
}

/* ---- Metrics (CPU/RAM/Disk/Processes) ---- */
[data-testid="stMetricValue"] {
    color: #ffcf8a !important;
    text-shadow: 0 0 8px rgba(255, 160, 40, 0.7);
    font-family: 'Orbitron', sans-serif !important;
}
[data-testid="stMetricLabel"] {
    color: #ff9d4d !important;
    letter-spacing: 1px;
}

/* ---- Buttons ---- */
.stButton > button, .stChatInput button {
    background: rgba(255, 140, 30, 0.08) !important;
    border: 1px solid rgba(255, 150, 40, 0.6) !important;
    color: #ffcf8a !important;
    border-radius: 6px !important;
    box-shadow: 0 0 6px rgba(255, 130, 20, 0.3);
    transition: all 0.15s ease-in-out;
}
.stButton > button:hover {
    box-shadow: 0 0 16px rgba(255, 150, 40, 0.7);
    border-color: #ffb15c !important;
    color: #fff2dd !important;
}

/* ---- Checkboxes ---- */
[data-testid="stCheckbox"] label p {
    color: #ffd8a8 !important;
}

/* ---- Text / chat input ---- */
.stChatInput textarea, .stTextInput input, textarea {
    background: rgba(20, 10, 4, 0.85) !important;
    border: 1px solid rgba(255, 140, 30, 0.5) !important;
    color: #ffe4bd !important;
    border-radius: 8px !important;
}

/* ---- Chat message bubbles ---- */
[data-testid="stChatMessage"] {
    background: rgba(15, 8, 3, 0.75) !important;
    border: 1px solid rgba(255, 120, 20, 0.35);
    border-radius: 10px;
    box-shadow: 0 0 10px rgba(255, 110, 20, 0.12);
}

/* ---- Scrollbar ---- */
::-webkit-scrollbar { width: 8px; }
::-webkit-scrollbar-track { background: #0a0500; }
::-webkit-scrollbar-thumb { background: #ff9d4d55; border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: #ffb15caa; }

/* ---- Corner-bracket HUD frame (used around the orb container) ---- */
.ultron-hud-frame {
    position: relative;
    padding: 10px;
    border: 1px solid rgba(255, 140, 30, 0.25);
    border-radius: 4px;
}
.ultron-hud-frame::before, .ultron-hud-frame::after,
.ultron-hud-frame > .corner-tr, .ultron-hud-frame > .corner-bl {
    content: "";
    position: absolute;
    width: 22px;
    height: 22px;
    border-color: #ffb15c;
    border-style: solid;
    opacity: 0.9;
}
.ultron-hud-frame::before {
    top: -1px; left: -1px;
    border-width: 2px 0 0 2px;
}
.ultron-hud-frame::after {
    bottom: -1px; right: -1px;
    border-width: 0 2px 2px 0;
}
</style>
"""


def inject_theme():
    st.markdown(_CSS, unsafe_allow_html=True)


def hud_frame_open():
    """Call before a block of content (like the orb) to wrap it in a corner-bracket frame."""
    st.markdown('<div class="ultron-hud-frame">', unsafe_allow_html=True)


def hud_frame_close():
    st.markdown('</div>', unsafe_allow_html=True)
