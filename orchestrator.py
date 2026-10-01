"""
Ultron's central orchestration loop — fully offline via Ollama.

Flow (matches your spec):
  1. Input arrives (text from Streamlit, or transcribed voice).
  2. ChromaDB retrieves relevant past memory -> prepended as context.
  3. The local model (with tool definitions) decides: shell / sandbox / adb / web / plain reply.
  4. Tool executes (sandboxed where relevant).
  5. Result logged to SQLite + ChromaDB, returned to the model for a final
     natural-language answer, then optionally spoken aloud.
"""
import json
import ollama
from config import OLLAMA_HOST, MODEL_NAME
from memory import db, vector_store
from tools import shell_tool, sandbox_tool, adb_tool, web_search_tool, system_control

_client = ollama.Client(host=OLLAMA_HOST)
db.init_db()

SYSTEM_PROMPT = """You are Ultron, a local automation agent running on the user's own laptop.
You can run shell commands, run Python in a sandbox, control an Android phone via ADB,
and search the web. Always prefer the sandbox for any code execution unless the user
explicitly wants a real system command run. Be concise. Confirm before anything destructive.
When a tool result is returned to you, use it to write a final natural-language answer —
do not call the same tool again unless the previous call failed."""

# Ollama uses OpenAI-style tool schemas: {"type": "function", "function": {...}}
TOOLS = [
    {"type": "function", "function": {
        "name": "run_shell_command",
        "description": "Execute a command directly on the user's OS (real filesystem, real effects). Use only for legitimate system/file/process tasks the user asked for.",
        "parameters": {"type": "object", "properties": {"command": {"type": "string"}}, "required": ["command"]},
    }},
    {"type": "function", "function": {
        "name": "get_system_status",
        "description": "Get CPU, RAM, disk, and network usage snapshot.",
        "parameters": {"type": "object", "properties": {}},
    }},
    {"type": "function", "function": {
        "name": "run_python_sandboxed",
        "description": "Run Python code in an isolated, network-disabled sandbox. Use this for any code you generate to test or compute something.",
        "parameters": {"type": "object", "properties": {"code": {"type": "string"}}, "required": ["code"]},
    }},
    {"type": "function", "function": {
        "name": "adb_list_devices",
        "description": "List connected Android devices.",
        "parameters": {"type": "object", "properties": {}},
    }},
    {"type": "function", "function": {
        "name": "adb_shell",
        "description": "Run a raw `adb shell` command on the connected Android phone (e.g. launch an app, tap coordinates, check battery).",
        "parameters": {"type": "object", "properties": {"command": {"type": "string"}}, "required": ["command"]},
    }},
    {"type": "function", "function": {
        "name": "web_search",
        "description": "Search the live web for current information.",
        "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]},
    }},
    {"type": "function", "function": {
        "name": "open_app",
        "description": "Open a desktop application on the user's laptop by name, e.g. 'notepad', 'chrome', 'spotify', 'calculator'.",
        "parameters": {"type": "object", "properties": {"app_name": {"type": "string"}}, "required": ["app_name"]},
    }},
    {"type": "function", "function": {
        "name": "play_youtube",
        "description": "Search YouTube and play the first matching video in the browser.",
        "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]},
    }},
    {"type": "function", "function": {
        "name": "send_whatsapp_message",
        "description": "Send a WhatsApp message to a phone number (must include country code, e.g. +919876543210).",
        "parameters": {"type": "object", "properties": {"phone_number": {"type": "string"}, "message": {"type": "string"}}, "required": ["phone_number", "message"]},
    }},
]


def _dispatch_tool(name: str, tool_input: dict) -> dict:
    if name == "run_shell_command":
        return shell_tool.run_command(tool_input["command"])
    if name == "get_system_status":
        return shell_tool.system_status()
    if name == "run_python_sandboxed":
        return sandbox_tool.run_code(tool_input["code"])
    if name == "adb_list_devices":
        return adb_tool.list_devices()
    if name == "adb_shell":
        return adb_tool.shell(tool_input["command"])
    if name == "web_search":
        return {"results": web_search_tool.search(tool_input["query"])}
    
    if name == "open_app":
        return system_control.open_app(tool_input["app_name"])
    if name == "play_youtube":
        return system_control.play_youtube(tool_input["query"])
    if name == "send_whatsapp_message":
        return system_control.send_whatsapp_message(tool_input["phone_number"], tool_input["message"])
    return {"error": f"Unknown tool {name}"}


def handle_user_input(user_text: str, speak_reply: bool = False) -> str:
    db.log_turn("user", user_text)

    # Semantic recall from past sessions
    memories = vector_store.recall(user_text, n_results=3)
    memory_context = ""
    if memories:
        memory_context = "\n\nRelevant past context:\n" + "\n".join(f"- {m[0]}" for m in memories)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_text + memory_context},
    ]

    # Agent loop: keep calling tools until the model gives a final text answer
    for _ in range(6):
        response = _client.chat(
            model=MODEL_NAME,
            messages=messages,
            tools=TOOLS,
        )
        message = response["message"]
        tool_calls = message.get("tool_calls")

        if not tool_calls:
            final_text = message.get("content", "").strip()
            db.log_turn("assistant", final_text)
            vector_store.remember(f"User asked: {user_text}\nUltron answered: {final_text}")
            if speak_reply:
                from voice.tts import speak
                speak(final_text)
            return final_text

        messages.append(message)
        for call in tool_calls:
            name = call["function"]["name"]
            args = call["function"]["arguments"]
            if isinstance(args, str):
                args = json.loads(args)
            result = _dispatch_tool(name, args)
            db.log_turn("tool", user_text, tool_name=name, tool_input=args, tool_output=result, success=result.get("success", True))
            messages.append({
                "role": "tool",
                "content": json.dumps(result)[:4000],
            })

    return "Ultron hit the max tool-call limit for this turn — try breaking the task into smaller steps."
