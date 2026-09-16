"""
characters/luffy.py — Monkey D. Luffy sprite drawn with QPainter.

This is the CHARACTER FILE. To swap to a different One Piece character,
create a new file (e.g. characters/chopper.py) with the same interface:

    draw_pet(painter, size, state, walk_frame, eye_offset_x, eye_offset_y)

Then change ACTIVE_CHARACTER in characters/__init__.py.

States handled:
    idle | walk_right | walk_left | happy | sad | sleep | surprised
"""

from PyQt6.QtGui import QPainter, QColor, QBrush, QPen, QFont, QPainterPath
from PyQt6.QtCore import Qt, QRect, QPoint

# ── Luffy colour palette ───────────────────────────────────────────────────
SKIN      = QColor("#F4C27A")
SKIN_DARK = QColor("#E8A85E")
HAT_RED   = QColor("#CC2222")
HAT_BAND  = QColor("#FFD700")
SHIRT_RED = QColor("#DD1111")
SHORTS    = QColor("#2244AA")
SHOES     = QColor("#1A1A1A")
SCAR      = QColor("#CC3333")
HAIR      = QColor("#1A0800")
WHITE     = QColor("#FFFFFF")
BLACK     = QColor("#111111")
SMILE_COL = QColor("#111111")
BLUSH     = QColor("#FF9999")
SHADOW    = QColor(0, 0, 0, 40)


def draw_pet(painter: QPainter, size: int, state: str,
             walk_frame: int = 0,
             eye_offset_x: float = 0.0,
             eye_offset_y: float = 0.0):
    """
    Main entry-point called by PetRenderer every frame.

    Parameters
    ----------
    painter       : active QPainter on the target pixmap
    size          : canvas size (square)
    state         : animation state string
    walk_frame    : 0-7 cycling walk frame counter
    eye_offset_x  : horizontal pupil offset  (-1.0 … +1.0)
    eye_offset_y  : vertical pupil offset    (-1.0 … +1.0)
    """
    s = size
    p = painter
    p.setRenderHint(QPainter.RenderHint.Antialiasing)

    # Mirror the whole canvas for walk_left
    if state == "walk_left":
        p.save()
        p.translate(s, 0)
        p.scale(-1, 1)

    _draw_luffy(p, s, state, walk_frame, eye_offset_x, eye_offset_y)

    if state == "walk_left":
        p.restore()


# ── Internal drawing helpers ───────────────────────────────────────────────

def _c(painter, color):
    painter.setBrush(QBrush(color))
    painter.setPen(Qt.PenStyle.NoPen)


def _outline(painter, color=BLACK, width=1.5):
    painter.setPen(QPen(color, width))
    painter.setBrush(Qt.BrushStyle.NoBrush)


def _draw_luffy(p, s, state, wf, ex, ey):
    # Layout constants (all relative to size)
    cx      = s * 0.50          # horizontal centre
    head_y  = s * 0.14          # top of head
    head_r  = s * 0.22          # head radius
    body_y  = s * 0.52          # top of body
    body_h  = s * 0.22          # body height
    body_w  = s * 0.32

    # --- Walk leg offsets ---
    leg_swing = 0
    if state in ("walk_right", "walk_left"):
        import math
        leg_swing = math.sin(wf * 0.8) * (s * 0.07)

    # ── Shadow ────────────────────────────────────────────────────────
    _c(p, SHADOW)
    p.drawEllipse(int(cx - s*0.22), int(s*0.90), int(s*0.44), int(s*0.07))

    # ── Legs ──────────────────────────────────────────────────────────
    _draw_legs(p, s, cx, body_y + body_h, leg_swing, state)

    # ── Body / shirt ─────────────────────────────────────────────────
    _c(p, SHIRT_RED)
    p.drawRoundedRect(int(cx - body_w/2), int(body_y),
                      int(body_w), int(body_h), 8, 8)

    # ── Arms ──────────────────────────────────────────────────────────
    _draw_arms(p, s, cx, body_y, body_h, wf, state)

    # ── Head ──────────────────────────────────────────────────────────
    _c(p, SKIN)
    p.drawEllipse(int(cx - head_r), int(head_y),
                  int(head_r*2), int(head_r*2))

    # ── Hat ───────────────────────────────────────────────────────────
    _draw_hat(p, s, cx, head_y, head_r)

    # ── Face ──────────────────────────────────────────────────────────
    face_cx = cx
    face_cy = head_y + head_r * 1.0
    _draw_face(p, s, face_cx, face_cy, head_r, state, ex, ey)


