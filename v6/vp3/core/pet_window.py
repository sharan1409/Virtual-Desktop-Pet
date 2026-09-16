"""
core/pet_window.py — Transparent always-on-top pet widget.

v6 changes
----------
• GIF never goes static on click — happy GIF loops until state changes
• Speech bubble "Chopper happy!" shows for 5 sec only
• Single click → dance animation (ch_dance.gif, plays for 2s then back to idle)
  Continuous clicks keep resetting the dance
• Sad mood:
    - Pet moves to leftmost screen edge first
    - Then plays cry GIF (ch_cry.gif) once
    - After cry ends → shows chopper_hide.png (static)
• Background removed from dance/cry/hide assets
"""

import random
import math

from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QMenu, QSystemTrayIcon, QApplication
)
from PyQt6.QtCore import Qt, QTimer, QPoint
from PyQt6.QtGui  import QCursor, QAction, QIcon, QPixmap, QKeySequence, QShortcut

from core.pet_renderer        import PetRenderer
from core.fullscreen_detector import should_hide
from core.mood                import MoodEngine
from ui.chat_window           import ChatWindow
from ui.todo_window           import TodoWindow
from ui.stats_window          import StatsWindow
from ui.reminder_window       import ReminderWindow
from ui.minigame_window       import MinigameWindow
from features.reminders       import ReminderChecker
from config import (
    PET_SIZE, PET_NAME, ANIMATION_FPS, WALK_SPEED,
    IDLE_TIMEOUT_SECS, MOOD_DECAY_INTERVAL, REMINDER_CHECK_INTERVAL
)

# How long "Chopper happy!" speech shows (ms)
_SPEECH_DURATION_MS = 5000
# How long one dance "burst" lasts (ms) — resets on each click
_DANCE_BURST_MS = 2000


