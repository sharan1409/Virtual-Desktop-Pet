"""
core/fullscreen_detector.py — Hide pet only when specific apps are running in the foreground.

Target apps (hide pet when any of these is the active/foreground window):
  • Microsoft Teams   (Teams.exe  / ms-teams.exe)
  • SpaceClaim        (SpaceClaim.exe)
  • Google Meet       (runs inside browser — detected by window title containing
                       "Meet" on a known browser process)

Works on Windows via ctypes win32 API:
  GetForegroundWindow → GetWindowText (title) + GetWindowThreadProcessId →
  QueryFullProcessImageName (exe name)

Returns:
  should_hide() → bool   True = pet should be hidden
"""

import platform
import ctypes
import ctypes.wintypes
import os

_IS_WINDOWS = platform.system() == "Windows"

# ── Process names that always trigger hide (case-insensitive) ──────────────
_HIDE_EXE = {
    "teams.exe",
    "ms-teams.exe",
    "msteams.exe",          # older Teams installer name
    "teams2.exe",           # Teams 2.0 / new Teams
    "spaceclaim.exe",
}

# ── Browser process names for Google Meet title detection ──────────────────
_BROWSER_EXE = {
    "chrome.exe",
    "brave.exe",
    "msedge.exe",
    "firefox.exe",
    "opera.exe",
    "vivaldi.exe",
}

# Window title substrings that identify a Google Meet tab as foreground
_MEET_TITLE_KEYWORDS = (
    "meet.google.com",
    "google meet",
    "– meet",      # "Your name – Meet" Chrome title format
    "| meet",
)


# ── Windows API setup ──────────────────────────────────────────────────────
if _IS_WINDOWS:
    try:
        _user32   = ctypes.windll.user32
        _kernel32 = ctypes.windll.kernel32
        _psapi    = ctypes.windll.psapi

        PROCESS_QUERY_LIMITED_INFORMATION = 0x1000

        def _get_foreground_info():
            """
            Returns (exe_name_lower, window_title_lower) for the foreground window,
            or ("", "") on any failure.
            """
            hwnd = _user32.GetForegroundWindow()
            if not hwnd:
                return "", ""

            # Window title
            buf = ctypes.create_unicode_buffer(512)
            _user32.GetWindowTextW(hwnd, buf, 512)
            title = buf.value.lower()

            # Process name
            pid = ctypes.wintypes.DWORD()
            _user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            h_proc = _kernel32.OpenProcess(
                PROCESS_QUERY_LIMITED_INFORMATION, False, pid
            )
            exe = ""
            if h_proc:
                exe_buf = ctypes.create_unicode_buffer(512)
                size    = ctypes.wintypes.DWORD(512)
                if _kernel32.QueryFullProcessImageNameW(h_proc, 0, exe_buf, ctypes.byref(size)):
                    exe = os.path.basename(exe_buf.value).lower()
                _kernel32.CloseHandle(h_proc)

            return exe, title

        _api_available = True

    except Exception as e:
        print(f"[fullscreen_detector] Win32 API unavailable: {e}")
        _api_available = False
else:
    _api_available = False


# ── Public API ─────────────────────────────────────────────────────────────
def should_hide() -> bool:
    """
    Returns True if the current foreground app is one of the target apps
    (Teams, SpaceClaim, or a browser showing Google Meet).

    Returns False on non-Windows or if the API is unavailable.
    """
    if not _IS_WINDOWS or not _api_available:
        return False

    try:
        exe, title = _get_foreground_info()

        # Direct exe match — Teams or SpaceClaim
        if exe in _HIDE_EXE:
            return True

        # Browser showing Google Meet tab
        if exe in _BROWSER_EXE:
            for kw in _MEET_TITLE_KEYWORDS:
                if kw in title:
                    return True

        return False

    except Exception:
        return False
