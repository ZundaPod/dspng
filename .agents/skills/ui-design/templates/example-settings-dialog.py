"""
Complete example: Material 3 Settings Dialog.

Demonstrates the canonical patterns for every component of the ui-design skill:
- ThemeManager subclass with token wiring
- Layout-based widget hierarchy (no absolute positioning)
- QScrollArea wrapping for overflow content
- Token-driven spacing and styling
- Size policies per Rule 4
- Dynamic property styling for active state
- QFormLayout for label–widget pairs

Run with: python example-settings-dialog.py
"""

import sys
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QGroupBox,
    QScrollArea,
    QFrame,
    QPushButton,
    QComboBox,
    QCheckBox,
    QSizePolicy,
)

# ---------------------------------------------------------------------------
# In a real project these imports come from theme_tokens.py / theme_manager.py
# ---------------------------------------------------------------------------
from theme_tokens import (
    SPACING_XS,
    SPACING_SM,
    SPACING_MD,
    SPACING_LG,
    SPACING_XL,
    LIGHT,
    DARK,
)
from theme_manager import ThemeManager


# ==============================================================================
# Theme
# ==============================================================================


class SettingsTheme(ThemeManager):
    """Project-specific theme — wires tokens and defines widget selectors."""

    def __init__(self):
        super().__init__()
        self.load_tokens(LIGHT, DARK)

    def build_stylesheet(self) -> str:
        return f"""
            /* --- Global defaults --- */
            QWidget {{
                background-color: {self.get("background")};
                color: {self.get("text_primary")};
                font-family: "{self.font_family()}";
                font-size: 13px;
            }}

            /* --- Sidebar --- */
            QFrame#sidebar {{
                background-color: {self.get("surface")};
                border-right: 1px solid {self.get("border")};
            }}
            QPushButton#navBtn {{
                background-color: transparent;
                color: {self.get("text_secondary")};
                border: none;
                border-radius: 8px;
                padding: 10px 16px;
                text-align: left;
                font-weight: 500;
            }}
            QPushButton#navBtn:hover {{
                background-color: {self.get("surface_variant")};
            }}
            QPushButton#navBtn[active="true"] {{
                background-color: {self.get("primary_container")};
                color: {self.get("primary")};
            }}

            /* --- Content area --- */
            QGroupBox {{
                font-weight: 600;
                border: none;
                margin-top: {SPACING_LG}px;
                padding-top: {SPACING_LG}px;
            }}
            QGroupBox::title {{
                color: {self.get("primary")};
            }}
            QLineEdit {{
                border: 1px solid {self.get("outline")};
                border-radius: 6px;
                padding: 6px 10px;
                background-color: {self.get("surface")};
            }}
            QLineEdit:focus {{
                border-color: {self.get("primary")};
            }}
            QPushButton#primaryBtn {{
                background-color: {self.get("primary")};
                color: {self.get("on_primary")};
                border: none;
                border-radius: 8px;
                padding: 8px 20px;
                font-weight: 600;
            }}
            QPushButton#primaryBtn:hover {{
                opacity: 0.9;
            }}
        """


# ==============================================================================
# Main Window
# ==============================================================================


class SettingsWindow(QMainWindow):
    """Settings dialog with sidebar navigation and scrollable content."""

    def __init__(self, theme: SettingsTheme):
        super().__init__()
        self._theme = theme
        self.setWindowTitle("Settings")
        self.resize(720, 480)

        # Central widget with horizontal layout (sidebar | content)
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Sidebar — fixed width, vertical nav buttons
        root.addWidget(self._build_sidebar(), stretch=0)

        # Scrollable content area — takes remaining space
        root.addWidget(self._build_content(), stretch=1)

    # ------------------------------------------------------------------
    # Sidebar
    # ------------------------------------------------------------------

    def _build_sidebar(self) -> QFrame:
        sidebar = QFrame(objectName="sidebar")
        sidebar.setFixedWidth(200)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(SPACING_SM, SPACING_LG, SPACING_SM, SPACING_LG)
        layout.setSpacing(SPACING_XS)

        # Navigation buttons — use dynamic property for active state
        self._nav_general = QPushButton("General", objectName="navBtn")
        self._nav_general.setProperty("active", True)  # default active
        self._nav_advanced = QPushButton("Advanced", objectName="navBtn")

        # Wire click handlers
        self._nav_general.clicked.connect(lambda: self._switch_nav("general"))
        self._nav_advanced.clicked.connect(lambda: self._switch_nav("advanced"))

        layout.addWidget(self._nav_general)
        layout.addWidget(self._nav_advanced)
        layout.addStretch()  # pushes buttons to top
        return sidebar

    def _switch_nav(self, page: str):
        """Toggle active state on nav buttons via dynamic properties."""
        for btn in (self._nav_general, self._nav_advanced):
            btn.setProperty("active", False)
            btn.style().unpolish(btn)
            btn.style().polish(btn)

        active = self._nav_general if page == "general" else self._nav_advanced
        active.setProperty("active", True)
        active.style().unpolish(active)
        active.style().polish(active)

        # In a real app you'd swap the content page here.

    # ------------------------------------------------------------------
    # Scrollable content
    # ------------------------------------------------------------------

    def _build_content(self) -> QScrollArea:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)  # mandatory — Rule 3
        scroll.setFrameShape(QFrame.NoFrame)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(SPACING_XL, SPACING_LG, SPACING_XL, SPACING_LG)
        layout.setSpacing(SPACING_MD)

        # Appearance section
        layout.addWidget(self._build_appearance_section())
        # Behaviour section
        layout.addWidget(self._build_behaviour_section())
        # Push remaining sections to top
        layout.addStretch()

        scroll.setWidget(content)
        return scroll

    # ------------------------------------------------------------------
    # Section builders
    # ------------------------------------------------------------------

    def _build_appearance_section(self) -> QGroupBox:
        group = QGroupBox("Appearance")
        form = QFormLayout(group)
        form.setContentsMargins(0, SPACING_SM, 0, 0)
        form.setSpacing(SPACING_SM)

        # Theme combo
        theme_combo = QComboBox()
        theme_combo.addItems(["Light", "Dark"])
        theme_combo.setSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed
        )
        form.addRow("Theme:", theme_combo)

        # Font size combo
        font_combo = QComboBox()
        font_combo.addItems(["Small", "Medium", "Large"])
        font_combo.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        form.addRow("Font size:", font_combo)

        return group

    def _build_behaviour_section(self) -> QGroupBox:
        group = QGroupBox("Behaviour")
        layout = QVBoxLayout(group)
        layout.setContentsMargins(0, SPACING_SM, 0, 0)
        layout.setSpacing(SPACING_SM)

        auto_save = QCheckBox("Auto-save changes")
        auto_save.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout.addWidget(auto_save)

        check_updates = QCheckBox("Check for updates on startup")
        check_updates.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        layout.addWidget(check_updates)

        return group


# ==============================================================================
# Entry point
# ==============================================================================


def main():
    app = QApplication(sys.argv)

    theme = SettingsTheme()
    theme.set_theme("light")

    window = SettingsWindow(theme)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
