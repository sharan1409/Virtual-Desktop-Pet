"""
features/gemini_chat.py — Gemini API integration (google-generativeai SDK).

Keeps a rolling conversation buffer so Gemini remembers context within a session.
"""

import threading
from typing import Callable

try:
    from google import genai
    from google.genai import types as genai_types
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

from config import GEMINI_API_KEY, GEMINI_MODEL, PET_PERSONALITY, PET_NAME


class GeminiChat:
    """
    Wraps the Gemini generative model (google-genai SDK).

    Usage
    -----
    chat = GeminiChat(db)
    chat.send("Hello!", on_reply=lambda text: print(text), on_error=lambda e: print(e))
    """

    def __init__(self, db):
        self.db     = db
        self._chat  = None
        self._client = None

        if not GEMINI_AVAILABLE:
            return

        if GEMINI_API_KEY == "YOUR_GEMINI_API_KEY_HERE":
            return  # Not configured — handled gracefully in send()

        try:
            self._client = genai.Client(api_key=GEMINI_API_KEY)
            self._chat   = self._client.chats.create(
                model=GEMINI_MODEL,
                config=genai_types.GenerateContentConfig(
                    system_instruction=PET_PERSONALITY,
                ),
            )
        except Exception:
            self._client = None
            self._chat   = None

    # ── Public ─────────────────────────────────────────────────────────────
    def send(self, user_text: str,
             on_reply: Callable[[str], None],
             on_error: Callable[[str], None]):
        """Send a message asynchronously; call on_reply or on_error on the main thread."""
        threading.Thread(
            target=self._worker,
            args=(user_text, on_reply, on_error),
            daemon=True
        ).start()

    def clear_history(self):
        # Re-create the chat session to reset history
        if GEMINI_AVAILABLE and self._client:
            try:
                self._chat = self._client.chats.create(
                    model=GEMINI_MODEL,
                    config=genai_types.GenerateContentConfig(
                        system_instruction=PET_PERSONALITY,
                    ),
                )
            except Exception:
                pass

    # ── Worker (background thread) ─────────────────────────────────────────
    def _worker(self, user_text: str, on_reply, on_error):
        try:
            reply = self._call_api(user_text)
            self.db.save_message("user",      user_text)
            self.db.save_message("assistant", reply)
            on_reply(reply)
        except Exception as exc:
            on_error(str(exc))

    def _call_api(self, user_text: str) -> str:
        if not GEMINI_AVAILABLE:
            return (
                "⚠️  google-genai is not installed.\n"
                "Run: pip install google-genai"
            )

        if GEMINI_API_KEY == "YOUR_GEMINI_API_KEY_HERE":
            return (
                f"Hi! I'm {PET_NAME} 🐱  "
                "(Set your Gemini API key in config.py to enable real AI chat!)"
            )

        if self._chat is None:
            return "⚠️  Could not connect to Gemini. Check your API key in config.py."

        # Append mood context
        mood     = self.db.get_mood()
        full_msg = f"[User mood context: my mood is {mood}/100] {user_text}"
        response = self._chat.send_message(full_msg)
        return response.text
