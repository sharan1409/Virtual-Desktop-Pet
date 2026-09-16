"""
features/reminders.py — Checks the DB for due reminders and fires a callback.
"""

from typing import Callable
from data.database import Database


class ReminderChecker:
    def __init__(self, db: Database, show_speech: Callable[[str], None]):
        self.db          = db
        self.show_speech = show_speech

    def check(self):
        due = self.db.get_due_reminders()
        for r in due:
            self.show_speech(f"⏰ {r['message']}", duration=6000)
            self.db.mark_reminder_done(r["id"])