class PetWindow(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db    = db
        self.mood  = MoodEngine(db)

        self._drag              = False
        self._drag_pos          = QPoint()
        self._follow_cursor     = False
        self._sleeping          = False
        self._hidden_for_app    = False
        self._manually_hidden   = False

        # Idle / sad tracking  (~60 fps ticks at 16 ms each)
        self._idle_ticks     = 0
        self._idle_sad_ticks = IDLE_TIMEOUT_SECS * 60
        self._is_sad         = False
        self._sad_phase      = None   # None | "moving" | "crying" | "hiding"

        # Dance state
        self._is_dancing    = False
        self._dance_timer   = QTimer(singleShot=True)
        self._dance_timer.timeout.connect(self._end_dance)

        self._speech_timer = QTimer(singleShot=True)
        self._speech_timer.timeout.connect(self._hide_speech)

        self._init_window()
        self._init_renderer()
        self._init_label()
        self._init_movement()
        self._init_timers()
        self._init_tray()
        self._init_hotkey()

        # Sub-windows (lazy)
        self._chat_win     = None
        self._todo_win     = None
        self._stats_win    = None
        self._reminder_win = None
        self._game_win     = None

    # ── Window setup ──────────────────────────────────────────────────────
    def _init_window(self):
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, False)
        self.setFixedSize(PET_SIZE, PET_SIZE + 40)
        screen = QApplication.primaryScreen().availableGeometry()
        self.move(screen.width() - PET_SIZE - 20, screen.height() - PET_SIZE - 60)

    def _init_renderer(self):
        self.renderer = PetRenderer(size=PET_SIZE, fps=ANIMATION_FPS)
        self.renderer.on_frame(self._on_frame)

    def _init_label(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.speech_label = QLabel("")
        self.speech_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.speech_label.setWordWrap(True)
        self.speech_label.setStyleSheet("""
            QLabel {
                background: white;
                border: 2px solid #ccc;
                border-radius: 10px;
                padding: 4px 8px;
                font-size: 11px;
                color: #333;
                max-width: 180px;
            }
        """)
        self.speech_label.setVisible(False)
        self.speech_label.setMaximumWidth(PET_SIZE + 80)

        self.pet_label = QLabel()
        self.pet_label.setFixedSize(PET_SIZE, PET_SIZE)
        self.pet_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.pet_label.setPixmap(self.renderer.current_pixmap())

        layout.addWidget(self.speech_label)
        layout.addWidget(self.pet_label)

    def _init_movement(self):
        self._walk_dir   = 1
        self._walk_ticks = 0
        self._walk_pause = 0

    def _init_timers(self):
        self._loop_timer = QTimer()
        self._loop_timer.timeout.connect(self._tick)
        self._loop_timer.start(16)

        self._app_timer = QTimer()
        self._app_timer.timeout.connect(self._check_app_hide)
        self._app_timer.start(400)

        self._mood_timer = QTimer()
        self._mood_timer.timeout.connect(self._decay_mood)
        self._mood_timer.start(MOOD_DECAY_INTERVAL * 1000)

        self._reminder_checker = ReminderChecker(self.db, self.show_speech)
        self._reminder_timer   = QTimer()
        self._reminder_timer.timeout.connect(self._reminder_checker.check)
        self._reminder_timer.start(REMINDER_CHECK_INTERVAL * 1000)

    def _init_tray(self):
        import os
        icon_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "assets", "chopper_happy_00.png"
        )
        icon = QIcon(icon_path) if os.path.exists(icon_path) else QIcon()
        self._tray = QSystemTrayIcon(icon, self)

        menu = QMenu()
        menu.addAction("🐾 Show Pet  [Ctrl+Shift+P]", self._manual_show)
        menu.addAction("💬 Chat",                      self._open_chat)
        menu.addAction("📋 To-Do List",                self._open_todo)
        menu.addAction("📊 PC Stats",                  self._open_stats)
        menu.addAction("⏰ Reminders",                 self._open_reminders)
        menu.addSeparator()
        menu.addAction("❌ Quit",                      QApplication.quit)
        self._tray.setContextMenu(menu)
        self._tray.activated.connect(self._tray_activated)
        self._tray.show()
        self._tray.setToolTip(f"{PET_NAME} — Ctrl+Shift+P or click tray to show")

    def _init_hotkey(self):
        self._hotkey = QShortcut(QKeySequence("Ctrl+Shift+P"), self)
        self._hotkey.setContext(Qt.ShortcutContext.ApplicationShortcut)
        self._hotkey.activated.connect(self._toggle_visibility)

    # ── Tray ──────────────────────────────────────────────────────────────
    def _tray_activated(self, reason):
        if reason in (
            QSystemTrayIcon.ActivationReason.Trigger,
            QSystemTrayIcon.ActivationReason.DoubleClick,
        ):
            self._manual_show()

    def _manual_show(self):
        self._manually_hidden = False
        self._hidden_for_app  = False
        self.show()
        self.raise_()

    def _toggle_visibility(self):
        if self.isVisible():
            self._manually_hidden = True
            self.hide()
            self._tray.showMessage(
                PET_NAME,
                "Pet hidden — press Ctrl+Shift+P or click tray icon to show.",
                QSystemTrayIcon.MessageIcon.Information, 2500,
            )
        else:
            self._manual_show()

    # ── App-specific hide ─────────────────────────────────────────────────
    def _check_app_hide(self):
        if self._manually_hidden:
            return
        hide_now = should_hide()
        if hide_now and self.isVisible():
            self._hidden_for_app = True
            self.hide()
        elif not hide_now and self._hidden_for_app:
            self._hidden_for_app = False
            self.show()
            self.raise_()

    # ── Main tick ─────────────────────────────────────────────────────────
    def _tick(self):
        # Don't walk/move when dancing or in sad sequence
        if self._is_dancing or self._sad_phase in ("moving", "crying", "hiding"):
            # During sad "moving" phase, handle the leftward slide
            if self._sad_phase == "moving":
                self._slide_to_left()
            return

        if self._follow_cursor:
            self._move_towards_cursor()
        else:
            self._random_walk()

        self._idle_ticks += 1
        if (self._idle_ticks >= self._idle_sad_ticks
                and not self._sleeping and not self._is_sad):
            self._go_sad()

    # ── Sad sequence ──────────────────────────────────────────────────────
    def _go_sad(self):
        """Start the sad sequence: move to left edge, then cry, then hide."""
        self._is_sad    = True
        self._sad_phase = "moving"
        self._dance_timer.stop()
        self._is_dancing = False
        self.show_speech("You forgot about me... 😢", duration=0)

    def _slide_to_left(self):
        """Smoothly slide the pet to the leftmost edge."""
        screen = QApplication.primaryScreen().availableGeometry()
        target_x = screen.left()          # leftmost x
        target_y = screen.bottom() - self.height() - 10
        pos = self.pos()

        dx = target_x - pos.x()
        dy = target_y - pos.y()
        dist = math.hypot(dx, dy)

        if dist < 4:
            # Arrived at left edge — start crying
            self.move(target_x, target_y)
            self._sad_phase = "crying"
            self._hide_speech()
            self.renderer.set_state("sad_cry", on_done=self._on_cry_finished)
        else:
            speed = min(WALK_SPEED * 2, dist)
            new_x = pos.x() + int(dx / dist * speed)
            new_y = pos.y() + int(dy / dist * speed)
            self.move(new_x, new_y)

    def _on_cry_finished(self):
        """Cry GIF finished — switch to hide image."""
        self._sad_phase = "hiding"
        self.renderer.set_state("sad_hide")
        self.show_speech("I'm hiding now... 🙈", duration=0)

    def _go_happy(self):
        """Snap out of sad mode."""
        self._is_sad     = False
        self._sad_phase  = None
        self._idle_ticks = 0
        self._hide_speech()
        self.renderer.set_state("idle")
        self.show_speech("Yay, you're back! 🎉", duration=2500)
        QTimer.singleShot(2600, lambda: self.renderer.set_state("idle"))

    # ── Dance ─────────────────────────────────────────────────────────────
    def _start_dance(self):
        """Play dance animation for _DANCE_BURST_MS, then return to idle.
        Each click resets the timer (continuous clicking keeps dancing)."""
        self._is_dancing = True
        self.renderer.set_state("dance")

        # Reset the timer on each click
        self._dance_timer.stop()
        self._dance_timer.start(_DANCE_BURST_MS)

    def _end_dance(self):
        """Called when dance burst timer fires with no new click."""
        self._is_dancing = False
        self.renderer.set_state("idle")

    # ── Random walk ───────────────────────────────────────────────────────
    def _random_walk(self):
        screen = QApplication.primaryScreen().availableGeometry()
        pos    = self.pos()

        if self._walk_pause > 0:
            self._walk_pause -= 1
            if not self._is_sad and not self._sleeping:
                self.renderer.set_state("idle")
            return

        if self._sleeping:
            self._wake_up()

        if self._is_sad:
            return

        new_x = pos.x() + self._walk_dir * WALK_SPEED
        if new_x <= 0 or new_x >= screen.width() - PET_SIZE:
            self._walk_dir *= -1
            new_x = pos.x() + self._walk_dir * WALK_SPEED

        self.renderer.set_state("walk_right" if self._walk_dir > 0 else "walk_left")
        self.move(new_x, pos.y())

        self._walk_ticks += 1
        if self._walk_ticks > random.randint(80, 200):
            self._walk_ticks = 0
            self._walk_pause = random.randint(30, 120)
            if random.random() < 0.5:
                self._walk_dir *= -1

    def _move_towards_cursor(self):
        cursor = QCursor.pos()
        pos    = self.pos()
        dx     = cursor.x() - pos.x() - PET_SIZE // 2
        dy     = cursor.y() - pos.y() - PET_SIZE // 2
        dist   = math.hypot(dx, dy)
        if dist > 5:
            speed = min(WALK_SPEED * 2, dist)
            new_x = pos.x() + int(dx / dist * speed)
            new_y = pos.y() + int(dy / dist * speed)
            self.renderer.set_state("walk_right" if dx > 0 else "walk_left")
            self.move(new_x, new_y)
        else:
            if not self._is_sad:
                self.renderer.set_state("idle")

    def _start_sleep(self):
        self._sleeping = True
        self.renderer.set_state("sleep")
        self.show_speech("Zzz... 💤", duration=0)

    def _wake_up(self):
        self._sleeping   = False
        self._idle_ticks = 0
        self._hide_speech()
        self.renderer.set_state("idle")
        self.show_speech("Yawn! 😴", duration=2000)

    # ── Frame callback ────────────────────────────────────────────────────
    def _on_frame(self, pixmap):
        self.pet_label.setPixmap(pixmap)

    # ── Speech bubble ─────────────────────────────────────────────────────
    def show_speech(self, text: str, duration: int = 4000):
        self.speech_label.setText(text)
        self.speech_label.setVisible(True)
        self.adjustSize()
        if duration > 0:
            self._speech_timer.start(duration)

    def _hide_speech(self):
        self.speech_label.setVisible(False)
        self.adjustSize()

    # ── Mood ──────────────────────────────────────────────────────────────
    def _decay_mood(self):
        self.mood.decay()
        if self.db.get_mood() < 20:
            self.show_speech("I'm feeling lonely... 😢")

    # ── Interaction ───────────────────────────────────────────────────────
    def _on_interaction(self):
        """Called on every left-click."""
        if self._sleeping:
            self._wake_up()
            return

        if self._is_sad:
            self._go_happy()
            # After going happy, do a dance burst
            QTimer.singleShot(200, self._start_dance)
            QTimer.singleShot(200, lambda: self.show_speech("Chopper happy! 🩺", _SPEECH_DURATION_MS))
        else:
            self._idle_ticks = 0
            # Play dance animation for 2 sec (reset timer on continuous clicks)
            self._start_dance()
            # Show speech for 5 sec — only once per click sequence
            self.show_speech("Chopper happy! 🩺", _SPEECH_DURATION_MS)

        self.mood.boost()
        self.db.add_xp(5)

    # ── Sub-windows ───────────────────────────────────────────────────────
    def _position_window(self, window: QWidget):
        screen = QApplication.primaryScreen().availableGeometry()
        w, h = window.width(), window.height()
        gap  = 10
        x = self.x() + self.width() + gap
        if x + w > screen.right():
            x = self.x() - w - gap
        y = self.y()
        x = max(screen.left(), min(x, screen.right()  - w))
        y = max(screen.top(),  min(y, screen.bottom() - h))
        window.move(x, y)

    def _open_chat(self):
        if self._chat_win is None or not self._chat_win.isVisible():
            self._chat_win = ChatWindow(self.db, self)
        self._position_window(self._chat_win)
        self._chat_win.show(); self._chat_win.raise_()
        self._on_interaction()

    def _open_todo(self):
        if self._todo_win is None or not self._todo_win.isVisible():
            self._todo_win = TodoWindow(self.db, self)
        self._position_window(self._todo_win)
        self._todo_win.show(); self._todo_win.raise_()

    def _open_stats(self):
        if self._stats_win is None or not self._stats_win.isVisible():
            self._stats_win = StatsWindow(self)
        self._position_window(self._stats_win)
        self._stats_win.show(); self._stats_win.raise_()

    def _open_reminders(self):
        if self._reminder_win is None or not self._reminder_win.isVisible():
            self._reminder_win = ReminderWindow(self.db, self)
        self._position_window(self._reminder_win)
        self._reminder_win.show(); self._reminder_win.raise_()

    def _open_minigame(self):
        if self._game_win is None or not self._game_win.isVisible():
            self._game_win = MinigameWindow(self.db, self)
        self._position_window(self._game_win)
        self._game_win.show(); self._game_win.raise_()

    # ── Mouse events ──────────────────────────────────────────────────────
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag     = True
            self._drag_pos = event.globalPosition().toPoint() - self.pos()
            self._on_interaction()
            event.accept()

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._open_chat()

    def mouseMoveEvent(self, event):
        if self._drag and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag = False

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu { background:#2b2b2b; color:white; border:1px solid #444; border-radius:6px; }
            QMenu::item { padding:6px 20px; color:white; }
            QMenu::item:selected { background:#404040; }
        """)
        mood_val = self.db.get_mood()
        level    = self.db.get_state("level", "1")
        xp       = self.db.get_state("xp", "0")
        menu.addAction(
            f"🏴‍☠️ {PET_NAME}  |  Lv.{level}  XP:{xp}/100  Mood:{mood_val}%"
        ).setEnabled(False)
        menu.addSeparator()
        menu.addAction("💬 Chat",       self._open_chat)
        menu.addAction("📋 To-Do List", self._open_todo)
        menu.addAction("⏰ Reminders",  self._open_reminders)
        menu.addAction("📊 PC Stats",   self._open_stats)
        menu.addAction("🎮 Mini-Game",  self._open_minigame)
        menu.addSeparator()

        lbl = "🖱️  Follow Cursor  ✓  (click to stop)" if self._follow_cursor else "🖱️  Follow Cursor"
        follow_act = QAction(lbl, self)
        follow_act.triggered.connect(self._toggle_follow)
        menu.addAction(follow_act)
        menu.addSeparator()

        menu.addAction("👋 Hide  [Ctrl+Shift+P to show]", self._manual_hide)
        menu.addAction("❌ Quit", QApplication.quit)
        menu.exec(event.globalPos())

    def _manual_hide(self):
        self._manually_hidden = True
        self.hide()

    def _toggle_follow(self):
        self._follow_cursor = not self._follow_cursor
        self._hide_speech()
        if self._follow_cursor:
            self.show_speech("Following you! 🐾", 2000)
        else:
            self.show_speech("Free walking now 🌊", 1800)
