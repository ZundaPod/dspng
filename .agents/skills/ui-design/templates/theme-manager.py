"""
Material 3 ThemeManager for PySide6.

Centralised theme engine: maintains state, provides token access, and compiles
Qt stylesheets dynamically.  Widgets must never contain inline styling.

Usage — subclass and wire tokens::

    from theme_tokens import LIGHT, DARK
    from theme_manager import ThemeManager

    class MyTheme(ThemeManager):
        def __init__(self):
            super().__init__()
            self.load_tokens(LIGHT, DARK)

        def build_stylesheet(self) -> str:
            return f'''
                QWidget {{
                    background-color: {self.get("background")};
                    color: {self.get("text_primary")};
                    font-family: "{self.font_family()}";
                }}
                QPushButton {{
                    background-color: {self.get("primary")};
                    color: {self.get("on_primary")};
                    border-radius: 6px;
                    padding: 8px 16px;
                }}
            '''

    # In main():
    app = QApplication(sys.argv)
    theme = MyTheme()
    theme.set_theme("light")
"""

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QColor


class ThemeManager:
    """Singleton theme manager — one instance per QApplication.

    Subclass and override ``build_stylesheet()`` to define widget-class
    selectors for your project.  Call ``load_tokens(light, dark)`` in
    ``__init__`` to populate the token store.
    """

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
        self._tokens = {"light": {}, "dark": {}}
        self._font_family = "Noto Sans"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load_tokens(self, light: dict, dark: dict):
        """Populate token dictionaries for both theme modes.

        Call once in ``__init__``, typically with ``LIGHT`` and ``DARK``
        from the project's ``theme_tokens`` module.
        """
        self._tokens["light"] = light
        self._tokens["dark"] = dark
        # Respect any font-family override from token dicts.
        if "font_family" in light:
            self._font_family = light["font_family"]

    def set_theme(self, mode: str):
        """Switch between ``"light"`` and ``"dark"`` at runtime."""
        if mode not in ("light", "dark"):
            raise ValueError(f"Unknown theme mode: {mode}")
        self._mode = mode
        self._apply()

    def get(self, key: str) -> str:
        """Return the resolved colour / token value for the current mode."""
        return self._tokens.get(self._mode, {}).get(key, "")

    def mode(self) -> str:
        """Return the active theme mode (``"light"`` or ``"dark"``)."""
        return self._mode

    def font_family(self) -> str:
        """Return the platform-appropriate font family."""
        return self._font_family

    # ------------------------------------------------------------------
    # Stylesheet compilation — override per project
    # ------------------------------------------------------------------

    def build_stylesheet(self) -> str:
        """Compile the full Qt stylesheet from token values.

        Override this method per-project to define widget-class selectors.
        The default implementation produces an empty stylesheet — projects
        must customise to match their widget hierarchy.

        Use ``self.get("token_name")`` to reference colour tokens and
        ``self.font_family()`` for the font family name.
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
