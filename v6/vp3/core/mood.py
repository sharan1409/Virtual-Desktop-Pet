"""
core/mood.py — Simple 0-100 mood engine.
"""

from config import MOOD_DECAY_AMOUNT, INTERACTION_MOOD_BOOST


MOOD_LABELS = {
    (80, 100): ("ecstatic",  "😄"),
    (60,  79): ("happy",     "😊"),
    (40,  59): ("content",   "😐"),
    (20,  39): ("sad",       "😢"),
    ( 0,  19): ("miserable", "😭"),
}


class MoodEngine:
    def __init__(self, db):
        self.db = db

    def value(self) -> int:
        return self.db.get_mood()

    def label(self) -> tuple[str, str]:
        v = self.value()
        for (lo, hi), label in MOOD_LABELS.items():
            if lo <= v <= hi:
                return label
        return ("unknown", "❓")

    def decay(self):
        self.db.set_mood(self.value() - MOOD_DECAY_AMOUNT)

    def boost(self, amount: int = INTERACTION_MOOD_BOOST):
        self.db.set_mood(self.value() + amount)
