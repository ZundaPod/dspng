"""
Locale manager for dspng i18n support.

Uses Python's built-in ``gettext`` with compiled ``.mo`` files.  All
user-visible strings should go through ``tr()`` so they are translated
at runtime.

Usage:
    from .locale_manager import tr

    label.setText(tr("Open File"))
"""

from __future__ import annotations

import gettext
import sys
from pathlib import Path

from PySide6.QtCore import QObject, Signal

# Locale directory (relative to this file's location in the package).
# When frozen by PyInstaller, locales are extracted to sys._MEIPASS.
if getattr(sys, "frozen", False):
    _LOCALE_DIR = Path(sys._MEIPASS) / "locales"
else:
    _LOCALE_DIR = Path(__file__).resolve().parent.parent.parent.parent / "locales"

# Available translations — code → display name
_AVAILABLE: dict[str, str] = {
    "en": "English",
    "zh_CN": "简体中文",
}

# Cache of compiled gettext translation objects
_translations: dict[str, gettext.NullTranslations] = {}


# ---------------------------------------------------------------------------
# LocaleManager (singleton)
# ---------------------------------------------------------------------------


class LocaleManager(QObject):
    """Singleton that manages the active translation and emits a signal
    when the language changes so widgets can re-translate themselves."""

    language_changed = Signal()

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialised = False
        return cls._instance

    def __init__(self):
        if self._initialised:
            return
        self._initialised = True
        super().__init__()
        self._lang = "en"
        self._load_translations()

    # ---- public API ----

    @property
    def language(self) -> str:
        return self._lang

    @property
    def available(self) -> dict[str, str]:
        return dict(_AVAILABLE)

    def set_language(self, lang: str):
        """Switch to *lang*.  Emits ``language_changed``."""
        if lang == self._lang or lang not in _AVAILABLE:
            return
        self._lang = lang
        self._install()
        self.language_changed.emit()

    # ---- internal ----

    def _load_translations(self):
        """Pre-load all available translations."""
        for code in _AVAILABLE:
            try:
                t = gettext.translation(
                    "messages",
                    localedir=str(_LOCALE_DIR),
                    languages=[code],
                    fallback=True,
                )
            except Exception:
                t = gettext.NullTranslations()
            _translations[code] = t
        # Ensure en is always available (NullTranslations = pass-through).
        _translations.setdefault("en", gettext.NullTranslations())

    def _install(self):
        """Install the active translation for the ``_()`` builtin."""
        _translations[self._lang].install()


# ---------------------------------------------------------------------------
# Shortcut
# ---------------------------------------------------------------------------


def locale_manager() -> LocaleManager:
    return LocaleManager()


def tr(message: str) -> str:
    """Translate *message* into the currently active language.

    Falls back to the original string if no translation exists.
    """
    t = _translations.get(LocaleManager().language)
    if t is None:
        return message
    return t.gettext(message)
