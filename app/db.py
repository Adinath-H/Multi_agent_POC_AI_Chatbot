import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from .config import DB_PATH


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS artifacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            kind TEXT NOT NULL,
            filename TEXT NOT NULL,
            path TEXT NOT NULL,
            version INTEGER NOT NULL,
            source_template TEXT,
            content_text TEXT,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS traces (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            agent TEXT NOT NULL,
            action TEXT NOT NULL,
            details TEXT,
            created_at TEXT NOT NULL
        );
        """
    )
    conn.commit()
    conn.close()


def create_session(session_id: str):
    conn = get_conn()
    conn.execute(
        "INSERT OR IGNORE INTO sessions(id, created_at) VALUES (?, ?)",
        (session_id, datetime.utcnow().isoformat()),
    )
    conn.commit()
    conn.close()


def add_artifact(session_id: str, kind: str, filename: str, path: str,
                 source_template: str | None, content_text: str):
    conn = get_conn()
    row = conn.execute(
        "SELECT COALESCE(MAX(version), 0) AS v FROM artifacts WHERE session_id=? AND kind=?",
        (session_id, kind),
    ).fetchone()
    version = int(row["v"]) + 1
    conn.execute(
        """INSERT INTO artifacts
           (session_id, kind, filename, path, version, source_template, content_text, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (session_id, kind, filename, path, version, source_template, content_text,
         datetime.utcnow().isoformat()),
    )
    conn.commit()
    conn.close()
    return version


def latest_artifact(session_id: str, kind: str):
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM artifacts WHERE session_id=? AND kind=? ORDER BY version DESC LIMIT 1",
        (session_id, kind),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def list_artifacts(session_id: str):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM artifacts WHERE session_id=? ORDER BY kind, version DESC",
        (session_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_trace(session_id: str, agent: str, action: str, details: Any = ""):
    conn = get_conn()
    conn.execute(
        "INSERT INTO traces(session_id, agent, action, details, created_at) VALUES (?, ?, ?, ?, ?)",
        (session_id, agent, action, str(details), datetime.utcnow().isoformat()),
    )
    conn.commit()
    conn.close()


def list_traces(session_id: str):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM traces WHERE session_id=? ORDER BY id ASC",
        (session_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]
