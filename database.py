"""
database.py — SQLite persistence layer for the Mental Wellness Journal.
"""

import sqlite3
import json
from datetime import datetime, date
from pathlib import Path
from typing import Optional

DB_PATH = Path("wellness_journal.db")


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create all tables if they don't exist."""
    with get_connection() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS journal_entries (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                entry_date  TEXT    NOT NULL,
                mood        INTEGER NOT NULL CHECK(mood BETWEEN 1 AND 10),
                stress      INTEGER NOT NULL CHECK(stress BETWEEN 1 AND 10),
                energy      INTEGER NOT NULL CHECK(energy BETWEEN 1 AND 10),
                sleep_hours REAL    NOT NULL CHECK(sleep_hours BETWEEN 0 AND 24),
                emotions    TEXT    NOT NULL DEFAULT '[]',
                notes       TEXT    NOT NULL DEFAULT '',
                activities  TEXT    NOT NULL DEFAULT '[]',
                created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS ai_insights (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                entry_id    INTEGER REFERENCES journal_entries(id) ON DELETE CASCADE,
                insight     TEXT    NOT NULL,
                flags       TEXT    NOT NULL DEFAULT '[]',
                created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS therapist_flags (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                entry_id    INTEGER REFERENCES journal_entries(id) ON DELETE CASCADE,
                flag_type   TEXT    NOT NULL,
                severity    TEXT    NOT NULL,
                description TEXT    NOT NULL,
                resolved    INTEGER NOT NULL DEFAULT 0,
                created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
            );
        """)


# ── Journal Entries ──────────────────────────────────────────────────────────

def add_entry(
    entry_date: str,
    mood: int,
    stress: int,
    energy: int,
    sleep_hours: float,
    emotions: list,
    notes: str,
    activities: list,
) -> int:
    with get_connection() as conn:
        cur = conn.execute(
            """INSERT INTO journal_entries
               (entry_date, mood, stress, energy, sleep_hours, emotions, notes, activities)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                entry_date,
                mood,
                stress,
                energy,
                sleep_hours,
                json.dumps(emotions),
                notes,
                json.dumps(activities),
            ),
        )
        return cur.lastrowid


def get_entry_by_date(entry_date: str) -> Optional[dict]:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM journal_entries WHERE entry_date = ? ORDER BY created_at DESC LIMIT 1",
            (entry_date,),
        ).fetchone()
    if row:
        return _deserialize_entry(dict(row))
    return None


def get_all_entries(limit: int = 365) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM journal_entries ORDER BY entry_date DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [_deserialize_entry(dict(r)) for r in rows]


def get_recent_entries(days: int = 30) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT * FROM journal_entries
               WHERE entry_date >= date('now', ? || ' days')
               ORDER BY entry_date ASC""",
            (f"-{days}",),
        ).fetchall()
    return [_deserialize_entry(dict(r)) for r in rows]


def _deserialize_entry(row: dict) -> dict:
    row["emotions"] = json.loads(row.get("emotions", "[]"))
    row["activities"] = json.loads(row.get("activities", "[]"))
    return row


# ── AI Insights ──────────────────────────────────────────────────────────────

def save_ai_insight(entry_id: int, insight: str, flags: list) -> None:
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO ai_insights (entry_id, insight, flags) VALUES (?, ?, ?)",
            (entry_id, insight, json.dumps(flags)),
        )


def get_insight_for_entry(entry_id: int) -> Optional[dict]:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM ai_insights WHERE entry_id = ? ORDER BY created_at DESC LIMIT 1",
            (entry_id,),
        ).fetchone()
    if row:
        d = dict(row)
        d["flags"] = json.loads(d.get("flags", "[]"))
        return d
    return None


# ── Therapist Flags ──────────────────────────────────────────────────────────

def save_flag(entry_id: int, flag_type: str, severity: str, description: str) -> None:
    with get_connection() as conn:
        conn.execute(
            """INSERT INTO therapist_flags (entry_id, flag_type, severity, description)
               VALUES (?, ?, ?, ?)""",
            (entry_id, flag_type, severity, description),
        )


def get_open_flags() -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT tf.*, je.entry_date, je.mood, je.stress
               FROM therapist_flags tf
               JOIN journal_entries je ON tf.entry_id = je.id
               WHERE tf.resolved = 0
               ORDER BY
                 CASE tf.severity WHEN 'critical' THEN 1 WHEN 'high' THEN 2 WHEN 'medium' THEN 3 ELSE 4 END,
                 tf.created_at DESC""",
        ).fetchall()
    return [dict(r) for r in rows]


def resolve_flag(flag_id: int) -> None:
    with get_connection() as conn:
        conn.execute("UPDATE therapist_flags SET resolved = 1 WHERE id = ?", (flag_id,))


def get_all_flags() -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT tf.*, je.entry_date, je.mood, je.stress
               FROM therapist_flags tf
               JOIN journal_entries je ON tf.entry_id = je.id
               ORDER BY tf.created_at DESC""",
        ).fetchall()
    return [dict(r) for r in rows]
