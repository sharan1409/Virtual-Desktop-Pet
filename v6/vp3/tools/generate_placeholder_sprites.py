"""
tools/generate_placeholder_sprites.py
--------------------------------------
Generates simple placeholder PNG sprite frames for all animation states.
Run this once to get visible sprites while you work on real artwork.

Usage:
    python tools/generate_placeholder_sprites.py
"""

import os
import sys

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("Pillow not installed. Run: pip install Pillow")
    sys.exit(1)

SIZE   = 100
STATES = {
    "idle":       ("#FFD700", "🐱", 4),
    "walk_right": ("#FFA500", "🐱", 6),
    "walk_left":  ("#FFA500", "🐱", 6),
    "sleep":      ("#87CEEB", "😴", 3),
    "happy":      ("#90EE90", "😊", 4),
    "sad":        ("#DDA0DD", "😢", 3),
    "surprised":  ("#FF6347", "😲", 2),
}

ROOT = os.path.join(os.path.dirname(__file__), "..", "assets", "sprites")


def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def make_frame(colour_hex: str, emoji: str, frame: int, total: int) -> Image.Image:
    img  = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Slight bobbing animation
    offset = int(4 * (frame / max(total - 1, 1) - 0.5))
    cx, cy = SIZE // 2, SIZE // 2 + offset

    rgb = hex_to_rgb(colour_hex)
    draw.ellipse([cx-38, cy-38, cx+38, cy+38], fill=(*rgb, 255))

    # Try to render emoji; fall back to "?" if font unavailable
    try:
        font = ImageFont.truetype("seguiemj.ttf", 38)
    except Exception:
        try:
            font = ImageFont.load_default()
        except Exception:
            font = None

    text = emoji
    if font:
        bbox = draw.textbbox((0, 0), text, font=font)
        tw   = bbox[2] - bbox[0]
        th   = bbox[3] - bbox[1]
        draw.text((cx - tw // 2, cy - th // 2), text, font=font, fill=(50, 50, 50, 230))
    return img


def main():
    for state, (colour, emoji, frames) in STATES.items():
        folder = os.path.join(ROOT, state)
        os.makedirs(folder, exist_ok=True)
        for i in range(frames):
            img  = make_frame(colour, emoji, i, frames)
            path = os.path.join(folder, f"frame_{i:02d}.png")
            img.save(path)
        print(f"  ✔  {state}: {frames} frames  →  {folder}")
    print("\nDone! Placeholder sprites generated.")


if __name__ == "__main__":
    main()
