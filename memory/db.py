"""
Structured (relational) memory: every user turn, tool call, and result
gets logged here. This is your audit trail and short-term recall source.
"""
import sqlite3
import json
import time
import os
from config import SQLITE_PATH, DATA_DIR

os.makedirs(DATA_DIR, exist_ok=True)


def _connect():
    conn = sqlite3.connect(SQLITE_PATH)
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn


def init_db():
    conn = _connect()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS turns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts REAL NOT NULL,
            role TEXT NOT NULL,          -- 'user' | 'assistant' | 'tool'
            content TEXT NOT NULL,
            tool_name TEXT,
            tool_input TEXT,
            tool_output TEXT,
            success INTEGER
        )
    """)
    conn.commit()
    conn.close()


def log_turn(role, content, tool_name=None, tool_input=None, tool_output=None, success=None):
    conn = _connect()
    conn.execute(
        "INSERT INTO turns (ts, role, content, tool_name, tool_input, tool_output, success) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (
            time.time(), role, content, tool_name,
            json.dumps(tool_input) if tool_input is not None else None,
            json.dumps(tool_output) if isinstance(tool_output, (dict, list)) else tool_output,
            None if success is None else int(success),
        ),
    )
    conn.commit()
    conn.close()


def recent_turns(limit=20):
    conn = _connect()
    cur = conn.execute(
        "SELECT ts, role, content, tool_name, tool_output FROM turns ORDER BY id DESC LIMIT ?",
        (limit,),
    )
    rows = cur.fetchall()
    conn.close()
    return list(reversed(rows))  # chronological order


def search_turns(keyword, limit=20):
    conn = _connect()
    cur = conn.execute(
        "SELECT ts, role, content FROM turns WHERE content LIKE ? ORDER BY id DESC LIMIT ?",
        (f"%{keyword}%", limit),
    )
    rows = cur.fetchall()
    conn.close()
    return rows
