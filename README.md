# Ultron — Fully Offline Local Automation Agent (Ollama Edition)

Everything runs on your laptop. No cloud API, no per-request cost, no data
leaving your machine (except the web-search tool, which by definition talks
to the internet).

The "brain" is a local LLM served by **Ollama**, running on your RTX 5050.

---

## Step 0 — What you're installing, and why

| Piece | Tool | Purpose |
|---|---|---|
| The brain | Ollama + qwen2.5:7b-instruct | decides which tool to call |
| Sandbox | Docker Desktop | isolates any code the model writes |
| Terminal control | built-in (Python `subprocess`) | runs real OS commands |
| Phone control | ADB (Android platform-tools) | controls your Android phone |
| Structured memory | SQLite (built into Python) | logs every turn |
| Semantic memory | ChromaDB + sentence-transformers | long-term recall |
| Voice in | faster-whisper | offline speech-to-text |
| Voice out | pyttsx3 | offline text-to-speech |
| Dashboard | Streamlit | the UI you'll actually use |

You said Python 3.11 is already installed, so we skip that step — just
confirm it's on PATH:

```powershell
python --version
```
Should print `Python 3.11.x`. If it doesn't, close and reopen PowerShell
(sometimes PATH needs a fresh terminal after install).

---

## Step 1 — Install Ollama

1. Go to **ollama.com/download**, download the Windows installer, run it.
2. It installs as a background service — you'll see a llama icon in your
   system tray once it's running.
3. Verify in PowerShell:
   ```powershell
   ollama --version
   ```

## Step 2 — Pull a tool-calling model sized for your GPU

The RTX 5050 (laptop) typically has 8GB VRAM. `qwen2.5:7b-instruct` is a
strong tool-calling model that fits well at 4-bit quantization (Ollama's
default pull):

```powershell
ollama pull qwen2.5:7b-instruct
```

This downloads several GB — let it finish. Test it works:
```powershell
ollama run qwen2.5:7b-instruct "Say hello in one sentence."
```
You should get a reply in a few seconds. Ctrl+D or `/bye` to exit.

**If replies feel slow** or you get out-of-memory errors, drop to a smaller
model instead: `ollama pull qwen2.5:3b-instruct` and set that as
`ULTRON_MODEL` in your `.env` later.

**Confirm GPU usage**: while a prompt is running, open Task Manager →
Performance → GPU. You should see GPU utilization spike. If it stays at 0%
and only CPU spikes, Ollama fell back to CPU — usually means your NVIDIA
driver needs updating (GeForce Experience / NVIDIA App → check for updates).

## Step 3 — Get the project files and create a virtual environment

Unzip the `ultron.zip` I gave you somewhere like `C:\Users\<you>\ultron`.

```powershell
cd C:\Users\<you>\ultron
python -m venv venv
venv\Scripts\activate
```
Your prompt should now start with `(venv)`. Keep this terminal — you'll
reuse it for every step below.

## Step 4 — Install Python dependencies

```powershell
pip install -r requirements.txt
```

