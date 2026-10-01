"""
A sci-fi HUD-style notification/confirmation card, matching the JARVIS
reference clip's popup style. Use it to ask the user to confirm before
Ultron runs something risky (a shell command, sending a message, etc).

Usage in app.py:

    from ultron_notification import confirm_action

    if confirm_action(
        title="Ultron interrupted",
        message='Run: del important_file.txt ?',
        key="confirm_delete_1",
    ):
        # user clicked Confirm -> proceed
        ...
    # if they click Ignore, confirm_action returns False and nothing runs
"""
import streamlit as st

_CSS = """
<style>
.ultron-notify {
    background: rgba(20, 10, 4, 0.92);
    border: 1px solid rgba(255, 140, 40, 0.6);
    box-shadow: 0 0 18px rgba(255, 120, 30, 0.35);
    border-radius: 10px;
    padding: 14px 18px;
    margin: 8px 0 4px 0;
    color: #ffd8a8;
    font-family: monospace;
}
.ultron-notify .title {
    color: #ffb15c;
    font-weight: bold;
    margin-bottom: 6px;
    letter-spacing: 0.5px;
}
.ultron-notify .msg {
    color: #ffe4bd;
    font-size: 0.92em;
}
</style>
"""


def confirm_action(title: str, message: str, key: str) -> bool:
    """
    Renders the popup with Confirm/Ignore buttons.
    Returns True only on the run where "Confirm" was just clicked.
    Returns False otherwise (including when "Ignore" was clicked).
    """
    st.markdown(_CSS, unsafe_allow_html=True)
    st.markdown(
        f'<div class="ultron-notify">'
        f'<div class="title">⚠ {title}</div>'
        f'<div class="msg">{message}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )
    col1, col2 = st.columns(2)
    confirmed = col1.button("Confirm", key=f"{key}_confirm")
    ignored = col2.button("Ignore", key=f"{key}_ignore")
    if ignored:
        return False
    return confirmed
