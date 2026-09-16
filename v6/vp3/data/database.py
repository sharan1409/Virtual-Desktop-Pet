"""
data/database.py — SQLite persistence layer.

Tables:
  chat_history  — all messages between user and Gemini
  todos         — to-do list items
  reminders     — scheduled reminders
  pet_state     — mood, xp, name, etc.
"""

import sqlite3
import os
from datetime import datetime
from config import DB_PATH


class Database:
    def __init__(self):
        self.path = DB_PATH

    # ── connection helper ──────────────────────────────────────────────────
    def _conn(self):
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    # ── setup ──────────────────────────────────────────────────────────────
    def initialize(self):
        with self._conn() as c:
            c.executescript("""
                CREATE TABLE IF NOT EXISTS chat_history (
                    id        INTEGER PRIMARY KEY AUTOINCREMENT,
                    role      TEXT    NOT NULL,   -- 'user' or 'assistant'
                    message   TEXT    NOT NULL,
                    timestamp TEXT    NOT NULL
                );

                CREATE TABLE IF NOT EXISTS todos (
                    id        INTEGER PRIMARY KEY AUTOINCREMENT,
                    task      TEXT    NOT NULL,
                    done      INTEGER NOT NULL DEFAULT 0,
                    priority  TEXT    NOT NULL DEFAULT 'normal',  -- low/normal/high
                    created   TEXT    NOT NULL,
                    completed TEXT
                );

                CREATE TABLE IF NOT EXISTS reminders (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    message     TEXT    NOT NULL,
                    remind_at   TEXT    NOT NULL,
                    repeat_mins INTEGER NOT NULL DEFAULT 0,
                    done        INTEGER NOT NULL DEFAULT 0
                );

                CREATE TABLE IF NOT EXISTS pet_state (
                    key   TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );
            """)
            # Seed default pet state if empty
            defaults = {
                "mood": "80",
                "xp": "0",
                "level": "1",
                "total_interactions": "0",
                "reaction_top_score": "",   # empty = no score yet
            }
            for k, v in defaults.items():
                c.execute(
                    "INSERT OR IGNORE INTO pet_state (key, value) VALUES (?, ?)", (k, v)
                )

    # ── chat history ───────────────────────────────────────────────────────
    def save_message(self, role: str, message: str):
        ts = datetime.now().isoformat(sep=" ", timespec="seconds")
        with self._conn() as c:
            c.execute(
                "INSERT INTO chat_history (role, message, timestamp) VALUES (?, ?, ?)",
                (role, message, ts),
            )

    def get_recent_messages(self, limit: int = 50):
        with self._conn() as c:
            rows = c.execute(
                "SELECT role, message, timestamp FROM chat_history "
                "ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return list(reversed(rows))

    def clear_chat_history(self):
        with self._conn() as c:
            c.execute("DELETE FROM chat_history")

    # ── to-do list ─────────────────────────────────────────────────────────
    def add_todo(self, task: str, priority: str = "normal") -> int:
        ts = datetime.now().isoformat(sep=" ", timespec="seconds")
        with self._conn() as c:
            cur = c.execute(
                "INSERT INTO todos (task, priority, created) VALUES (?, ?, ?)",
                (task, priority, ts),
            )
            return cur.lastrowid

    def get_todos(self, include_done: bool = False):
        with self._conn() as c:
            if include_done:
                return c.execute(
                    "SELECT * FROM todos ORDER BY done, priority DESC, created"
                ).fetchall()
            return c.execute(
                "SELECT * FROM todos WHERE done=0 ORDER BY priority DESC, created"
            ).fetchall()

    def complete_todo(self, todo_id: int):
        ts = datetime.now().isoformat(sep=" ", timespec="seconds")
        with self._conn() as c:
            c.execute(
                "UPDATE todos SET done=1, completed=? WHERE id=?", (ts, todo_id)
            )

    def delete_todo(self, todo_id: int):
        with self._conn() as c:
            c.execute("DELETE FROM todos WHERE id=?", (todo_id,))

    # ── reminders ──────────────────────────────────────────────────────────
    def add_reminder(self, message: str, remind_at: str, repeat_mins: int = 0) -> int:
        with self._conn() as c:
            cur = c.execute(
                "INSERT INTO reminders (message, remind_at, repeat_mins) VALUES (?, ?, ?)",
                (message, remind_at, repeat_mins),
            )
            return cur.lastrowid

    def get_due_reminders(self):
        now = datetime.now().isoformat(sep=" ", timespec="seconds")
        with self._conn() as c:
            return c.execute(
                "SELECT * FROM reminders WHERE done=0 AND remind_at <= ?", (now,)
            ).fetchall()

    def get_all_reminders(self):
        with self._conn() as c:
            return c.execute(
                "SELECT * FROM reminders WHERE done=0 ORDER BY remind_at"
            ).fetchall()

    def mark_reminder_done(self, reminder_id: int):
        with self._conn() as c:
            c.execute("UPDATE reminders SET done=1 WHERE id=?", (reminder_id,))

    def delete_reminder(self, reminder_id: int):
        with self._conn() as c:
            c.execute("DELETE FROM reminders WHERE id=?", (reminder_id,))

    # ── pet state ──────────────────────────────────────────────────────────
    def get_state(self, key: str, default=None):
        with self._conn() as c:
            row = c.execute(
                "SELECT value FROM pet_state WHERE key=?", (key,)
            ).fetchone()
        return row["value"] if row else default

    def set_state(self, key: str, value):
        with self._conn() as c:
            c.execute(
                "INSERT OR REPLACE INTO pet_state (key, value) VALUES (?, ?)",
                (key, str(value)),
            )

    def get_mood(self) -> int:
        return int(self.get_state("mood", 80))

    def set_mood(self, value: int):
        self.set_state("mood", max(0, min(100, value)))

    def add_xp(self, amount: int = 5):
        xp = int(self.get_state("xp", 0)) + amount
        level = int(self.get_state("level", 1))
        # Level up every 100 XP
        while xp >= 100:
            xp -= 100
            level += 1
        self.set_state("xp", xp)
        self.set_state("level", level)
        interactions = int(self.get_state("total_interactions", 0)) + 1
        self.set_state("total_interactions", interactions)
        return level