def _draw_hat(p, s, cx, head_y, head_r):
    # Brim
    _c(p, HAT_RED)
    brim_w = head_r * 2.6
    brim_h = head_r * 0.28
    p.drawEllipse(int(cx - brim_w/2), int(head_y + head_r*0.55),
                  int(brim_w), int(brim_h))
    # Crown
    _c(p, HAT_RED)
    crown_w = head_r * 1.8
    crown_h = head_r * 1.0
    p.drawEllipse(int(cx - crown_w/2), int(head_y - crown_h * 0.55),
                  int(crown_w), int(crown_h))
    # Gold band
    _c(p, HAT_BAND)
    p.drawRect(int(cx - crown_w/2), int(head_y + head_r*0.40),
               int(crown_w), int(head_r*0.22))


def _draw_face(p, s, cx, cy, head_r, state, ex, ey):
    # Scar under left eye
    pen = QPen(SCAR, max(1, int(s*0.015)))
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    sx = cx - head_r * 0.25
    sy = cy + head_r * 0.10
    p.drawLine(int(sx), int(sy - head_r*0.08), int(sx + head_r*0.04), int(sy + head_r*0.12))

    # Blush marks
    _c(p, BLUSH)
    blush_r = int(head_r * 0.14)
    p.setOpacity(0.55)
    p.drawEllipse(int(cx - head_r*0.52), int(cy + head_r*0.18), blush_r, blush_r)
    p.drawEllipse(int(cx + head_r*0.38), int(cy + head_r*0.18), blush_r, blush_r)
    p.setOpacity(1.0)

    # Eyes
    eye_spacing = head_r * 0.36
    eye_y       = cy - head_r * 0.08
    eye_r       = head_r * 0.17

    if state == "sleep":
        _draw_sleep_eyes(p, cx, eye_y, eye_spacing, eye_r)
    elif state == "sad":
        _draw_sad_eyes(p, cx, eye_y, eye_spacing, eye_r, ex, ey)
    elif state == "happy":
        _draw_happy_eyes(p, cx, eye_y, eye_spacing, eye_r)
    else:
        _draw_normal_eyes(p, cx, eye_y, eye_spacing, eye_r, ex, ey)

    # Mouth
    _draw_mouth(p, cx, cy, head_r, state)


def _draw_normal_eyes(p, cx, ey_y, spacing, eye_r, ex, oy):
    for side in (-1, 1):
        ecx = cx + side * spacing
        # White of eye
        _c(p, WHITE)
        p.drawEllipse(int(ecx - eye_r), int(ey_y - eye_r),
                      int(eye_r*2), int(eye_r*2))
        # Outline
        _outline(p, BLACK, 1.0)
        p.drawEllipse(int(ecx - eye_r), int(ey_y - eye_r),
                      int(eye_r*2), int(eye_r*2))
        # Pupil (tracks cursor)
        pupil_r = eye_r * 0.52
        max_off = eye_r * 0.38
        px_ = ecx + ex * max_off
        py_ = ey_y + oy * max_off
        _c(p, BLACK)
        p.drawEllipse(int(px_ - pupil_r), int(py_ - pupil_r),
                      int(pupil_r*2), int(pupil_r*2))
        # Shine
        _c(p, WHITE)
        shine_r = int(pupil_r * 0.38)
        p.drawEllipse(int(px_ - pupil_r*0.25), int(py_ - pupil_r*0.35),
                      shine_r, shine_r)


