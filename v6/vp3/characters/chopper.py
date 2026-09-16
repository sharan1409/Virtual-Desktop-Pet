"""
characters/chopper.py — Tony Tony Chopper sprite drawn with QPainter.

SWAP INSTRUCTIONS
-----------------
To use Chopper instead of Luffy, open characters/__init__.py and change:

    ACTIVE_CHARACTER = "luffy"
to:
    ACTIVE_CHARACTER = "chopper"

Same interface as luffy.py — draw_pet() is the only required function.
"""

from PyQt6.QtGui import QPainter, QColor, QBrush, QPen, QPainterPath
from PyQt6.QtCore import Qt

# Chopper palette
FUR_BROWN  = QColor("#7B4F2E")
FUR_PINK   = QColor("#F5C2C2")
FUR_WHITE  = QColor("#F5F0EB")
HAT_PINK   = QColor("#E8A0B0")
HAT_BAND   = QColor("#D4507A")
NOSE       = QColor("#C06060")
BLACK      = QColor("#111111")
WHITE      = QColor("#FFFFFF")
BLUSH      = QColor("#FF9999")
SHADOW     = QColor(0, 0, 0, 40)
EYES_COL   = QColor("#2E1A0E")


def draw_pet(painter: QPainter, size: int, state: str,
             walk_frame: int = 0,
             eye_offset_x: float = 0.0,
             eye_offset_y: float = 0.0):
    s = size
    p = painter
    p.setRenderHint(QPainter.RenderHint.Antialiasing)

    if state == "walk_left":
        p.save()
        p.translate(s, 0)
        p.scale(-1, 1)

    _draw_chopper(p, s, state, walk_frame, eye_offset_x, eye_offset_y)

    if state == "walk_left":
        p.restore()


def _c(painter, color):
    painter.setBrush(QBrush(color))
    painter.setPen(Qt.PenStyle.NoPen)


def _draw_chopper(p, s, state, wf, ex, ey):
    import math
    cx     = s * 0.50
    body_y = s * 0.50
    body_w = s * 0.36
    body_h = s * 0.28
    head_r = s * 0.26
    head_y = s * 0.18

    # Shadow
    _c(p, SHADOW)
    p.drawEllipse(int(cx - s*0.22), int(s*0.90), int(s*0.44), int(s*0.07))

    # Legs
    leg_swing = math.sin(wf * 0.8) * (s * 0.06) if state in ("walk_right","walk_left") else 0
    _draw_chopper_legs(p, s, cx, body_y + body_h, leg_swing, state)

    # Body
    _c(p, FUR_BROWN)
    p.drawRoundedRect(int(cx - body_w/2), int(body_y), int(body_w), int(body_h), 10, 10)

    # White chest
    _c(p, FUR_WHITE)
    p.drawEllipse(int(cx - body_w*0.28), int(body_y + body_h*0.15),
                  int(body_w*0.56), int(body_h*0.72))

    # Arms
    for side, sign in ((-1,-1),(1,1)):
        swing = math.sin(wf*0.8 + (0 if sign>0 else math.pi)) * 0.3 if state in ("walk_right","walk_left") else 0.1
        ax = cx + sign * s*0.20
        p.save()
        p.translate(ax, body_y + s*0.04)
        p.rotate(math.degrees(swing)*sign*1.5)
        _c(p, FUR_BROWN)
        p.drawRoundedRect(int(-s*0.06), 0, int(s*0.12), int(s*0.18), 5, 5)
        p.restore()

    # Head
    _c(p, FUR_BROWN)
    p.drawEllipse(int(cx - head_r), int(head_y), int(head_r*2), int(head_r*2))

    # White face patch
    _c(p, FUR_WHITE)
    p.drawEllipse(int(cx - head_r*0.62), int(head_y + head_r*0.45),
                  int(head_r*1.24), int(head_r*1.1))

    # Ears / antlers
    _draw_chopper_hat(p, s, cx, head_y, head_r)

    # Face
    _draw_chopper_face(p, s, cx, head_y + head_r*1.0, head_r, state, ex, ey)


