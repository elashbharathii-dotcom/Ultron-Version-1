import streamlit as st
from orchestrator import handle_user_input
from tools import shell_tool
from memory import db
from ultron_orb import render_orb
from ultron_theme import inject_theme, hud_frame_open, hud_frame_close
from wake_queue import get_pending_wake_command
from gesture_state import get_gesture_state, consume_swipe
from streamlit_autorefresh import st_autorefresh
import streamlit.components.v1 as components

st.set_page_config(page_title="Ultron", layout="wide")
inject_theme()

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

st.markdown(
    "<h1 style='text-align:center;'>🤖 U L T R O N</h1>",
    unsafe_allow_html=True,
)
st_autorefresh(interval=3000, key="wake_poll")

# ---------------- Top bar: mic + text input + toggles, all up front ----------------
top_l, top_c, top_r = st.columns([1, 3, 1])
with top_l:
    if st.button("🎙️ Speak (5s)", use_container_width=True):
        st.session_state["_speak_now"] = True
with top_c:
    user_typed = st.chat_input("Ask Ultron anything...")
with top_r:
    st.checkbox("Allow shell", value=True, key="allow_shell")
    st.checkbox("Allow ADB", value=True, key="allow_adb")
    st.checkbox("Speak replies", value=False, key="allow_tts")

# ---------------- Resolve input source: wake word > mic button > typed ----------------
user_input = None

wake_cmd = get_pending_wake_command()
if wake_cmd:
    user_input = wake_cmd

if st.session_state.pop("_speak_now", False):
    orb_slot_preview = st.empty()
    with orb_slot_preview:
        components.html(render_orb(state="listening"), height=540)
    from voice.stt import listen_and_transcribe
    user_input = listen_and_transcribe(5)
    orb_slot_preview.empty()

if not user_input and user_typed:
    user_input = user_typed

# ---------------- Gesture: hand speed drives orb rotation, swipe cycles panels ----------------
gesture = get_gesture_state()
speed_mult = gesture["speed_mult"]

PANELS = ["Chat", "System Status", "Activity Log"]
if "active_panel" not in st.session_state:
    st.session_state.active_panel = 0

swipe = consume_swipe()
if swipe == "up":
    st.session_state.active_panel = (st.session_state.active_panel - 1) % len(PANELS)
    components.html(
        "<script>try{window.parent.scrollBy({top:-500,left:0,behavior:'smooth'});}catch(e){}</script>",
        height=0,
    )
elif swipe == "down":
    st.session_state.active_panel = (st.session_state.active_panel + 1) % len(PANELS)
    components.html(
        "<script>try{window.parent.scrollBy({top:500,left:0,behavior:'smooth'});}catch(e){}</script>",
        height=0,
    )

st.markdown(
    f"<p style='text-align:center; color:#ff9d4d; letter-spacing:2px;'>"
    f"◀ swipe to navigate ▶ &nbsp;&nbsp;|&nbsp;&nbsp; VIEW: {PANELS[st.session_state.active_panel].upper()}</p>",
    unsafe_allow_html=True,
)

# ---------------- The holographic core: large, centered, front and center ----------------
hud_frame_open()
orb_slot = st.empty()
with orb_slot:
    components.html(render_orb(state="idle", speed_mult=speed_mult), height=540)
hud_frame_close()

# ---------------- Below: HUD-styled panel for whichever section is active ----------------
active = PANELS[st.session_state.active_panel]

if active == "System Status":
    hud_frame_open()
    st.markdown("**SYSTEM STATUS**")
    status = shell_tool.system_status()
    c1, c2 = st.columns(2)
    c1.metric("CPU", f"{status['cpu_percent']}%")
    c2.metric("RAM", f"{status['ram_percent']}%")
    c1.metric("Disk", f"{status['disk_percent']}%")
    c2.metric("Processes", status["process_count"])
    hud_frame_close()

elif active == "Activity Log":
    hud_frame_open()
    st.markdown("**ACTIVITY LOG**")
    for ts, role, content, tool_name, tool_output in db.recent_turns(limit=10):
        label = f"[{role}]" + (f" {tool_name}" if tool_name else "")
        st.text(f"{label}: {str(content)[:70]}")
    hud_frame_close()

else:  # "Chat"
    hud_frame_open()
    st.markdown("**CONVERSATION**")
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    hud_frame_close()

# ---------------- Process new input ----------------
if user_input:
    st.session_state.chat_history.append({"role": "user", "content": user_input})

    with orb_slot:
        components.html(render_orb(state="thinking"), height=540)

    error_happened = False
    try:
        reply = handle_user_input(user_input, speak_reply=st.session_state.get("allow_tts", False))
    except Exception as e:
        error_happened = True
        reply = f"Something went wrong: {e}"

    with orb_slot:
        components.html(render_orb(state="speaking"), height=540)

    st.session_state.chat_history.append({"role": "assistant", "content": reply})

    with orb_slot:
        components.html(render_orb(state="error" if error_happened else "success"), height=540)

    st.rerun()
