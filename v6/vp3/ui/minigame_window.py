"""
ui/minigame_window.py — Two mini-games:
  1. Number Guess  (classic hi/lo)
  2. Reaction Test (click when green) — top score saved PERMANENTLY to SQLite

The MinigameWindow now requires the db object so the reaction game
can persist and load the all-time best score across restarts.
"""

import random
import time

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QLineEdit, QStackedWidget, QFrame
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui  import QFont


_STYLE = """
QWidget { background: #1e1e2e; color: #cdd6f4; font-size: 13px; }
QLabel#title { font-size: 16px; font-weight: bold; padding: 4px 0 8px 0; }
QLabel#big   { font-size: 28px; font-weight: bold; }
QLabel.hint  { color: #6c7086; font-size: 11px; }
QLabel#top_score {
    font-size: 13px; font-weight: bold;
    color: #f9e2af;
    background: #313244;
    border-radius: 6px;
    padding: 4px 10px;
}
QPushButton {
    background: #cba6f7; color: #1e1e2e; border: none;
    border-radius: 8px; padding: 10px 20px; font-weight: bold; font-size: 14px;
}
QPushButton:hover { background: #b4befe; }
QPushButton#game_btn {
    background: #a6e3a1; color: #1e1e2e;
    border-radius: 12px; font-size: 16px; padding: 20px;
}
QPushButton#game_btn:hover { background: #94e2d5; }
QLineEdit {
    background: #313244; border: 1px solid #45475a;
    border-radius: 6px; padding: 8px; color: #cdd6f4;
    font-size: 14px;
}
QFrame#sep { background: #313244; max-height: 1px; }
"""

DB_KEY_TOP = "reaction_top_score"


# ─────────────────────────────────────────────────────────────────────────────
class NumberGuessGame(QWidget):
    def __init__(self):
        super().__init__()
        self._secret = random.randint(1, 100)
        self._tries  = 0
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(10)

        lay.addWidget(QLabel("🔢  Guess the number (1–100)!"))

        self.feedback = QLabel("Enter your first guess below.")
        self.feedback.setWordWrap(True)
        lay.addWidget(self.feedback)

        row = QHBoxLayout()
        self.guess_input = QLineEdit()
        self.guess_input.setPlaceholderText("Your guess…")
        self.guess_input.returnPressed.connect(self._check)
        guess_btn = QPushButton("Guess")
        guess_btn.clicked.connect(self._check)
        row.addWidget(self.guess_input)
        row.addWidget(guess_btn)
        lay.addLayout(row)

        self.tries_label = QLabel("Tries: 0")
        lay.addWidget(self.tries_label)

        new_btn = QPushButton("New game")
        new_btn.clicked.connect(self._reset)
        lay.addWidget(new_btn)

    def _check(self):
        text = self.guess_input.text().strip()
        if not text.isdigit():
            self.feedback.setText("⚠️  Please enter a number!")
            return
        guess = int(text)
        self._tries += 1
        self.tries_label.setText(f"Tries: {self._tries}")
        self.guess_input.clear()
        if guess < self._secret:
            self.feedback.setText("📈  Too low!  Try higher.")
        elif guess > self._secret:
            self.feedback.setText("📉  Too high!  Try lower.")
        else:
            self.feedback.setText(
                f"🎉  Correct! You guessed {self._secret} in {self._tries} tries!"
            )

    def _reset(self):
        self._secret = random.randint(1, 100)
        self._tries  = 0
        self.tries_label.setText("Tries: 0")
        self.feedback.setText("New game! Enter your first guess.")
        self.guess_input.clear()


