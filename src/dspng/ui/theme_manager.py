"""
Material 3 ThemeManager for PySide6.

Centralised theme engine: maintains light/dark mode state, provides token
access, and compiles Qt stylesheets dynamically.  Widgets must never contain
inline styling — all selectors live in `build_stylesheet()`.

Usage:
    theme = ThemeManager()
    theme.set_theme("dark")   # or "light"
    value = theme.get("primary")
"""

from __future__ import annotations

from enum import Enum

from PySide6.QtGui import QColor, QFont, QGuiApplication
from PySide6.QtWidgets import QApplication


class ThemeMode(Enum):
    LIGHT = "light"
    DARK = "dark"
    SYSTEM = "system"


MODE_LABELS: dict[ThemeMode, str] = {
    ThemeMode.LIGHT: "Light",
    ThemeMode.DARK: "Dark",
    ThemeMode.SYSTEM: "System",
}


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
        self._mode = "dark"
        self._custom_colors: dict[str, str] = {}
        self._custom_font_family: str | None = None
        self._custom_font_size: str | None = None
        self._custom_font_weight: str | None = None
        self._load_tokens()

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
        """Return the resolved colour / token value for the current mode.

        Checks custom overrides first, then falls back to M3 defaults.
        """
        if key in self._custom_colors:
            return self._custom_colors[key]
        palette = self._tokens.get(self._mode, {})
        return palette.get(key, "")

    def mode(self) -> str:
        return self._mode

    def set_custom_colors(self, colors: dict[str, str]):
        """Override M3 tokens with user-defined colours.

        Pass an empty dict to clear all overrides.  Re-applies the
        stylesheet so changes are visible immediately.
        """
        self._custom_colors = dict(colors)
        self._apply()

    def reset_customs(self):
        """Remove all custom colour overrides."""
        self._custom_colors.clear()
        self._apply()

    @property
    def custom_colors(self) -> dict[str, str]:
        return dict(self._custom_colors)

    def font_family(self) -> str:
        return self._custom_font_family or FONT_FAMILY

    def font_size(self) -> str:
        return self._custom_font_size or DEFAULT_FONT_SIZE

    def font_size_small(self) -> str:
        """Small variant (panel titles, headers) — 1pt less than body."""
        size = int(self.font_size().rstrip("pt"))
        return f"{max(size - 1, 6)}pt"

    def font_weight(self) -> str:
        return self._custom_font_weight or "400"

    def set_custom_fonts(
        self, family: str | None, size: str | None, weight: str | None = None
    ):
        """Override the default font family, size, and/or weight.

        Pass None for any argument to keep the M3 default.
        """
        self._custom_font_family = family if family else None
        self._custom_font_size = size if size else None
        self._custom_font_weight = weight if weight else None
        self._apply()

    @property
    def custom_fonts(self) -> dict[str, str]:
        result: dict[str, str] = {}
        if self._custom_font_family:
            result["family"] = self._custom_font_family
        if self._custom_font_size:
            result["size"] = self._custom_font_size
        if self._custom_font_weight:
            result["weight"] = self._custom_font_weight
        return result

    # ------------------------------------------------------------------
    # System-mode detection
    # ------------------------------------------------------------------

    @staticmethod
    def detect_system_mode() -> str:
        """Heuristic: check if the system palette background is dark."""
        palette = QGuiApplication.palette()
        bg = palette.window().color()
        return "dark" if bg.lightnessF() < 0.5 else "light"

    # ------------------------------------------------------------------
    # Stylesheet compilation
    # ------------------------------------------------------------------

    def build_stylesheet(self) -> str:
        """Compile the full Qt stylesheet from token values.

        Every selector references tokens via ``self.get("key")`` so the
        stylesheet reflects the current mode automatically.
        """
        t = self.get  # shorthand for readability

        return f"""
/* ---- Global ---- */
* {{
    font-weight: {self.font_weight()};
}}
QMainWindow, QWidget {{
    background-color: {t("background")};
    color: {t("text_primary")};
    font-family: "{self.font_family()}", "Helvetica Neue", Arial, sans-serif;
    font-size: {self.font_size()};
}}

/* ---- Panel containers ---- */
QFrame[frameShape="6"] {{
    background-color: {t("background")};
    border: 1px solid {t("border")};
    border-radius: {RADIUS_SM}px;
}}

/* ---- Panel title labels ---- */
QLabel#panelTitle {{
    background-color: {t("background")};
    color: {t("text_secondary")};
    font-size: {self.font_size_small()};
    font-weight: bold;
    letter-spacing: 1px;
    padding: 3px 6px;
    border-bottom: 1px solid {t("border")};
}}

/* ---- Push buttons ---- */
QPushButton {{
    background-color: transparent;
    color: {t("text_primary")};
    border: 1px solid transparent;
    border-radius: {RADIUS_SM}px;
    padding: 4px 10px;
    min-height: 22px;
}}
QPushButton:hover {{
    background-color: {t("surface_variant")};
    border-color: {t("border")};
}}
QPushButton:pressed {{
    background-color: {t("border")};
}}
QPushButton:checked {{
    background-color: {t("primary")};
    color: {t("on_primary")};
    border-color: {t("primary")};
}}

/* ---- Colour swatch buttons ---- */
QPushButton#colorSwatch {{
    border: 1px solid {t("outline")};
    border-radius: {RADIUS_SM}px;
}}

/* ---- Tree / List views ---- */
QTreeView, QListView {{
    background-color: {t("background")};
    alternate-background-color: {t("background")};
    border: 1px solid {t("border")};
    outline: none;
    font-size: {self.font_size()};
}}
QTreeView::item, QListView::item {{
    padding: 2px 4px;
    border: none;
}}
QTreeView::item:selected, QListView::item:selected {{
    background-color: {t("primary")};
    color: {t("on_primary")};
}}
QTreeView::item:hover, QListView::item:hover {{
    background-color: {t("surface_variant")};
}}

/* ---- Tree-view row height presets (dynamic property) ---- */
QTreeView[thumbSize="s"]::item {{
    height: 36px;
    min-height: 36px;
}}
QTreeView[thumbSize="m"]::item {{
    height: 68px;
    min-height: 68px;
}}
QTreeView[thumbSize="l"]::item {{
    height: 132px;
    min-height: 132px;
}}

/* ---- Checkbox inside tree-view delegate ---- */
QTreeView QCheckBox {{
    margin: 0px;
    padding: 0px;
}}

/* ---- Header ---- */
QHeaderView::section {{
    background-color: {t("background")};
    color: {t("text_secondary")};
    border: none;
    border-right: 1px solid {t("border")};
    padding: 2px 4px;
    font-size: {self.font_size_small()};
}}

/* ---- Scroll bars ---- */
QScrollBar:vertical {{
    background: transparent;
    width: 8px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: {t("primary")};
    border-radius: 4px;
    min-height: 20px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
QScrollBar:horizontal {{
    background: transparent;
    height: 8px;
    margin: 0;
}}
QScrollBar::handle:horizontal {{
    background: {t("primary")};
    border-radius: 4px;
    min-width: 20px;
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0;
}}

/* ---- Checkboxes ---- */
QCheckBox {{
    spacing: {SPACING_XS}px;
}}
QCheckBox::indicator {{
    width: 14px;
    height: 14px;
    border: 1px solid {t("border")};
    border-radius: 2px;
    background-color: {t("background")};
}}
QCheckBox::indicator:checked {{
    background-color: {t("primary")};
    border-color: {t("primary")};
}}
QCheckBox::indicator:hover {{
    border-color: {t("primary")};
}}

/* ---- Splitter ---- */
QSplitter::handle {{
    background-color: {t("border")};
}}
QSplitter::handle:horizontal {{
    width: 2px;
}}
QSplitter::handle:vertical {{
    height: 2px;
}}

/* ---- Menu bar ---- */
QMenuBar {{
    background-color: {t("background")};
    color: {t("text_primary")};
    border-bottom: 1px solid {t("border")};
    padding: 2px;
}}
QMenuBar::item:selected {{
    background-color: {t("surface_variant")};
}}
QMenu {{
    background-color: {t("background")};
    color: {t("text_primary")};
    border: 1px solid {t("border")};
}}
QMenu::item:selected {{
    background-color: {t("primary")};
    color: {t("on_primary")};
}}
QMenu::separator {{
    height: 1px;
    background: {t("border")};
    margin: 4px 8px;
}}

/* ---- Slider ---- */
QSlider::groove:horizontal {{
    height: 4px;
    background: {t("surface_variant")};
    border-radius: 2px;
}}
QSlider::handle:horizontal {{
    background: {t("text_primary")};
    width: 12px;
    height: 12px;
    margin: -4px 0;
    border-radius: 6px;
}}
QSlider::handle:horizontal:hover {{
    background: {t("primary")};
}}

/* ---- Tooltip ---- */
QToolTip {{
    background-color: {t("background")};
    color: {t("text_primary")};
    border: 1px solid {t("border")};
    padding: 4px;
    font-size: {self.font_size()};
}}

/* ---- Message box ---- */
QMessageBox {{
    background-color: {t("background")};
}}
QMessageBox QLabel {{
    color: {t("text_primary")};
}}
"""

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load_tokens(self):
        """Populate the token dictionary from theme_tokens."""
        from .theme_tokens import DARK, LIGHT

        self._tokens = {"light": LIGHT, "dark": DARK}

    def _apply(self):
        """Push the compiled stylesheet, font, and icon colour to the app."""
        app = QApplication.instance()
        if app is not None:
            app.setStyleSheet(self.build_stylesheet())
            font = app.font()
            font.setWeight(QFont.Weight(int(self.font_weight())))
            app.setFont(font)
            from .icon_manager import IconManager

            IconManager().set_color(self.get("text_primary"))

    @staticmethod
    def _colour(value: str) -> QColor:
        return QColor(value)


# Import at module level for use in stylesheet f-strings.
from .theme_tokens import (  # noqa: E402
    DEFAULT_FONT_SIZE,
    FONT_FAMILY,
    RADIUS_SM,
    SPACING_XS,
)
