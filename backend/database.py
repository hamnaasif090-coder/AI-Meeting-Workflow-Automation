"""
Database Layer – SQLite via Python's built-in sqlite3 module.
No ORM needed for this project size; keeps dependencies minimal.
"""

import os
import json
import sqlite3
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

DB_PATH = os.path.join(
    os.path.dirname(__file__), "..", "database", "meetings.db"
)


def _connect() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create tables if they don't exist."""
    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS meetings (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                title       TEXT    NOT NULL,
                transcript  TEXT    NOT NULL,
                summary     TEXT,
                tasks       TEXT,   -- JSON array
                action_items TEXT,  -- JSON array
                created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
    logger.info("Database initialised at %s", DB_PATH)


def save_meeting(
    title: str,
    transcript: str,
    summary: str,
    tasks: List[Dict],
    action_items: List[str],
) -> int:
    """Insert a meeting record and return its new ID."""
    with _connect() as conn:
        cursor = conn.execute(
            """
            INSERT INTO meetings (title, transcript, summary, tasks, action_items)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                title,
                transcript,
                summary,
                json.dumps(tasks, ensure_ascii=False),
                json.dumps(action_items, ensure_ascii=False),
            ),
        )
        conn.commit()
        meeting_id = cursor.lastrowid
    logger.info("Meeting saved with id=%d", meeting_id)
    return meeting_id


def get_all_meetings() -> List[Dict[str, Any]]:
    """Return lightweight list of all meetings (no transcript body)."""
    with _connect() as conn:
        rows = conn.execute(
            "SELECT id, title, created_at FROM meetings ORDER BY id DESC"
        ).fetchall()
    return [dict(r) for r in rows]


def get_meeting_by_id(meeting_id: int) -> Optional[Dict[str, Any]]:
    """Return full meeting record including parsed tasks."""
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM meetings WHERE id = ?", (meeting_id,)
        ).fetchone()
    if not row:
        return None
    data = dict(row)
    data["tasks"] = json.loads(data["tasks"] or "[]")
    data["action_items"] = json.loads(data["action_items"] or "[]")
    return data
