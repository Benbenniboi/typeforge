from __future__ import annotations
from pathlib import Path

APP_NAME = "TypeForge"
VERSION = "1.0.0"

# Data directories
APP_DIR = Path.home() / ".typeforge"
DB_PATH = APP_DIR / "typeforge.db"
EXPORTS_DIR = APP_DIR / "exports"

# Bundled data (relative to app package)
_HERE = Path(__file__).parent
DATA_DIR = _HERE / "data"
WORDS_DIR = DATA_DIR / "words"
QUOTES_FILE = DATA_DIR / "quotes" / "quotes.json"
LESSONS_DIR = DATA_DIR / "lessons"
CURRICULUM_FILE = LESSONS_DIR / "curriculum.json"

# Assets
ASSETS_DIR = _HERE.parent / "assets"
FONTS_DIR = ASSETS_DIR / "fonts"
SOUNDS_DIR = ASSETS_DIR / "sounds"
ICONS_DIR = ASSETS_DIR / "icons"

# Ensure runtime dirs exist
APP_DIR.mkdir(parents=True, exist_ok=True)
EXPORTS_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_SETTINGS = {
    "theme": "dark",
    "font_size": "18",
    "caret_style": "line",
    "smooth_caret": "true",
    "quick_restart_key": "tab",
    "stop_on_error": "false",
    "hint_delay": "3",
    "show_live_wpm": "true",
    "show_raw_wpm": "true",
    "sound_enabled": "false",
    "sound_style": "soft",
    "sound_volume": "50",
    "window_width": "1200",
    "window_height": "750",
    "window_x": "-1",
    "window_y": "-1",
    "last_mode": "words",
    "last_word_count": "25",
    "last_duration": "60",
    "last_word_list": "english_200",
    "punctuation": "false",
    "numbers_mode": "false",
}

FINGER_MAP = {
    "a": "left_pinky", "q": "left_pinky", "z": "left_pinky",
    "1": "left_pinky", "`": "left_pinky",
    "s": "left_ring", "w": "left_ring", "x": "left_ring", "2": "left_ring",
    "d": "left_middle", "e": "left_middle", "c": "left_middle", "3": "left_middle",
    "f": "left_index", "g": "left_index", "r": "left_index", "t": "left_index",
    "v": "left_index", "b": "left_index", "4": "left_index", "5": "left_index",
    "h": "right_index", "j": "right_index", "y": "right_index", "u": "right_index",
    "n": "right_index", "m": "right_index", "6": "right_index", "7": "right_index",
    "k": "right_middle", "i": "right_middle", ",": "right_middle", "8": "right_middle",
    "l": "right_ring", "o": "right_ring", ".": "right_ring", "9": "right_ring",
    ";": "right_pinky", "p": "right_pinky", "/": "right_pinky", "0": "right_pinky",
    "'": "right_pinky", "[": "right_pinky", "]": "right_pinky", "\\": "right_pinky",
    "-": "right_pinky", "=": "right_pinky",
    " ": "thumb",
}
