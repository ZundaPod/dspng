"""
Persistent user settings stored at ~/.dspng/settings.json.

Structure::

    {
      "app":    { "language": "en" },
      "theme":  { "mode": "dark", "custom_colors": {} }
    }

Old flat-format files (``{"theme_mode": "dark"}``) are auto-migrated
on first load.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any

from .theme_manager import ThemeMode

# ---------------------------------------------------------------------------
# Defaults — used as template when merging with on-disk data
# ---------------------------------------------------------------------------
_TEMPLATE: dict[str, Any] = {
    "app": {
        "language": "en",
        "temp_dir": str(Path(tempfile.gettempdir()) / "dspng"),
    },
    "theme": {
        "mode": ThemeMode.DARK.value,
        "custom_colors": {},
    },
}

SETTINGS_DIR = Path.home() / ".dspng"
SETTINGS_FILE = SETTINGS_DIR / "settings.json"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def load() -> dict[str, Any]:
    """Load settings from disk, falling back to defaults.

    Automatically migrates the old flat format to the new nested layout.
    """
    try:
        data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
    except FileNotFoundError, json.JSONDecodeError:
        return _deep_copy_template()

    # Detect old flat format and migrate.
    if "theme_mode" in data and "theme" not in data:
        data = _migrate_flat(data)

    return _deep_merge(_deep_copy_template(), data)


def save(settings: dict[str, Any]) -> None:
    """Persist settings to disk."""
    SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
    SETTINGS_FILE.write_text(
        json.dumps(settings, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def get_language(settings: dict[str, Any]) -> str:
    return settings.get("app", {}).get("language", "en")


def set_language(settings: dict[str, Any], lang: str) -> None:
    settings.setdefault("app", {})["language"] = lang


def get_temp_dir(settings: dict[str, Any]) -> str:
    return settings.get("app", {}).get(
        "temp_dir", str(Path(tempfile.gettempdir()) / "dspng")
    )


def set_temp_dir(settings: dict[str, Any], path: str) -> None:
    settings.setdefault("app", {})["temp_dir"] = path


def get_mode(settings: dict[str, Any]) -> ThemeMode:
    raw = settings.get("theme", {}).get("mode", ThemeMode.DARK.value)
    try:
        return ThemeMode(raw)
    except ValueError:
        return ThemeMode.DARK


def set_mode(settings: dict[str, Any], mode: ThemeMode) -> None:
    settings.setdefault("theme", {})["mode"] = mode.value


def get_custom_colors(settings: dict[str, Any]) -> dict[str, str]:
    return dict(settings.get("theme", {}).get("custom_colors", {}))


def set_custom_colors(settings: dict[str, Any], colors: dict[str, str]) -> None:
    settings.setdefault("theme", {})["custom_colors"] = dict(colors)


def get_custom_fonts(settings: dict[str, Any]) -> dict[str, str]:
    return dict(settings.get("theme", {}).get("custom_fonts", {}))


def set_custom_fonts(settings: dict[str, Any], fonts: dict[str, str]) -> None:
    settings.setdefault("theme", {})["custom_fonts"] = dict(fonts)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _deep_copy_template() -> dict[str, Any]:
    """Deep-copy the template so mutations don't leak."""
    import copy

    return copy.deepcopy(_TEMPLATE)


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Recursively merge *override* into *base*, mutating *base*."""
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value
    return base


def _migrate_flat(old: dict[str, Any]) -> dict[str, Any]:
    """Convert old flat-format settings to the nested structure."""
    result: dict[str, Any] = {}

    # app section
    result["app"] = {}
    if "language" in old:
        result["app"]["language"] = old["language"]

    # theme section
    result["theme"] = {}
    if "theme_mode" in old:
        result["theme"]["mode"] = old["theme_mode"]
    if "accent" in old:
        # Accent was removed — discard silently.
        pass

    return _deep_merge(_deep_copy_template(), result)
