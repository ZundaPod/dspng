"""
Material 3 ThemeManager for PySide6.

Centralised theme engine: maintains state, provides token access, and compiles
Qt stylesheets dynamically.  Widgets must never contain inline styling.
"""

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPalette, QColor


class ThemeManager:
    """Singleton theme manager — one instance per QApplication."""

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
        self._mode = "light"
        self._tokens = {}   # populated by load_tokens()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_theme(self, mode: str):
        """Switch between 'light' and 'dark' at runtime."""
        if mode not in ("light", "dark"):
            raise ValueError(f"Unknown theme mode: {mode}")
        self._mode = mode
        self._apply()

    def get(self, key: str) -> str:
        """Return the resolved colour / token value for the current mode."""
        palette = self._tokens.get(self._mode, {})
        return palette.get(key, "")

    def mode(self) -> str:
        return self._mode

    # ------------------------------------------------------------------
    # Stylesheet compilation
    # ------------------------------------------------------------------

    def build_stylesheet(self) -> str:
        """Compile the full Qt stylesheet from token values.

        Override this method per-project to define widget-class selectors.
        The default implementation produces an empty stylesheet — projects
        must customise to match their widget hierarchy.
        """
        return ""

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _apply(self):
        """Push the compiled stylesheet to the global QApplication."""
        app = QApplication.instance()
        if app is not None:
            app.setStyleSheet(self.build_stylesheet())

    @staticmethod
    def _colour(value: str) -> QColor:
        return QColor(value)
