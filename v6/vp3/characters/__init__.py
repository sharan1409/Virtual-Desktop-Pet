"""
characters/__init__.py — Character switcher.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  HOW TO SWITCH YOUR PET CHARACTER
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Change ACTIVE_CHARACTER below and restart the app:

    "luffy"   → Monkey D. Luffy  (One Piece)
    "chopper" → Tony Tony Chopper (One Piece)

To add your own character:
  1. Create  characters/my_char.py  with a draw_pet() function
     (same signature as luffy.py)
  2. Add it to CHARACTER_MAP below
  3. Set ACTIVE_CHARACTER = "my_char"
"""

# ── CHANGE THIS LINE TO SWAP CHARACTER ────────────────────────────────────
ACTIVE_CHARACTER = "chopper"
# ──────────────────────────────────────────────────────────────────────────

CHARACTER_MAP = {
    "luffy"   : "characters.luffy",
    "chopper" : "characters.chopper",
}


def get_draw_fn():
    """Return the draw_pet() function for the active character."""
    import importlib
    module_path = CHARACTER_MAP.get(ACTIVE_CHARACTER, "characters.luffy")
    mod = importlib.import_module(module_path)
    return mod.draw_pet