Two common Windows hiccups:
- If `sentence-transformers` or `faster-whisper` fail to build with a
  compiler error: install **Visual C++ Build Tools** (search "Build Tools
  for Visual Studio" → download → check "Desktop development with C++"
  → install → restart PowerShell → retry `pip install -r requirements.txt`.
- If `sounddevice` complains about PortAudio: `pip install sounddevice`
  again after the first failure usually resolves it (it bundles the binary
  on retry).

To make Whisper use your RTX 5050 instead of CPU, also install CUDA-enabled
PyTorch:
```powershell
pip install torch --index-url https://download.pytorch.org/whl/cu121
```

## Step 5 — Configure environment variables

```powershell
copy .env.example .env
notepad .env
```
Defaults are already correct for this setup (`OLLAMA_HOST`, model name,
`WHISPER_DEVICE=cuda`). Save and close.

## Step 6 — Install Docker Desktop (real sandbox isolation)

1. Download Docker Desktop from docker.com, install, **restart your laptop**
   (Windows requires this for the WSL2 backend Docker uses).
2. Open Docker Desktop once so the engine starts (whale icon in system tray
   turns steady, not animated).
3. Verify:
   ```powershell
   docker run hello-world
   ```
   If you see "Hello from Docker!", you're set. If you skip this step,
   `sandbox_tool.py` still works but only with a timeout as protection —
   fine for learning, not for running code you don't trust.

## Step 7 — (Optional) Set up ADB for phone control

1. Download **platform-tools** from developer.android.com/tools/releases/platform-tools
2. Unzip to e.g. `C:\platform-tools`
3. Add that folder to PATH: Windows search "Edit environment variables for
   your account" → select `Path` → Edit → New → paste the folder → OK
4. On your phone: Settings → About phone → tap "Build number" 7 times
   (unlocks Developer options) → back out → Developer options → enable
   "USB debugging"
5. Plug phone into laptop via USB → tap "Allow" on the "Allow USB
   debugging?" popup that appears on the phone
6. Verify in a **new** PowerShell window (so PATH refreshes):
   ```powershell
   adb devices
   ```
   Should list your device as `device` (not `unauthorized` — if
   unauthorized, check the phone screen for the permission popup again).

## Step 8 — Run Ultron

Back in your venv terminal:
```powershell
streamlit run app.py
```
A browser tab opens automatically at `localhost:8501`. That's your
dashboard: chat box, system monitor, tool toggles, and a 🎙️ voice button.

## Step 9 — Try it out

- "What's my CPU and RAM usage right now?"
- "Write and run a Python script that prints the first 20 Fibonacci numbers"
- "List connected ADB devices"
- "Search the web for RTX 5050 laptop benchmark reviews"

Watch the terminal running `streamlit run app.py` — you'll see it logging
each Ollama call and tool dispatch, which is useful for understanding what's
happening under the hood while you learn.

---

## How the pieces map to your original spec

| Your requirement | File |
|---|---|
| Terminal & OS control | `tools/shell_tool.py` |
| System monitoring | `shell_tool.system_status()` |
| ADB remote control | `tools/adb_tool.py` |
| Sandbox + auto-repair | `tools/sandbox_tool.py` (`run_and_repair`, not yet wired into the loop — see below) |
| SQLite structured memory | `memory/db.py` |
| ChromaDB semantic memory / RAG | `memory/vector_store.py` |
| Offline STT | `voice/stt.py` (faster-whisper) |
| Offline TTS | `voice/tts.py` (pyttsx3) |
| Streamlit dashboard | `app.py` |
| Web search & scraping | `tools/web_search_tool.py` |
| Orchestration loop (now Ollama-based) | `orchestrator.py` |

---

## Safety notes — please actually read this

- `shell_tool.py` uses a **blocklist**, not an allowlist. It stops known-bad
  patterns but isn't bulletproof. Never expose port 8501 beyond
  `localhost` (no port forwarding, no `--server.address 0.0.0.0`).
- Because you asked for real OS/ADB control, Ultron *will* run destructive
  commands if you explicitly ask it to — there's no confirmation dialog
  yet. Treat it like a capable but very literal intern, not a safety net.
- Docker's `--network none` flag on the sandbox is intentional — it stops
  any model-generated code from reaching the internet. Don't remove it.
- Only use ADB control on a phone you own, with USB debugging explicitly
  authorized by you.
- Local models (unlike Claude/GPT-4-class cloud models) are much more
  likely to hallucinate a plausible-looking shell command that's subtly
  wrong. Read what it's about to run before trusting it blindly, especially
  early on.

---

## Next steps once this is running smoothly

1. **Wire up `run_and_repair`** in `sandbox_tool.py` into the orchestrator
   so failed sandboxed code gets automatically fixed and retried.
2. **Try a bigger/smaller model** — if qwen2.5:7b's tool-calling feels
   unreliable, `ollama pull llama3.1:8b` is another solid tool-calling
   option to A/B test.
3. **Add a wake-word** (`pvporcupine`) so voice mode listens continuously
   instead of a manual 5-second button press.
4. **Add a confirmation step** before `run_shell_command` or `adb_shell`
   actually executes, especially for anything matching delete/uninstall/
   format patterns.
5. **Screenshot + tap on the phone** — `adb exec-out screencap` piped
   through OCR, so Ultron can "see" the phone screen before tapping
   coordinates blindly.
