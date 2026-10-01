"""
Direct control over apps, YouTube playback, and WhatsApp messaging on the
user's own laptop.

IMPORTANT: WhatsApp messaging requires being already logged into WhatsApp
Web in your default browser at least once. The first send will open a
browser tab and wait ~15 seconds before sending, then leave the tab open.
"""
import subprocess
import webbrowser
import requests
import re

# Add or edit entries here to teach Ultron new app names.
# The value is what actually gets launched — an .exe name (must be on
# PATH or a known Windows app) or a "start ms-..." command for system apps.
COMMON_APPS = {
    "notepad": "notepad.exe",
    "calculator": "calc.exe",
    "calc": "calc.exe",
    "chrome": "chrome.exe",
    "google chrome": "chrome.exe",
    "spotify": "spotify.exe",
    "whatsapp": "whatsapp.exe",
    "vscode": "code.exe",
    "vs code": "code.exe",
    "word": "winword.exe",
    "excel": "excel.exe",
    "paint": "mspaint.exe",
    "file explorer": "explorer.exe",
    "settings": "ms-settings:",
}


def open_app(app_name: str) -> dict:
    """Launch a known desktop app by name (see COMMON_APPS)."""
    key = app_name.strip().lower()
    target = COMMON_APPS.get(key, app_name)
    try:
        if target.startswith("ms-settings:"):
            subprocess.Popen(f'start {target}', shell=True)
        else:
            subprocess.Popen(f'start "" "{target}"', shell=True)
        return {"success": True, "opened": target}
    except Exception as e:
        return {"success": False, "error": str(e)}


def play_youtube(query: str) -> dict:
    """Searches YouTube and opens/plays the first matching video."""
    try:
        search_url = "https://www.youtube.com/results?search_query=" + requests.utils.quote(query)
        resp = requests.get(search_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        video_ids = re.findall(r"watch\?v=(\S{11})", resp.text)
        if not video_ids:
            webbrowser.open(search_url)
            return {"success": False, "message": "Couldn't find a direct video — opened search results instead."}
        video_url = f"https://www.youtube.com/watch?v={video_ids[0]}"
        webbrowser.open(video_url)
        return {"success": True, "opened": video_url}
    except Exception as e:
        return {"success": False, "error": str(e)}


def send_whatsapp_message(phone_number: str, message: str) -> dict:
    """
    phone_number must include the country code, e.g. +919876543210
    Requires: pip install pywhatkit
    Requires: already logged into web.whatsapp.com in your default browser.
    """
    try:
        import pywhatkit
        pywhatkit.sendwhatmsg_instantly(phone_number, message, wait_time=15, tab_close=False)
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}
