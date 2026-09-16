"""
ui/stats_window.py — Live PC stats: CPU, RAM, Battery.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QProgressBar, QHBoxLayout
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui  import QFont

from features.system_stats import get_stats


_STYLE = """
QWidget { background: #1e1e2e; color: #cdd6f4; font-size: 13px; }
QLabel#title { font-size: 16px; font-weight: bold; padding: 4px 0 10px 0; }
QLabel.stat_label { font-size: 13px; color: #a6adc8; }
QProgressBar {
    background: #313244;
    border: none;
    border-radius: 6px;
    height: 14px;
    text-align: center;
    color: #1e1e2e;
    font-size: 11px;
    font-weight: bold;
}
QProgressBar::chunk { border-radius: 6px; }
QLabel#footer { color: #45475a; font-size: 11px; margin-top: 6px; }
"""


def _bar_colour(pct: float) -> str:
    if pct < 60:
        return "#a6e3a1"   # green
    elif pct < 80:
        return "#fab387"   # orange
    return "#f38ba8"       # red


class StatsWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent, Qt.WindowType.Window)
        self.setWindowTitle("📊 PC Stats")
        self.setFixedSize(340, 280)
        self.setWindowFlags(
            Qt.WindowType.Window | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setStyleSheet(_STYLE)
        self._build_ui()
        self._refresh()

        self._timer = QTimer()
        self._timer.timeout.connect(self._refresh)
        self._timer.start(2000)   # refresh every 2 s

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 16, 20, 16)
        root.setSpacing(12)

        title = QLabel("📊  PC Stats")
        title.setObjectName("title")
        root.addWidget(title)

        # CPU
        self.cpu_label = QLabel("CPU: …")
        self.cpu_label.setProperty("class", "stat_label")
        self.cpu_bar = QProgressBar()
        self.cpu_bar.setRange(0, 100)
        root.addWidget(self.cpu_label)
        root.addWidget(self.cpu_bar)

        # RAM
        self.ram_label = QLabel("RAM: …")
        self.ram_label.setProperty("class", "stat_label")
        self.ram_bar = QProgressBar()
        self.ram_bar.setRange(0, 100)
        root.addWidget(self.ram_label)
        root.addWidget(self.ram_bar)

        # Battery
        self.batt_label = QLabel("Battery: …")
        self.batt_label.setProperty("class", "stat_label")
        self.batt_bar = QProgressBar()
        self.batt_bar.setRange(0, 100)
        root.addWidget(self.batt_label)
        root.addWidget(self.batt_bar)

        self.footer = QLabel("Refreshes every 2 seconds")
        self.footer.setObjectName("footer")
        self.footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(self.footer)
        root.addStretch()

    def _refresh(self):
        s = get_stats()
        if "error" in s:
            self.cpu_label.setText(s["error"])
            return

        cpu = s["cpu"]
        self.cpu_label.setText(f"CPU Usage: {cpu:.1f}%")
        self.cpu_bar.setValue(int(cpu))
        self.cpu_bar.setStyleSheet(
            f"QProgressBar::chunk {{ background: {_bar_colour(cpu)}; border-radius:6px; }}"
        )

        ram_pct = s["ram_used"] / s["ram_total"] * 100 if s["ram_total"] else 0
        self.ram_label.setText(
            f"RAM: {s['ram_used']:,} MB / {s['ram_total']:,} MB  ({ram_pct:.1f}%)"
        )
        self.ram_bar.setValue(int(ram_pct))
        self.ram_bar.setStyleSheet(
            f"QProgressBar::chunk {{ background: {_bar_colour(ram_pct)}; border-radius:6px; }}"
        )

        if s["battery"] is not None:
            plug  = "🔌" if s["plugged_in"] else "🔋"
            btext = f"Battery: {s['battery']}%  {plug}"
            self.batt_label.setText(btext)
            self.batt_bar.setValue(int(s["battery"]))
            b_col = "#f38ba8" if s["battery"] < 20 else "#a6e3a1"
            self.batt_bar.setStyleSheet(
                f"QProgressBar::chunk {{ background: {b_col}; border-radius:6px; }}"
            )
        else:
            self.batt_label.setText("Battery: Not available (desktop?)")
            self.batt_bar.setValue(0)
