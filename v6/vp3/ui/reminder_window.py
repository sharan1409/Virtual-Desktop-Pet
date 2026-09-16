"""
ui/reminder_window.py — Add and manage reminders.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
    QPushButton, QListWidget, QListWidgetItem, QLabel,
    QDateTimeEdit, QSpinBox
)
from PyQt6.QtCore import Qt, QDateTime
from PyQt6.QtGui  import QColor


_STYLE = """
QWidget { background: #1e1e2e; color: #cdd6f4; font-size: 13px; }
QLabel#title { font-size: 16px; font-weight: bold; padding: 4px 0 8px 0; }
QListWidget {
    background: #181825; border: 1px solid #313244;
    border-radius: 8px; padding: 4px;
}
QListWidget::item { padding: 6px 4px; border-radius: 4px; }
QLineEdit, QDateTimeEdit, QSpinBox {
    background: #313244; border: 1px solid #45475a;
    border-radius: 6px; padding: 6px 10px; color: #cdd6f4;
}
QPushButton {
    background: #cba6f7; color: #1e1e2e; border: none;
    border-radius: 6px; padding: 6px 14px; font-weight: bold;
}
QPushButton:hover { background: #b4befe; }
QPushButton#del_btn { background: #f38ba8; }
QLabel.hint { color: #6c7086; font-size: 11px; }
"""


class ReminderWindow(QWidget):
    def __init__(self, db, pet_window=None):
        super().__init__()
        self.db         = db
        self.pet_window = pet_window
        self.setWindowTitle("⏰ Reminders")
        self.setFixedSize(420, 480)
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

        title = QLabel("⏰  Reminders")
        title.setObjectName("title")
        root.addWidget(title)

        # Message input
        self.msg_input = QLineEdit()
        self.msg_input.setPlaceholderText("Reminder message…")
        root.addWidget(self.msg_input)

        # DateTime + repeat
        row1 = QHBoxLayout()
        self.dt_edit = QDateTimeEdit(QDateTime.currentDateTime().addSecs(300))
        self.dt_edit.setDisplayFormat("dd/MM/yyyy  hh:mm")
        self.dt_edit.setCalendarPopup(True)

        repeat_label = QLabel("Repeat (mins):")
        self.repeat_spin = QSpinBox()
        self.repeat_spin.setRange(0, 1440)
        self.repeat_spin.setValue(0)
        self.repeat_spin.setSpecialValueText("No repeat")

        row1.addWidget(self.dt_edit, stretch=2)
        row1.addWidget(repeat_label)
        row1.addWidget(self.repeat_spin, stretch=1)
        root.addLayout(row1)

        hint = QLabel("0 minutes = one-time reminder")
        hint.setProperty("class", "hint")
        root.addWidget(hint)

        add_btn = QPushButton("➕  Add Reminder")
        add_btn.clicked.connect(self._add)
        root.addWidget(add_btn)

        root.addWidget(QLabel("Upcoming reminders:"))
        self.list_widget = QListWidget()
        root.addWidget(self.list_widget, stretch=1)

        del_btn = QPushButton("🗑  Delete Selected")
        del_btn.setObjectName("del_btn")
        del_btn.clicked.connect(self._delete)
        root.addWidget(del_btn)

    def _add(self):
        msg = self.msg_input.text().strip()
        if not msg:
            return
        remind_at  = self.dt_edit.dateTime().toString("yyyy-MM-dd hh:mm:ss")
        repeat_min = self.repeat_spin.value()
        self.db.add_reminder(msg, remind_at, repeat_min)
        self.msg_input.clear()
        self._refresh()
        if self.pet_window:
            self.pet_window.show_speech("Reminder set! ⏰", 2000)

    def _delete(self):
        item = self.list_widget.currentItem()
        if item and item.data(Qt.ItemDataRole.UserRole):
            self.db.delete_reminder(item.data(Qt.ItemDataRole.UserRole))
            self._refresh()

    def _refresh(self):
        self.list_widget.clear()
        reminders = self.db.get_all_reminders()
        for r in reminders:
            rep  = f"  🔄 every {r['repeat_mins']} min" if r["repeat_mins"] else ""
            text = f"⏰  {r['remind_at']}  —  {r['message']}{rep}"
            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, r["id"])
            item.setForeground(QColor("#89dceb"))
            self.list_widget.addItem(item)
