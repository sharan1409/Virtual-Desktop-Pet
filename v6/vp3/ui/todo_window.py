"""
ui/todo_window.py — To-do list with priority levels and completion tracking.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
    QPushButton, QListWidget, QListWidgetItem, QLabel,
    QComboBox, QCheckBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui  import QColor, QFont


_STYLE = """
QWidget { background: #1e1e2e; color: #cdd6f4; font-size: 13px; }
QLabel#title { font-size: 16px; font-weight: bold; padding: 4px 0; }
QListWidget {
    background: #181825;
    border: 1px solid #313244;
    border-radius: 8px;
    padding: 4px;
}
QListWidget::item { padding: 6px 4px; border-radius: 4px; }
QListWidget::item:selected { background: #313244; }
QLineEdit {
    background: #313244; border: 1px solid #45475a;
    border-radius: 6px; padding: 6px 10px; color: #cdd6f4;
}
QPushButton {
    background: #cba6f7; color: #1e1e2e;
    border: none; border-radius: 6px; padding: 6px 14px;
    font-weight: bold;
}
QPushButton:hover  { background: #b4befe; }
QPushButton#del_btn { background: #f38ba8; }
QPushButton#del_btn:hover { background: #eba0ac; }
QComboBox {
    background: #313244; color: #cdd6f4;
    border: 1px solid #45475a; border-radius: 6px; padding: 4px 8px;
}
"""

PRIORITY_COLOUR = {"high": "#f38ba8", "normal": "#cdd6f4", "low": "#6c7086"}
PRIORITY_ICON   = {"high": "🔴", "normal": "🟡", "low": "🟢"}


class TodoWindow(QWidget):
    def __init__(self, db, pet_window=None):
        super().__init__()
        self.db         = db
        self.pet_window = pet_window
        self.setWindowTitle("📋 To-Do List")
        self.setFixedSize(380, 500)
        self.setWindowFlags(
            Qt.WindowType.Window | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setStyleSheet(_STYLE)
        self._build_ui()
        self._refresh()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 14, 16, 16)
        root.setSpacing(10)

        title = QLabel("📋  To-Do List")
        title.setObjectName("title")
        root.addWidget(title)

        # Input row
        row = QHBoxLayout()
        self.input = QLineEdit()
        self.input.setPlaceholderText("New task…")
        self.input.returnPressed.connect(self._add)
        self.priority_box = QComboBox()
        self.priority_box.addItems(["🔴 High", "🟡 Normal", "🟢 Low"])
        self.priority_box.setCurrentIndex(1)
        add_btn = QPushButton("Add")
        add_btn.clicked.connect(self._add)
        row.addWidget(self.input, stretch=1)
        row.addWidget(self.priority_box)
        row.addWidget(add_btn)
        root.addLayout(row)

        # List
        self.list_widget = QListWidget()
        self.list_widget.setAlternatingRowColors(False)
        root.addWidget(self.list_widget, stretch=1)

        # Bottom buttons
        bot = QHBoxLayout()
        done_btn = QPushButton("✔ Mark Done")
        done_btn.clicked.connect(self._complete)
        del_btn  = QPushButton("🗑 Delete")
        del_btn.setObjectName("del_btn")
        del_btn.clicked.connect(self._delete)
        show_all = QPushButton("Show All")
        show_all.clicked.connect(lambda: self._refresh(include_done=True))
        bot.addWidget(done_btn)
        bot.addWidget(del_btn)
        bot.addWidget(show_all)
        root.addLayout(bot)

    def _add(self):
        text = self.input.text().strip()
        if not text:
            return
        pmap   = {0: "high", 1: "normal", 2: "low"}
        prio   = pmap[self.priority_box.currentIndex()]
        self.db.add_todo(text, prio)
        self.input.clear()
        self._refresh()
        if self.pet_window:
            self.pet_window.show_speech(f"Task added! ✅", 2000)

    def _complete(self):
        item = self.list_widget.currentItem()
        if item and item.data(Qt.ItemDataRole.UserRole):
            self.db.complete_todo(item.data(Qt.ItemDataRole.UserRole))
            self._refresh()
            if self.pet_window:
                self.pet_window.show_speech("Great job! 🎉", 2000)

    def _delete(self):
        item = self.list_widget.currentItem()
        if item and item.data(Qt.ItemDataRole.UserRole):
            self.db.delete_todo(item.data(Qt.ItemDataRole.UserRole))
            self._refresh()

    def _refresh(self, include_done: bool = False):
        self.list_widget.clear()
        todos = self.db.get_todos(include_done=include_done)
        for t in todos:
            icon  = PRIORITY_ICON.get(t["priority"], "🟡")
            check = "✔ " if t["done"] else ""
            label = f"{check}{icon}  {t['task']}"
            item  = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, t["id"])
            colour = QColor(PRIORITY_COLOUR.get(t["priority"], "#cdd6f4"))
            if t["done"]:
                colour = QColor("#45475a")
            item.setForeground(colour)
            self.list_widget.addItem(item)
