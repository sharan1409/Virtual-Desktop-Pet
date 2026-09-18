"""
Configuration — edit this file to set your API key and preferences.
"""

# ─────────────────────────────────────────────
#  Gemini API
# ─────────────────────────────────────────────
GEMINI_API_KEY = "_____"   # <-- paste your key
GEMINI_MODEL   = "gemini-2.0-flash"

# ─────────────────────────────────────────────
#  Pet personality (sent as system context)
# ─────────────────────────────────────────────
PET_NAME = "Pixel"
PET_PERSONALITY = f"""
You are {PET_NAME}, a cute and playful virtual desktop pet.
You live on the user's computer screen and love to chat, help with tasks,
and keep the user company. You are enthusiastic, supportive, and a little silly.
Keep responses short (1-3 sentences) and use occasional emojis.
You can see the user's mood and remind them to take breaks or finish tasks.
"""

# ─────────────────────────────────────────────
#  Window & display
# ─────────────────────────────────────────────
PET_SIZE          = 120        # px — width & height of the pet window
CHAT_BUBBLE_WIDTH = 320        # px
CHAT_BUBBLE_HEIGHT= 420        # px

# ─────────────────────────────────────────────
#  Animation
# ─────────────────────────────────────────────
ANIMATION_FPS      = 8         # frames per second
WALK_SPEED         = 1         # px per tick
IDLE_TIMEOUT_SECS  = 60        # seconds before pet becomes sad (no interaction)

# ─────────────────────────────────────────────
#  Mood system
# ─────────────────────────────────────────────
MOOD_DECAY_INTERVAL = 300      # seconds between mood decay ticks
MOOD_DECAY_AMOUNT   = 5        # points lost per tick (0-100 scale)
INTERACTION_MOOD_BOOST = 10    # points gained on user interaction

# ─────────────────────────────────────────────
#  Reminders
# ─────────────────────────────────────────────
REMINDER_CHECK_INTERVAL = 60   # seconds between reminder checks

# ─────────────────────────────────────────────
#  Database
# ─────────────────────────────────────────────
DB_PATH = "virtual_pet.db"