def _draw_chopper_hat(p, s, cx, head_y, head_r):
    # Ear horns (small)
    _c(p, FUR_BROWN)
    for side in (-1, 1):
        ex_ = cx + side * head_r * 0.70
        p.drawEllipse(int(ex_ - s*0.06), int(head_y - s*0.04),
                      int(s*0.12), int(s*0.10))
    # Pink hat
    _c(p, HAT_PINK)
    brim_w = head_r * 2.4
    p.drawEllipse(int(cx - brim_w/2), int(head_y + head_r*0.45),
                  int(brim_w), int(head_r*0.25))
    crown_w = head_r * 1.6
    p.drawEllipse(int(cx - crown_w/2), int(head_y - head_r*0.45),
                  int(crown_w), int(head_r*0.9))
    # Band
    _c(p, HAT_BAND)
    p.drawRect(int(cx - crown_w/2), int(head_y + head_r*0.28),
               int(crown_w), int(head_r*0.22))
    # Cross on hat
    p.setPen(QPen(WHITE, max(1, int(s*0.02))))
    cx2, cy2 = int(cx), int(head_y + head_r*0.08)
    hw = int(s*0.07)
    p.drawLine(cx2, cy2-hw, cx2, cy2+hw)
    p.drawLine(cx2-hw, cy2, cx2+hw, cy2)


def _draw_chopper_face(p, s, cx, cy, head_r, state, ex, ey):
    # Nose
    _c(p, NOSE)
    p.drawEllipse(int(cx - head_r*0.12), int(cy + head_r*0.05),
                  int(head_r*0.24), int(head_r*0.16))

    # Blush
    _c(p, BLUSH)
    p.setOpacity(0.55)
    br = int(head_r*0.16)
    p.drawEllipse(int(cx - head_r*0.52), int(cy + head_r*0.22), br, br)
    p.drawEllipse(int(cx + head_r*0.36), int(cy + head_r*0.22), br, br)
    p.setOpacity(1.0)

    eye_spacing = head_r * 0.38
    eye_y = cy - head_r * 0.14
    eye_r = head_r * 0.19

    if state == "sleep":
        pen = QPen(BLACK, max(1.5, eye_r*0.35))
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)
        for side in (-1,1):
            ecx = cx + side*eye_spacing
            r = int(eye_r)
            p.drawArc(int(ecx-r), int(eye_y-r//2), r*2, r*2, 0, 180*16)
    elif state == "happy":
        pen = QPen(BLACK, max(1.5, eye_r*0.35))
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)
        for side in (-1,1):
            ecx = cx + side*eye_spacing
            r = int(eye_r)
            p.drawArc(int(ecx-r), int(eye_y-r//2), r*2, r*2, 0, -180*16)
    else:
        for side in (-1,1):
            ecx = cx + side*eye_spacing
            _c(p, WHITE)
            p.drawEllipse(int(ecx-eye_r), int(eye_y-eye_r), int(eye_r*2), int(eye_r*2))
            p.setPen(QPen(BLACK, 1.0))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawEllipse(int(ecx-eye_r), int(eye_y-eye_r), int(eye_r*2), int(eye_r*2))
            pupil_r = eye_r * 0.50
            max_off = eye_r * 0.35
            _c(p, EYES_COL)
            p.drawEllipse(int(ecx+ex*max_off-pupil_r), int(eye_y+ey*max_off-pupil_r),
                          int(pupil_r*2), int(pupil_r*2))
            _c(p, WHITE)
            sr = int(pupil_r*0.35)
            p.drawEllipse(int(ecx+ex*max_off-pupil_r*0.2), int(eye_y+ey*max_off-pupil_r*0.35), sr, sr)

    # Mouth
    pen = QPen(BLACK, max(1.5, head_r*0.07))
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    mouth_y = cy + head_r*0.42
    mw = int(head_r*0.60)
    if state == "sad":
        p.drawArc(int(cx-mw//2), int(mouth_y), mw, int(head_r*0.24), 0, -180*16)
    elif state == "sleep":
        p.drawLine(int(cx-mw//3), int(mouth_y), int(cx+mw//3), int(mouth_y))
    else:
        p.drawArc(int(cx-mw//2), int(mouth_y-head_r*0.12), mw, int(head_r*0.24), 0, -180*16)


def _draw_chopper_legs(p, s, cx, leg_top, swing, state):
    leg_w = s*0.11
    leg_h = s*0.15
    gap   = s*0.055
    for side, sign in ((-1,-1),(1,1)):
        lx = cx + side*(leg_w/2 + gap/2)
        off = swing*sign if state in ("walk_right","walk_left") else 0
        _c(p, FUR_BROWN)
        p.drawRoundedRect(int(lx-leg_w/2), int(leg_top+off), int(leg_w), int(leg_h), 4,4)
        # Hooves
        _c(p, BLACK)
        p.drawRoundedRect(int(lx-leg_w/2-2), int(leg_top+leg_h+off-2), int(leg_w+4), int(s*0.06), 3,3)
