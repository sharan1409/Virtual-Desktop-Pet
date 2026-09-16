"""
core/animator.py — Sprite-sheet & GIF animation engine.

States  : idle | walk_right | walk_left | sleep | happy | sad | surprised
Fallback: if no real sprite files are found, draws a coloured emoji square so
          the pet is still visible during development.
"""

import os
from PyQt6.QtGui  import QPixmap, QPainter, QColor, QFont
from PyQt6.QtCore import QTimer, Qt


# Map state → subfolder name (inside assets/sprites/)
STATE_DIRS = {
    "idle"        : "idle",
    "walk_right"  : "walk_right",
    "walk_left"   : "walk_left",
    "sleep"       : "sleep",
    "happy"       : "happy",
    "sad"         : "sad",
    "surprised"   : "surprised",
}

# Fallback colour + emoji per state (used when sprites are absent)
FALLBACK = {
    "idle"        : ("#FFD700", "🐱"),
    "walk_right"  : ("#FFA500", "🐱"),
    "walk_left"   : ("#FFA500", "🐱"),
    "sleep"       : ("#87CEEB", "😴"),
    "happy"       : ("#90EE90", "😊"),
    "sad"         : ("#DDA0DD", "😢"),
    "surprised"   : ("#FF6347", "😲"),
}


class Animator:
    """
    Loads frames for each animation state and cycles through them.

    Usage
    -----
    anim = Animator(size=100, fps=8, sprites_dir="assets/sprites")
    anim.set_state("walk_right")
    anim.frame_changed.connect(label.setPixmap)  # NOT a Qt signal — use callback
    # call anim.current_pixmap() each tick to get the current frame
    """

    def __init__(self, size: int = 100, fps: int = 8,
                 sprites_dir: str = "assets/sprites"):
        self.size        = size
        self.fps         = fps
        self.sprites_dir = sprites_dir
        self.state       = "idle"
        self._frames: dict[str, list[QPixmap]] = {}
        self._index      = 0
        self._callback   = None

        self._load_all_states()

        self._timer = QTimer()
        self._timer.timeout.connect(self._advance)
        self._timer.start(1000 // fps)

    # ── public API ─────────────────────────────────────────────────────────
    def set_state(self, state: str):
        if state not in STATE_DIRS:
            state = "idle"
        if state != self.state:
            self.state  = state
            self._index = 0

    def current_pixmap(self) -> QPixmap:
        frames = self._frames.get(self.state)
        if not frames:
            return self._fallback_pixmap(self.state)
        return frames[self._index % len(frames)]

    def on_frame(self, callback):
        """Register a callable(pixmap) that fires every frame tick."""
        self._callback = callback

    def stop(self):
        self._timer.stop()

    # ── internals ──────────────────────────────────────────────────────────
    def _advance(self):
        frames = self._frames.get(self.state)
        if frames:
            self._index = (self._index + 1) % len(frames)
        if self._callback:
            self._callback(self.current_pixmap())

    def _load_all_states(self):
        for state, folder in STATE_DIRS.items():
            path = os.path.join(self.sprites_dir, folder)
            frames = self._load_frames(path)
            if frames:
                self._frames[state] = frames

    def _load_frames(self, folder: str) -> list[QPixmap]:
        """Load all PNG/GIF frames from a folder, sorted by filename."""
        if not os.path.isdir(folder):
            return []
        exts  = (".png", ".gif", ".jpg", ".jpeg")
        files = sorted(
            f for f in os.listdir(folder)
            if f.lower().endswith(exts)
        )
        frames = []
        for fn in files:
            px = QPixmap(os.path.join(folder, fn))
            if not px.isNull():
                frames.append(
                    px.scaled(self.size, self.size,
                               Qt.AspectRatioMode.KeepAspectRatio,
                               Qt.TransformationMode.SmoothTransformation)
                )
        return frames

    def _fallback_pixmap(self, state: str) -> QPixmap:
        """Draw a solid-colour square with an emoji — visible without sprites."""
        colour, emoji = FALLBACK.get(state, ("#FFD700", "🐱"))
        px = QPixmap(self.size, self.size)
        px.fill(Qt.GlobalColor.transparent)
        painter = QPainter(px)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        # Circle background
        painter.setBrush(QColor(colour))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(5, 5, self.size - 10, self.size - 10)
        # Emoji
        font = QFont("Segoe UI Emoji", int(self.size * 0.38))
        painter.setFont(font)
        painter.setPen(QColor("#000000"))
        painter.drawText(px.rect(), Qt.AlignmentFlag.AlignCenter, emoji)
        painter.end()
        return px
