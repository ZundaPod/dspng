"""
Persistent user settings stored at ~/.dspng/settings.json.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .themes import Accent, ThemeMode

_DEFAULTS: dict[str, Any] = {
    "theme_mode": ThemeMode.DARK.value,
    "accent": Accent.BLUE.value,
}

SETTINGS_DIR = Path.home() / ".dspng"
SETTINGS_FILE = SETTINGS_DIR / "settings.json"


def load() -> dict[str, Any]:
    """Load settings from disk, falling back to defaults."""
    try:
        data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
        # Merge with defaults so new keys are always present.
        return {**_DEFAULTS, **data}
    except (FileNotFoundError, json.JSONDecodeError):
        return dict(_DEFAULTS)


def save(settings: dict[str, Any]) -> None:
    """Persist settings to disk."""
    SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
    SETTINGS_FILE.write_text(
        json.dumps(settings, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def get_mode(settings: dict[str, Any]) -> ThemeMode:
    raw = settings.get("theme_mode", _DEFAULTS["theme_mode"])
    try:
        return ThemeMode(raw)
    except ValueError:
        return ThemeMode.DARK


def get_accent(settings: dict[str, Any]) -> Accent:
    raw = settings.get("accent", _DEFAULTS["accent"])
    try:
        return Accent(raw)
    except ValueError:
        return Accent.BLUE
