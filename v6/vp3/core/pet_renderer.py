"""
core/pet_renderer.py — GIF/image renderer with dance, cry, and hide support.

States:
    happy / idle / walk_right / walk_left
        → chopper_happy GIF looping continuously
    dance
        → chopper_dance.gif (plays once, then callback)
    sad_cry
        → chopper_cry.gif (plays once, then switches to sad_hide)
    sad_hide
        → chopper_hide.png (static)
"""

import os
from PyQt6.QtGui  import QPixmap, QPainter
from PyQt6.QtCore import QTimer, Qt

_ASSETS = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets"
)

_HAPPY_FRAME_MS = 270   # ms per frame for happy GIF
_DANCE_FRAME_MS = 83    # ~12fps for dance (dance has 120 frames @ 10fps)
_CRY_FRAME_MS   = 100   # 10fps for cry GIF

_SAD_STATES = {"sad_cry", "sad_hide"}


class PetRenderer:
    def __init__(self, size: int = 120, fps: int = 12):
        self.size  = size
        self.state = "idle"

        self._frame_idx  = 0
        self._callback   = None
        self._on_dance_done = None   # called when dance animation finishes
        self._on_cry_done   = None   # called when cry animation finishes

        self._eye_x = 0.0
        self._eye_y = 0.0

        self._happy_frames: list[QPixmap] = []
        self._dance_frames: list[QPixmap] = []
        self._cry_frames:   list[QPixmap] = []
        self._hide_frame:   QPixmap | None = None
        self._load_images()

        # One timer — interval changes per state
        self._gif_timer = QTimer()
        self._gif_timer.timeout.connect(self._advance)
        self._gif_timer.start(_HAPPY_FRAME_MS)

    # ── Loading ────────────────────────────────────────────────────────────
    def _load_gif_frames(self, path: str) -> list[QPixmap]:
        """Load frames from an animated GIF using PIL."""
        frames = []
        try:
            from PIL import Image as PILImage
            import io
            gif = PILImage.open(path)
            for i in range(getattr(gif, 'n_frames', 1)):
                gif.seek(i)
                rgba = gif.convert("RGBA")
                buf = io.BytesIO()
                rgba.save(buf, format="PNG")
                buf.seek(0)
                px = QPixmap()
                px.loadFromData(buf.read())
                if not px.isNull():
                    frames.append(self._fit(px))
        except Exception as e:
            print(f"[PetRenderer] GIF load error for {path}: {e}")
        return frames

    def _load_images(self):
        # Happy frames: chopper_happy_00.png … chopper_happy_03.png
        for i in range(20):
            path = os.path.join(_ASSETS, f"chopper_happy_{i:02d}.png")
            if not os.path.exists(path):
                break
            px = QPixmap(path)
            if not px.isNull():
                self._happy_frames.append(self._fit(px))

        if self._happy_frames:
            print(f"[PetRenderer] happy: {len(self._happy_frames)} frames")
        else:
            px = QPixmap(self.size, self.size)
            px.fill(Qt.GlobalColor.transparent)
            self._happy_frames = [px]

        # Dance GIF
        dance_path = os.path.join(_ASSETS, "chopper_dance.gif")
        if os.path.exists(dance_path):
            self._dance_frames = self._load_gif_frames(dance_path)
            print(f"[PetRenderer] dance: {len(self._dance_frames)} frames")
        else:
            print(f"[PetRenderer] WARNING: chopper_dance.gif not found")
            self._dance_frames = self._happy_frames[:]

        # Cry GIF
        cry_path = os.path.join(_ASSETS, "chopper_cry.gif")
        if os.path.exists(cry_path):
            self._cry_frames = self._load_gif_frames(cry_path)
            print(f"[PetRenderer] cry: {len(self._cry_frames)} frames")
        else:
            print(f"[PetRenderer] WARNING: chopper_cry.gif not found")
            self._cry_frames = self._happy_frames[:]

        # Hide image
        hide_path = os.path.join(_ASSETS, "chopper_hide.png")
        if os.path.exists(hide_path):
            px = QPixmap(hide_path)
            if not px.isNull():
                self._hide_frame = self._fit(px)
                print(f"[PetRenderer] hide image loaded")
        
        if self._hide_frame is None:
            self._hide_frame = self._happy_frames[0]

    def _fit(self, px: QPixmap) -> QPixmap:
        return px.scaled(
            self.size, self.size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )

    # ── Public API ─────────────────────────────────────────────────────────
    def set_state(self, state: str, on_done=None):
        """
        Switch display state.
        on_done: callback fired when a one-shot animation (dance/cry) finishes.
        """
        self.state      = state
        self._frame_idx = 0

        if state == "dance":
            self._on_dance_done = on_done
            self._gif_timer.setInterval(_DANCE_FRAME_MS)
        elif state == "sad_cry":
            self._on_cry_done = on_done
            self._gif_timer.setInterval(_CRY_FRAME_MS)
        else:
            self._gif_timer.setInterval(_HAPPY_FRAME_MS)

    def set_eye_offset(self, ox: float, oy: float):
        pass  # kept for API compat

    def current_pixmap(self) -> QPixmap:
        return self._render()

    def on_frame(self, callback):
        self._callback = callback

    def stop(self):
        self._gif_timer.stop()

    def get_dance_duration_ms(self) -> int:
        """Total duration of dance animation in ms."""
        return len(self._dance_frames) * _DANCE_FRAME_MS

    def get_cry_duration_ms(self) -> int:
        """Total duration of cry animation in ms."""
        return len(self._cry_frames) * _CRY_FRAME_MS

    # ── Internal ───────────────────────────────────────────────────────────
    def _advance(self):
        """Advance frame; handle one-shot end for dance/cry."""
        if self.state == "dance":
            if self._dance_frames:
                self._frame_idx += 1
                if self._frame_idx >= len(self._dance_frames):
                    self._frame_idx = len(self._dance_frames) - 1
                    cb = self._on_dance_done
                    self._on_dance_done = None
                    if cb:
                        cb()
                    # Don't advance further — stay on last frame until state changes
        elif self.state == "sad_cry":
            if self._cry_frames:
                self._frame_idx += 1
                if self._frame_idx >= len(self._cry_frames):
                    self._frame_idx = len(self._cry_frames) - 1
                    cb = self._on_cry_done
                    self._on_cry_done = None
                    if cb:
                        cb()
        elif self.state == "sad_hide":
            pass  # static
        else:
            # looping happy/idle/walk
            if self._happy_frames:
                self._frame_idx = (self._frame_idx + 1) % len(self._happy_frames)

        if self._callback:
            self._callback(self._render())

    def _render(self) -> QPixmap:
        if self.state == "sad_hide":
            src = self._hide_frame
        elif self.state == "sad_cry":
            frames = self._cry_frames
            src = frames[min(self._frame_idx, len(frames) - 1)] if frames else self._hide_frame
        elif self.state == "dance":
            frames = self._dance_frames
            src = frames[min(self._frame_idx, len(frames) - 1)] if frames else self._happy_frames[0]
        else:
            src = self._happy_frames[self._frame_idx % len(self._happy_frames)]

        canvas = QPixmap(self.size, self.size)
        canvas.fill(Qt.GlobalColor.transparent)
        p = QPainter(canvas)
        x = (self.size - src.width())  // 2
        y = (self.size - src.height()) // 2
        p.drawPixmap(x, y, src)
        p.end()
        return canvas
