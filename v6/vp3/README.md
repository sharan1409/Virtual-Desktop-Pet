# 🏴‍☠️ One Piece Virtual Desktop Pet — Chopper Edition

A desktop pet featuring **Tony Tony Chopper** that lives on your screen.

## Features
- 🖼️ **Real Chopper images** for sad / happy moods (your uploaded PNGs/GIFs)
- 👀 **Eye tracking** — pupils follow your cursor in every other state
- 🚶 **Walking animation** with leg swing
- 😢 **Mood system** — goes SAD if ignored 1 min, HAPPY when you interact
- 🔑 **Ctrl+Shift+P** — show/unhide pet from anywhere on screen
- 📺 **Auto-hide in fullscreen** — hides during videos/meetings, restores after
- 🏆 **Persistent reaction game high score** saved in SQLite
- 💬 **AI Chat** via Gemini API

## Quick Start

```bash
pip install -r requirements.txt
python main.py
```

## If You Hide the Pet

**3 ways to bring it back:**
1. Press **Ctrl+Shift+P** (works from anywhere)
2. **Right-click** the system tray icon (bottom-right taskbar) → "Show Pet"
3. **Click** the tray icon once

## Switching Characters

Open `characters/__init__.py`:
```python
ACTIVE_CHARACTER = "luffy"    # or "chopper"
```

## Auto-hide Fullscreen
The pet automatically hides when you go fullscreen (YouTube, Netflix, Google Meet,
games, presentations). It reappears when you exit fullscreen. No action needed.

## Adding Custom Images
Place images in the `assets/` folder:
- `chopper_sad.png`         → shown when pet is sad (no interaction for 1 min)
- `chopper_happy_00.png`    → happy animation frame 1
- `chopper_happy_01.png`    → happy animation frame 2
- etc. (any number of frames)

## Gemini API Key
Edit `config.py`:
```python
GEMINI_API_KEY = "your-key-here"
```
