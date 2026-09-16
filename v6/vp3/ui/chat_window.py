"""
ui/chat_window.py — Chat window with Gemini AI integration.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit,
    QLineEdit, QPushButton, QLabel, QScrollArea, QFrame
)
from PyQt6.QtCore    import Qt, QTimer, pyqtSignal
from PyQt6.QtGui     import QFont, QColor

from features.gemini_chat import GeminiChat
from config import PET_NAME, CHAT_BUBBLE_WIDTH, CHAT_BUBBLE_HEIGHT


_STYLE = """
QWidget#ChatWindow {
    background: #1e1e2e;
    border-radius: 16px;
}
QLabel#title {
    color: #cdd6f4;
    font-size: 15px;
    font-weight: bold;
    padding: 8px 0 4px 0;
}
QTextEdit#history {
    background: #181825;
    color: #cdd6f4;
    border: none;
    border-radius: 10px;
    font-size: 12px;
    padding: 8px;
}
QLineEdit#input {
    background: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 20px;
    padding: 8px 14px;
    font-size: 13px;
}
QPushButton#send_btn {
    background: #cba6f7;
    color: #1e1e2e;
    border: none;
    border-radius: 18px;
    padding: 8px 16px;
    font-weight: bold;
    font-size: 13px;
}
QPushButton#send_btn:hover  { background: #b4befe; }
QPushButton#clear_btn {
    background: transparent;
    color: #6c7086;
    border: none;
    font-size: 11px;
}
QPushButton#clear_btn:hover { color: #f38ba8; }
"""


class ChatWindow(QWidget):
    def __init__(self, db, pet_window=None):
        super().__init__()
        self.db         = db
        self.pet_window = pet_window
        self.gemini     = GeminiChat(db)
        self._thinking  = False

        self.setObjectName("ChatWindow")
        self.setWindowTitle(f"Chat with {PET_NAME}")
        self.setFixedSize(CHAT_BUBBLE_WIDTH, CHAT_BUBBLE_HEIGHT)
        self.setWindowFlags(
            Qt.WindowType.Window
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setStyleSheet(_STYLE)

        self._build_ui()
        self._load_history()

    # ── UI construction ────────────────────────────────────────────────────
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(14, 10, 14, 14)
        root.setSpacing(8)

        # Title bar
        top = QHBoxLayout()
        title = QLabel(f"💬 {PET_NAME}")
        title.setObjectName("title")
        clear_btn = QPushButton("Clear history")
        clear_btn.setObjectName("clear_btn")
        clear_btn.clicked.connect(self._clear_history)
        top.addWidget(title)
        top.addStretch()
        top.addWidget(clear_btn)
        root.addLayout(top)

        # Chat history
        self.history = QTextEdit()
        self.history.setObjectName("history")
        self.history.setReadOnly(True)
        root.addWidget(self.history, stretch=1)

        # Input row
        row = QHBoxLayout()
        self.input = QLineEdit()
        self.input.setObjectName("input")
        self.input.setPlaceholderText(f"Talk to {PET_NAME}…")
        self.input.returnPressed.connect(self._send)

        self.send_btn = QPushButton("Send")
        self.send_btn.setObjectName("send_btn")
        self.send_btn.setFixedHeight(36)
        self.send_btn.clicked.connect(self._send)

        row.addWidget(self.input, stretch=1)
        row.addWidget(self.send_btn)
        root.addLayout(row)

    # ── Logic ──────────────────────────────────────────────────────────────
    def _load_history(self):
        msgs = self.db.get_recent_messages(40)
        for m in msgs:
            self._append(m["role"], m["message"])

    def _send(self):
        if self._thinking:
            return
        text = self.input.text().strip()
        if not text:
            return
        self.input.clear()
        self._append("user", text)

        self._thinking = True
        self.send_btn.setText("…")
        self.send_btn.setEnabled(False)
        if self.pet_window:
            self.pet_window.show_speech("Thinking… 🤔", duration=0)

        self.gemini.send(
            text,
            on_reply=self._on_reply,
            on_error=self._on_error,
        )

    def _on_reply(self, reply: str):
        # Must update UI on main thread — use QTimer single-shot trick
        QTimer.singleShot(0, lambda: self._show_reply(reply))

    def _show_reply(self, reply: str):
        self._thinking = False
        self.send_btn.setText("Send")
        self.send_btn.setEnabled(True)
        self._append("assistant", reply)
        if self.pet_window:
            short = reply[:60] + ("…" if len(reply) > 60 else "")
            self.pet_window.show_speech(short, duration=5000)
            self.pet_window.animator.set_state("happy")
            QTimer.singleShot(2000,
                lambda: self.pet_window.animator.set_state("idle"))

    def _on_error(self, err: str):
        QTimer.singleShot(0, lambda: self._show_error(err))

    def _show_error(self, err: str):
        self._thinking = False
        self.send_btn.setText("Send")
        self.send_btn.setEnabled(True)
        self._append("error", f"Error: {err}")
        if self.pet_window:
            self.pet_window._hide_speech()

    def _append(self, role: str, text: str):
        colours = {
            "user":      ("#b4befe", "You"),
            "assistant": ("#a6e3a1", PET_NAME),
            "error":     ("#f38ba8", "⚠️"),
        }
        colour, label = colours.get(role, ("#cdd6f4", role))
        html = (
            f'<p style="margin:4px 0">'
            f'<span style="color:{colour};font-weight:bold">{label}:</span> '
            f'<span style="color:#cdd6f4">{text}</span>'
            f'</p>'
        )
        self.history.append(html)
        # Scroll to bottom
        sb = self.history.verticalScrollBar()
        sb.setValue(sb.maximum())

    def _clear_history(self):
        self.db.clear_chat_history()
        self.gemini.clear_history()
        self.history.clear()
        self._append("assistant", "Chat cleared! Fresh start 😊")