def _draw_happy_eyes(p, cx, ey_y, spacing, eye_r):
    """Big bright happy U-curve eyes."""
    for side in (-1, 1):
        ecx = cx + side * spacing
        pen = QPen(BLACK, max(1.5, eye_r*0.35))
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)
        # Draw upside-down arc (happy squint)
        r = int(eye_r * 1.0)
        p.drawArc(int(ecx - r), int(ey_y - r//2), r*2, r*2, 0*16, -180*16)


def _draw_sad_eyes(p, cx, ey_y, spacing, eye_r, ex, oy):
    """Droopy sad eyes with downward slant brows."""
    for side in (-1, 1):
        ecx = cx + side * spacing
        # White
        _c(p, WHITE)
        p.drawEllipse(int(ecx - eye_r), int(ey_y - eye_r + eye_r*0.2),
                      int(eye_r*2), int(eye_r*2))
        _outline(p, BLACK, 1.0)
        p.drawEllipse(int(ecx - eye_r), int(ey_y - eye_r + eye_r*0.2),
                      int(eye_r*2), int(eye_r*2))
        # Pupil (still tracks)
        pupil_r = eye_r * 0.45
        max_off = eye_r * 0.30
        _c(p, BLACK)
        p.drawEllipse(int(ecx + ex*max_off - pupil_r),
                      int(ey_y + eye_r*0.2 + oy*max_off - pupil_r),
                      int(pupil_r*2), int(pupil_r*2))
        # Sad brow
        pen = QPen(BLACK, max(1.5, eye_r*0.30))
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(pen)
        brow_sx = ecx - eye_r*0.7
        brow_ex = ecx + eye_r*0.7
        brow_y_s = ey_y - eye_r * 1.4 + side * eye_r * 0.25   # slant inward
        brow_y_e = ey_y - eye_r * 1.4 - side * eye_r * 0.25
        p.drawLine(int(brow_sx), int(brow_y_s), int(brow_ex), int(brow_y_e))


def _draw_sleep_eyes(p, cx, ey_y, spacing, eye_r):
    pen = QPen(BLACK, max(1.5, eye_r*0.35))
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    for side in (-1, 1):
        ecx = cx + side * spacing
        r = int(eye_r * 1.0)
        p.drawArc(int(ecx - r), int(ey_y - r//2), r*2, r*2, 0*16, 180*16)


def _draw_mouth(p, cx, cy, head_r, state):
    pen = QPen(SMILE_COL, max(1.5, head_r*0.08))
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)

    mouth_y = cy + head_r * 0.42
    mouth_w = int(head_r * 0.82)

    if state in ("happy", "walk_right", "walk_left", "idle"):
        # Big Luffy grin
        _c(p, BLACK)
        path = QPainterPath()
        path.moveTo(cx - mouth_w/2, mouth_y - head_r*0.05)
        path.quadTo(cx, mouth_y + head_r*0.32, cx + mouth_w/2, mouth_y - head_r*0.05)
        path.quadTo(cx, mouth_y + head_r*0.12, cx - mouth_w/2, mouth_y - head_r*0.05)
        p.fillPath(path, QBrush(BLACK))
        # Teeth
        _c(p, WHITE)
        teeth_w = mouth_w * 0.55
        p.drawRect(int(cx - teeth_w/2), int(mouth_y - head_r*0.02),
                   int(teeth_w), int(head_r*0.14))

    elif state == "sad":
        p.setPen(pen)
        p.drawArc(int(cx - mouth_w//2), int(mouth_y),
                  mouth_w, int(head_r*0.28), 0*16, -180*16)

    elif state == "sleep":
        p.drawLine(int(cx - mouth_w//3), int(mouth_y),
                   int(cx + mouth_w//3), int(mouth_y))

    elif state == "surprised":
        _c(p, BLACK)
        p.drawEllipse(int(cx - head_r*0.18), int(mouth_y - head_r*0.05),
                      int(head_r*0.36), int(head_r*0.32))
    else:
        # neutral small smile
        p.setPen(pen)
        p.drawArc(int(cx - mouth_w//3), int(mouth_y - head_r*0.1),
                  int(mouth_w*0.66), int(head_r*0.24), 0*16, -180*16)


def _draw_legs(p, s, cx, leg_top, swing, state):
    leg_w  = s * 0.115
    leg_h  = s * 0.20
    shoe_h = s * 0.07
    gap    = s * 0.06

    for side, sign in ((-1, -1), (1, 1)):
        lx = cx + side * (leg_w/2 + gap/2)
        # Vertical swing offset for walk animation
        if state in ("walk_right", "walk_left"):
            offset_y = swing * sign
        else:
            offset_y = 0

        # Shorts (blue)
        _c(p, SHORTS)
        p.drawRoundedRect(int(lx - leg_w/2), int(leg_top + offset_y),
                          int(leg_w), int(leg_h * 0.55), 4, 4)
        # Leg skin
        _c(p, SKIN)
        p.drawRoundedRect(int(lx - leg_w/2 + 2), int(leg_top + leg_h*0.45 + offset_y),
                          int(leg_w - 4), int(leg_h * 0.55), 3, 3)
        # Shoe
        _c(p, SHOES)
        p.drawRoundedRect(int(lx - leg_w/2 - 2), int(leg_top + leg_h + offset_y - 2),
                          int(leg_w + 4), int(shoe_h), 4, 4)


def _draw_arms(p, s, cx, body_y, body_h, wf, state):
    arm_w = s * 0.09
    arm_h = s * 0.20
    shoulder_y = body_y + body_h * 0.1

    import math
    for side, sign in ((-1, -1), (1, 1)):
        ax = cx + sign * (s * 0.185)

        if state in ("walk_right", "walk_left"):
            arm_angle = math.sin(wf * 0.8 + (0 if sign > 0 else math.pi)) * 0.35
        elif state == "happy":
            arm_angle = -0.6 * sign   # arms raised
        elif state == "sad":
            arm_angle = 0.4
        else:
            arm_angle = 0.15

        # Draw upper arm rotated around shoulder joint
        p.save()
        p.translate(ax, shoulder_y)
        p.rotate(math.degrees(arm_angle) * sign)
        _c(p, SHIRT_RED)
        p.drawRoundedRect(int(-arm_w/2), 0, int(arm_w), int(arm_h*0.55), 4, 4)
        # Forearm (skin)
        _c(p, SKIN)
        p.drawRoundedRect(int(-arm_w/2 + 1), int(arm_h*0.50),
                          int(arm_w - 2), int(arm_h*0.55), 3, 3)
        p.restore()