# ─────────────────────────────────────────────────────────────────────────────
class ReactionGame(QWidget):
    """
    Reaction Test with PERMANENT best score stored in the pet's SQLite DB.

    The top score is loaded when the widget is created and updated whenever
    the player beats it — survives app restarts.
    """

    def __init__(self, db):
        super().__init__()
        self._db       = db
        self._waiting  = False
        self._start_ts = 0.0
        self._timer    = QTimer(singleShot=True)
        self._timer.timeout.connect(self._light_up)

        # Load persisted best score
        raw = self._db.get_state(DB_KEY_TOP, "")
        self._top_score: float | None = float(raw) if raw else None

        self._build()

    # ── UI ────────────────────────────────────────────────────────────────
    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(10)

        lay.addWidget(QLabel("⚡  Reaction Test — click when it turns green!"))

        # Top score banner
        self.top_label = QLabel()
        self.top_label.setObjectName("top_score")
        self.top_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._refresh_top_label()
        lay.addWidget(self.top_label)

        self.btn = QPushButton("Click START")
        self.btn.setObjectName("game_btn")
        self.btn.setFixedHeight(100)
        self.btn.clicked.connect(self._handle_click)
        lay.addWidget(self.btn)

        self.result = QLabel("")
        self.result.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self.result)

        reset_btn = QPushButton("Reset Top Score")
        reset_btn.clicked.connect(self._reset_top_score)
        lay.addWidget(reset_btn)

    def _refresh_top_label(self):
        if self._top_score is None:
            self.top_label.setText("🏆  Best: —  (no score yet)")
        else:
            self.top_label.setText(f"🏆  All-Time Best: {self._top_score:.0f} ms")

    # ── Game logic ────────────────────────────────────────────────────────
    def _handle_click(self):
        if not self._waiting:
            # Arm the timer — show red wait state
            self.btn.setText("Wait…")
            self.btn.setStyleSheet(
                "QPushButton#game_btn { background: #f38ba8; color: #1e1e2e; "
                "border-radius:12px; font-size:16px; padding:20px; }"
            )
            self._waiting = True
            self._timer.start(random.randint(1000, 4000))
            self.result.setText("")
        else:
            # Player clicked while green → record time
            elapsed = (time.perf_counter() - self._start_ts) * 1000

            # Check if this beats the stored best
            new_record = (self._top_score is None or elapsed < self._top_score)
            if new_record:
                self._top_score = elapsed
                self._db.set_state(DB_KEY_TOP, f"{elapsed:.3f}")
                self._refresh_top_label()
                self.result.setText(
                    f"⚡ {elapsed:.0f} ms  —  🏆 NEW RECORD!"
                )
            else:
                self.result.setText(
                    f"⚡ {elapsed:.0f} ms  "
                    f"(best: {self._top_score:.0f} ms)"
                )

            self._reset_btn()
            self._waiting = False

    def _light_up(self):
        self._start_ts = time.perf_counter()
        self.btn.setText("NOW! Click!")
        self.btn.setStyleSheet(
            "QPushButton#game_btn { background: #a6e3a1; color: #1e1e2e; "
            "border-radius:12px; font-size:16px; padding:20px; }"
        )

    def _reset_btn(self):
        self.btn.setText("Click START")
        self.btn.setStyleSheet("")

    def _reset_top_score(self):
        """Erase the saved top score from the DB."""
        self._top_score = None
        self._db.set_state(DB_KEY_TOP, "")
        self._refresh_top_label()
        self.result.setText("Top score cleared.")


# ─────────────────────────────────────────────────────────────────────────────
class MinigameWindow(QWidget):
    def __init__(self, db, parent=None):
        super().__init__(parent, Qt.WindowType.Window)
        self._db = db
        self.setWindowTitle("🎮 Mini-Games")
        self.setFixedSize(380, 440)
        self.setWindowFlags(
            Qt.WindowType.Window | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setStyleSheet(_STYLE)
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 14, 16, 16)
        root.setSpacing(12)

        title = QLabel("🎮  Mini-Games")
        title.setObjectName("title")
        root.addWidget(title)

        tab_row = QHBoxLayout()
        self._num_btn  = QPushButton("🔢 Number Guess")
        self._reac_btn = QPushButton("⚡ Reaction")
        self._num_btn.clicked.connect(lambda: self._switch(0))
        self._reac_btn.clicked.connect(lambda: self._switch(1))
        tab_row.addWidget(self._num_btn)
        tab_row.addWidget(self._reac_btn)
        root.addLayout(tab_row)

        sep = QFrame()
        sep.setObjectName("sep")
        sep.setFrameShape(QFrame.Shape.HLine)
        root.addWidget(sep)

        self.stack = QStackedWidget()
        self.stack.addWidget(NumberGuessGame())
        self.stack.addWidget(ReactionGame(self._db))   # ← pass db
        root.addWidget(self.stack, stretch=1)

    def _switch(self, idx: int):
        self.stack.setCurrentIndex(idx)
