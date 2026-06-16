"""
Settings dialog with sidebar navigation — OBS Studio layout conventions.

Sidebar (QListWidget, max 180 px, Minimum×Expanding) + QStackedWidget.
Appearance tab: language, font (family/slider+readout/weight), theme,
colour customisation (14 tokens, grid-aligned, per-token reset).
"""

from __future__ import annotations

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QColorDialog,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFontComboBox,
    QFormLayout,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSlider,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from .icon_manager import icon
from .locale_manager import LocaleManager, tr
from .theme_manager import ThemeManager, ThemeMode
from .theme_tokens import (
    SPACING_LG,
    SPACING_NONE,
    SPACING_SM,
    SPACING_XS,
)

# ---------------------------------------------------------------------------
# All colour tokens exposed in the Appearance tab, grouped for display.
# ---------------------------------------------------------------------------
_COLOR_GROUPS: list[tuple[str, list[str]]] = [
    ("Surface", ["background", "surface", "surface_variant"]),
    ("Primary", ["primary", "primary_container", "on_primary", "secondary"]),
    ("Text", ["text_primary", "text_secondary", "text_on_primary"]),
    ("Borders", ["border", "outline"]),
    ("Status", ["error"]),
]

_TOKEN_LABELS: dict[str, str] = {
    "background": "Background",
    "surface": "Surface",
    "surface_variant": "Surface Variant",
    "primary": "Primary",
    "primary_container": "Primary Container",
    "on_primary": "On Primary",
    "secondary": "Secondary",
    "text_primary": "Text Primary",
    "text_secondary": "Text Secondary",
    "text_on_primary": "Text On Primary",
    "border": "Border",
    "outline": "Outline",
    "error": "Error",
}

_MODE_LABELS: dict[ThemeMode, str] = {
    ThemeMode.LIGHT: "Light",
    ThemeMode.DARK: "Dark",
    ThemeMode.SYSTEM: "System",
}


# ======================================================================
# Settings Dialog
# ======================================================================


class SettingsDialog(QDialog):
    """Modal settings dialog — OBS-style sidebar + stacked pages."""

    settings_changed = Signal()

    def __init__(self, settings: dict, parent=None):
        super().__init__(parent)
        self._settings = settings
        self._sidebar_items: list[QListWidgetItem] = []
        self.setWindowTitle(tr("Settings"))
        self.setMinimumWidth(560)
        self.setMinimumHeight(400)
        self.setSizeGripEnabled(True)

        self._setup_ui()

        LocaleManager().language_changed.connect(self._retranslate_ui)

    def _setup_ui(self):
        # --- Sidebar (OBS: Minimum×Expanding, max 180 px) ---
        self._sidebar = QListWidget()
        self._sidebar.setMaximumWidth(180)
        self._sidebar.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding)
        self._sidebar.currentRowChanged.connect(self._on_sidebar_changed)

        # --- Stacked pages ---
        self._stack = QStackedWidget()
        self._stack.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self._appearance = AppearancePage(self._settings)
        self._add_page(tr("Appearance"), self._appearance, "palette")
        self._files_page = FilesPage(self._settings)
        self._add_page(tr("Files"), self._files_page, "folder")
        self._keymaps = KeymapsPage()
        self._add_page(tr("Keymaps"), self._keymaps, "keyboard")
        self._sidebar.setCurrentRow(0)

        # --- Final layout (OBS: spacing=0 between sidebar and stack) ---
        content_row = QHBoxLayout()
        content_row.setContentsMargins(
            SPACING_NONE, SPACING_NONE, SPACING_NONE, SPACING_NONE
        )
        content_row.setSpacing(SPACING_NONE)
        content_row.addWidget(self._sidebar)
        content_row.addWidget(self._stack, stretch=1)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(
            SPACING_NONE, SPACING_NONE, SPACING_NONE, SPACING_NONE
        )
        main_layout.setSpacing(SPACING_SM)
        main_layout.addLayout(content_row, stretch=1)
        main_layout.addWidget(buttons)

    def _add_page(self, name: str, widget: QWidget, icon_name: str = ""):
        item = QListWidgetItem(name)
        item.setSizeHint(QSize(0, 36))
        if icon_name:
            item.setIcon(icon("actions", icon_name))
        self._sidebar.addItem(item)
        self._stack.addWidget(widget)
        self._sidebar_items.append(item)

    def _retranslate_ui(self):
        self.setWindowTitle(tr("Settings"))
        for i, item in enumerate(self._sidebar_items):
            if i == 0:
                item.setText(tr("Appearance"))
            elif i == 1:
                item.setText(tr("Keymaps"))
        self._appearance._retranslate_ui()
        self._keymaps._retranslate_ui()

    def _on_sidebar_changed(self, index: int):
        self._stack.setCurrentIndex(index)

    def _on_accept(self):
        self._appearance.commit()
        self._files_page.commit()
        self.settings_changed.emit()
        self.accept()

    def reject(self):
        self._appearance.cancel()
        super().reject()


# ======================================================================
# Appearance Page — OBS layout conventions
# ======================================================================


class AppearancePage(QWidget):
    """Appearance tab: Language, Font, Theme, Colours."""

    def __init__(self, settings: dict, parent=None):
        super().__init__(parent)
        self._settings = settings
        self._theme = ThemeManager()

        from .settings import get_custom_colors, get_custom_fonts, get_mode

        self._custom_colors = get_custom_colors(settings)
        self._saved_colors = dict(self._custom_colors)
        self._saved_mode = get_mode(settings)
        self._saved_language = settings.get("app", {}).get("language", "en")

        saved_fonts = get_custom_fonts(settings)
        self._saved_font_family = saved_fonts.get("family", "")
        self._saved_font_size = saved_fonts.get("size", "")
        self._saved_font_weight = saved_fonts.get("weight", "")

        self._color_swatches: dict[str, QPushButton] = {}
        self._translatable_labels: list[QLabel] = []
        self._translatable_groups: list[QGroupBox] = []
        self._translatable_buttons: list[QPushButton] = []

        self._setup_ui()

    # ------------------------------------------------------------------
    # UI construction — OBS page structure
    # ------------------------------------------------------------------

    def _setup_ui(self):
        # OBS: page margin left=9, others=0
        page_layout = QVBoxLayout(self)
        page_layout.setContentsMargins(9, 0, 0, 0)
        page_layout.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(
            SPACING_NONE, SPACING_NONE, SPACING_NONE, SPACING_NONE
        )
        scroll_layout.setSpacing(0)

        # OBS: QFrame as styling surface inside scroll content
        frame = QFrame()
        frame_layout = QVBoxLayout(frame)
        frame_layout.setContentsMargins(
            SPACING_NONE, SPACING_NONE, SPACING_NONE, SPACING_NONE
        )
        frame_layout.setSpacing(0)

        # -- General group (Language + Theme via QFormLayout) --
        general_group = QGroupBox(tr("General"))
        self._translatable_groups.append(general_group)
        general_form = QFormLayout(general_group)
        general_form.setFieldGrowthPolicy(
            QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow
        )
        general_form.setLabelAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        general_form.setContentsMargins(
            SPACING_NONE, SPACING_SM, SPACING_NONE, SPACING_NONE
        )
        general_form.setSpacing(SPACING_SM)

        # Language
        lang_label = QLabel(tr("Language"))
        self._lang_combo = QComboBox()
        self._lang_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        lm = LocaleManager()
        for code, name in lm.available.items():
            self._lang_combo.addItem(name, code)
        current_lang = self._settings.get("app", {}).get("language", "en")
        idx = self._lang_combo.findData(current_lang)
        if idx >= 0:
            self._lang_combo.setCurrentIndex(idx)
        self._lang_combo.currentIndexChanged.connect(self._on_lang_changed)
        lang_label.setBuddy(self._lang_combo)
        general_form.addRow(lang_label, self._lang_combo)

        # Theme (OBS: QComboBox, not stacked buttons)
        theme_label = QLabel(tr("Theme"))
        self._theme_combo = QComboBox()
        self._theme_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        from .settings import get_mode

        current_mode = get_mode(self._settings)
        for mode in ThemeMode:
            self._theme_combo.addItem(tr(_MODE_LABELS[mode]), mode.value)
        idx = self._theme_combo.findData(current_mode.value)
        if idx >= 0:
            self._theme_combo.setCurrentIndex(idx)
        self._theme_combo.currentIndexChanged.connect(self._on_theme_changed)
        theme_label.setBuddy(self._theme_combo)
        general_form.addRow(theme_label, self._theme_combo)

        frame_layout.addWidget(general_group)
        frame_layout.addSpacing(SPACING_LG)

        # -- Font group (QFormLayout, slider+readout for size) --
        font_group = QGroupBox(tr("Font"))
        self._translatable_groups.append(font_group)
        font_form = QFormLayout(font_group)
        font_form.setFieldGrowthPolicy(
            QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow
        )
        font_form.setLabelAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        font_form.setContentsMargins(
            SPACING_NONE, SPACING_SM, SPACING_NONE, SPACING_NONE
        )
        font_form.setSpacing(SPACING_SM)

        # Family
        family_label = QLabel(tr("Family"))
        self._font_family_combo = QFontComboBox()
        self._font_family_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        family_label.setBuddy(self._font_family_combo)
        font_form.addRow(family_label, self._font_family_combo)

        # Size — QSlider + QLineEdit readout (OBS pattern)
        size_label = QLabel(tr("Size"))
        size_row = QHBoxLayout()
        size_row.setContentsMargins(
            SPACING_NONE, SPACING_NONE, SPACING_NONE, SPACING_NONE
        )
        size_row.setSpacing(SPACING_SM)

        self._font_size_readout = QLineEdit("9")
        self._font_size_readout.setReadOnly(True)
        self._font_size_readout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._font_size_readout.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self._font_size_readout.setMaximumWidth(40)
        size_row.addWidget(self._font_size_readout)

        self._font_size_slider = QSlider(Qt.Orientation.Horizontal)
        self._font_size_slider.setMinimum(7)
        self._font_size_slider.setMaximum(12)
        self._font_size_slider.setValue(9)
        self._font_size_slider.setTickPosition(QSlider.TickPosition.TicksBothSides)
        self._font_size_slider.setTickInterval(1)
        self._font_size_slider.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._font_size_slider.valueChanged.connect(
            lambda v: self._font_size_readout.setText(str(v))
        )
        size_row.addWidget(self._font_size_slider, stretch=1)

        font_form.addRow(size_label, size_row)

        # Weight
        weight_label = QLabel(tr("Weight"))
        self._font_weight_combo = QComboBox()
        self._font_weight_combo.addItems(
            ["100", "200", "300", "400", "500", "600", "700", "800", "900"]
        )
        self._font_weight_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        weight_label.setBuddy(self._font_weight_combo)
        font_form.addRow(weight_label, self._font_weight_combo)

        # Load saved font prefs BEFORE connecting change signals so the
        # initial values don't trigger a premature _on_font_changed call.
        from .settings import get_custom_fonts
        from .theme_tokens import DEFAULT_FONT_SIZE

        saved_fonts = get_custom_fonts(self._settings)
        saved_family = saved_fonts.get("family", "")
        if saved_family:
            idx = self._font_family_combo.findText(saved_family)
            if idx >= 0:
                self._font_family_combo.setCurrentIndex(idx)
        saved_size = saved_fonts.get("size", DEFAULT_FONT_SIZE)
        self._font_size_slider.setValue(int(saved_size.rstrip("pt")))
        saved_weight = saved_fonts.get("weight", "400")
        idx = self._font_weight_combo.findText(saved_weight)
        if idx >= 0:
            self._font_weight_combo.setCurrentIndex(idx)

        # Connect change signals AFTER all initial values are loaded.
        self._font_size_slider.valueChanged.connect(self._on_font_changed)
        self._font_family_combo.currentTextChanged.connect(self._on_font_changed)
        self._font_weight_combo.currentTextChanged.connect(self._on_font_changed)

        frame_layout.addWidget(font_group)
        frame_layout.addSpacing(SPACING_LG)

        # -- Colour groups (QGridLayout per group, aligned columns) --
        self._color_group_boxes: list[QGroupBox] = []
        for group_name, token_keys in _COLOR_GROUPS:
            group_box = QGroupBox(tr(group_name))
            self._translatable_groups.append(group_box)
            self._color_group_boxes.append(group_box)
            grid = QGridLayout(group_box)
            grid.setSpacing(SPACING_XS)
            grid.setColumnStretch(0, 0)
            grid.setColumnStretch(1, 0)
            grid.setColumnStretch(2, 0)
            grid.setColumnStretch(3, 0)
            for i, key in enumerate(token_keys):
                label = QLabel(tr(_TOKEN_LABELS.get(key, key)))
                label.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
                self._translatable_labels.append(label)
                grid.addWidget(label, i, 0, Qt.AlignmentFlag.AlignLeft)

                swatch = QPushButton()
                swatch.setObjectName("colorSwatch")
                swatch.setFixedSize(28, 28)
                color = QColor(self._resolve_color(key))
                self._set_swatch_color(swatch, color)
                swatch.setToolTip(f"{key} — {color.name()}")
                swatch.clicked.connect(
                    lambda checked, k=key, s=swatch: self._pick_color(k, s)
                )
                grid.addWidget(swatch, i, 1)

                hex_label = QLabel(color.name())
                grid.addWidget(hex_label, i, 2)

                reset_btn = QPushButton()
                reset_btn.setIcon(icon("arrows", "arrow-back-up"))
                reset_btn.setIconSize(QSize(16, 16))
                reset_btn.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
                reset_btn.setToolTip(tr("Reset to default"))
                reset_btn.clicked.connect(lambda checked, k=key: self._reset_token(k))
                grid.addWidget(reset_btn, i, 3)

                self._color_swatches[key] = swatch
            frame_layout.addWidget(group_box)
            frame_layout.addSpacing(SPACING_LG)

        # -- Reset --
        self._reset_btn = QPushButton(tr("Reset to defaults"))
        self._translatable_buttons.append(self._reset_btn)
        self._reset_btn.clicked.connect(self._reset)
        self._reset_btn.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        frame_layout.addWidget(self._reset_btn)

        # OBS: vertical stretch pushes content to top
        frame_layout.addStretch()

        scroll_layout.addWidget(frame)
        scroll.setWidget(scroll_content)
        page_layout.addWidget(scroll)

    # ------------------------------------------------------------------
    # Colour picker helpers
    # ------------------------------------------------------------------

    def _set_swatch_color(self, btn: QPushButton, color: QColor):
        btn.setStyleSheet(
            f"QPushButton#colorSwatch {{ background-color: {color.name()}; }}"
        )

    def _pick_color(self, token_key: str, swatch: QPushButton):
        current = QColor(self._resolve_color(token_key))
        color = QColorDialog.getColor(current, self, tr("Choose colour"))
        if color.isValid():
            self._custom_colors[token_key] = color.name()
            self._set_swatch_color(swatch, color)
            self._update_hex_label(token_key, color.name())
            self._apply_live()

    def _update_hex_label(self, token_key: str, hex_str: str):
        for group in self._color_group_boxes:
            grid = group.layout()
            if not isinstance(grid, QGridLayout):
                continue
            for i in range(grid.rowCount()):
                swatch_item = grid.itemAtPosition(i, 1)
                if swatch_item and swatch_item.widget() is self._color_swatches.get(
                    token_key
                ):
                    hex_item = grid.itemAtPosition(i, 2)
                    if hex_item and isinstance(hex_item.widget(), QLabel):
                        hex_item.widget().setText(hex_str)
                    return

    # ------------------------------------------------------------------
    # Handlers
    # ------------------------------------------------------------------

    def _on_lang_changed(self, _index: int):
        LocaleManager().set_language(self._lang_combo.currentData())

    def _on_theme_changed(self, _index: int):
        from .settings import set_mode

        mode = ThemeMode(self._theme_combo.currentData())
        set_mode(self._settings, mode)
        self._apply_live()

    def _on_font_changed(self):
        family = self._font_family_combo.currentText()
        size = f"{self._font_size_slider.value()}pt"
        weight = self._font_weight_combo.currentText()
        self._theme.set_custom_fonts(family or None, size or None, weight or None)

    def _apply_live(self):
        self._theme.set_custom_colors(self._custom_colors)
        family = self._font_family_combo.currentText()
        size = f"{self._font_size_slider.value()}pt"
        weight = self._font_weight_combo.currentText()
        self._theme.set_custom_fonts(family or None, size or None, weight or None)
        from .settings import get_mode

        mode = get_mode(self._settings)
        if mode == ThemeMode.SYSTEM:
            self._theme.set_theme(ThemeManager.detect_system_mode())
        else:
            self._theme.set_theme(mode.value)

    # ------------------------------------------------------------------
    # Colour resolution / reset
    # ------------------------------------------------------------------

    def _resolve_color(self, token_key: str) -> str:
        if token_key in self._custom_colors:
            return self._custom_colors[token_key]
        return self._theme.get(token_key)

    def _reset_token(self, token_key: str):
        self._custom_colors.pop(token_key, None)
        from .settings import get_mode
        from .theme_tokens import DARK, LIGHT

        mode = get_mode(self._settings)
        if mode == ThemeMode.SYSTEM:
            mode = (
                ThemeMode.DARK
                if ThemeManager.detect_system_mode() == "dark"
                else ThemeMode.LIGHT
            )
        palette = LIGHT if mode == ThemeMode.LIGHT else DARK
        color = QColor(palette.get(token_key, "#000000"))
        swatch = self._color_swatches.get(token_key)
        if swatch:
            self._set_swatch_color(swatch, color)
            self._update_hex_label(token_key, color.name())
        self._apply_live()

    def _reset(self):
        self._custom_colors.clear()
        for key, swatch in self._color_swatches.items():
            color = QColor(self._theme.get(key))
            self._set_swatch_color(swatch, color)
            self._update_hex_label(key, color.name())
        self._apply_live()

    # ------------------------------------------------------------------
    # Re-translation
    # ------------------------------------------------------------------

    def _retranslate_ui(self):
        lm = LocaleManager()
        for code in lm.available:
            idx = self._lang_combo.findData(code)
            if idx >= 0:
                self._lang_combo.setItemText(idx, tr(lm.available[code]))

        for group_box, (group_name, _token_keys) in zip(
            self._color_group_boxes, _COLOR_GROUPS
        ):
            group_box.setTitle(tr(group_name))

        idx = 0
        for _group_name, token_keys in _COLOR_GROUPS:
            for key in token_keys:
                if idx < len(self._translatable_labels):
                    self._translatable_labels[idx].setText(
                        tr(_TOKEN_LABELS.get(key, key))
                    )
                    idx += 1

        self._reset_btn.setText(tr("Reset to defaults"))

    # ------------------------------------------------------------------
    # Cancel / Commit
    # ------------------------------------------------------------------

    def cancel(self):
        from .settings import (
            set_custom_colors,
            set_custom_fonts,
            set_language,
            set_mode,
        )

        set_mode(self._settings, self._saved_mode)
        set_custom_colors(self._settings, self._saved_colors)
        set_language(self._settings, self._saved_language)
        set_custom_fonts(
            self._settings,
            {
                "family": self._saved_font_family,
                "size": self._saved_font_size,
                "weight": self._saved_font_weight,
            },
        )
        self._theme.set_custom_colors(self._saved_colors)
        self._theme.set_custom_fonts(
            self._saved_font_family or None,
            self._saved_font_size or None,
            self._saved_font_weight or None,
        )
        LocaleManager().set_language(self._saved_language)
        if self._saved_mode == ThemeMode.SYSTEM:
            self._theme.set_theme(ThemeManager.detect_system_mode())
        else:
            self._theme.set_theme(self._saved_mode.value)

    def commit(self):
        from .settings import set_custom_colors, set_custom_fonts, set_language, save

        lang_code = self._lang_combo.currentData()
        set_language(self._settings, lang_code)
        LocaleManager().set_language(lang_code)

        set_custom_colors(self._settings, self._custom_colors)

        family = self._font_family_combo.currentText()
        size = f"{self._font_size_slider.value()}pt"
        weight = self._font_weight_combo.currentText()
        fonts = {}
        if family:
            fonts["family"] = family
        if size:
            fonts["size"] = size
        if weight:
            fonts["weight"] = weight
        set_custom_fonts(self._settings, fonts)

        save(self._settings)

        self._theme.set_custom_colors(self._custom_colors)
        self._theme.set_custom_fonts(family or None, size or None, weight or None)
        from .settings import get_mode

        mode = get_mode(self._settings)
        if mode == ThemeMode.SYSTEM:
            self._theme.set_theme(ThemeManager.detect_system_mode())
        else:
            self._theme.set_theme(mode.value)


# ======================================================================
# Keymaps Page — read-only display of all shortcuts
# ======================================================================

_KEYMAPS: list[tuple[str, list[tuple[str, str]]]] = [
    (
        "File",
        [
            ("Open PSD", "Ctrl+O"),
            ("Export PNG", "Ctrl+E"),
            ("Settings", "Ctrl+,"),
            ("Quit", "Ctrl+Q"),
        ],
    ),
    (
        "Canvas",
        [
            ("Zoom in / out", "Scroll wheel"),
            ("Pan", "Middle-click / Right-click / Alt+Left-click drag"),
            ("Fit to view", "Double-click"),
            ("Export PNG (drag)", "Left-click drag"),
        ],
    ),
    (
        "Layer Panel",
        [
            ("Toggle visibility", "Click checkbox"),
            ("Move up / down", "↑ / ↓ buttons"),
            ("Reorder", "Drag and drop"),
        ],
    ),
    (
        "File List",
        [
            ("Add file", "+ button / Drag and drop .psd"),
            ("Remove file", "− button"),
            ("Reload file", "↻ button"),
        ],
    ),
]


class KeymapsPage(QWidget):
    """Read-only keymap reference — OBS-style page layout."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._translatable_groups: list[QGroupBox] = []
        self._translatable_labels: list[QLabel] = []
        self._setup_ui()

    def _setup_ui(self):
        page_layout = QVBoxLayout(self)
        page_layout.setContentsMargins(9, 0, 0, 0)
        page_layout.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(
            SPACING_NONE, SPACING_NONE, SPACING_NONE, SPACING_NONE
        )
        scroll_layout.setSpacing(0)

        frame = QFrame()
        frame_layout = QVBoxLayout(frame)
        frame_layout.setContentsMargins(
            SPACING_NONE, SPACING_NONE, SPACING_NONE, SPACING_NONE
        )
        frame_layout.setSpacing(0)

        for group_name, entries in _KEYMAPS:
            group = QGroupBox(tr(group_name))
            self._translatable_groups.append(group)
            form = QFormLayout(group)
            form.setFieldGrowthPolicy(
                QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow
            )
            form.setLabelAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            form.setContentsMargins(
                SPACING_NONE, SPACING_SM, SPACING_NONE, SPACING_NONE
            )
            form.setSpacing(SPACING_SM)

            for action, shortcut in entries:
                label = QLabel(tr(action))
                label.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
                self._translatable_labels.append(label)

                value = QLineEdit(tr(shortcut))
                value.setReadOnly(True)
                value.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
                form.addRow(label, value)

            frame_layout.addWidget(group)
            frame_layout.addSpacing(SPACING_LG)

        frame_layout.addStretch()
        scroll_layout.addWidget(frame)
        scroll.setWidget(scroll_content)
        page_layout.addWidget(scroll)

    def _retranslate_ui(self):
        for group, (group_name, _entries) in zip(self._translatable_groups, _KEYMAPS):
            group.setTitle(tr(group_name))

        idx = 0
        for _group_name, entries in _KEYMAPS:
            for action, _shortcut in entries:
                if idx < len(self._translatable_labels):
                    self._translatable_labels[idx].setText(tr(action))
                    idx += 1


# ======================================================================
# Files Page — temp directory configuration
# ======================================================================


class FilesPage(QWidget):
    """Configure file paths — currently only the temp directory for drag-export."""

    def __init__(self, settings: dict, parent=None):
        super().__init__(parent)
        self._settings = settings
        self._setup_ui()

    def _setup_ui(self):
        from .settings import get_temp_dir

        page_layout = QVBoxLayout(self)
        page_layout.setContentsMargins(9, 0, 0, 0)
        page_layout.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(
            SPACING_NONE, SPACING_NONE, SPACING_NONE, SPACING_NONE
        )
        scroll_layout.setSpacing(0)

        frame = QFrame()
        frame_layout = QVBoxLayout(frame)
        frame_layout.setContentsMargins(
            SPACING_NONE, SPACING_NONE, SPACING_NONE, SPACING_NONE
        )
        frame_layout.setSpacing(0)

        group = QGroupBox(tr("Temp files"))
        form = QFormLayout(group)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        form.setLabelAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        form.setContentsMargins(SPACING_NONE, SPACING_SM, SPACING_NONE, SPACING_NONE)
        form.setSpacing(SPACING_SM)

        label = QLabel(tr("Drag-export temp dir"))
        row = QHBoxLayout()
        row.setContentsMargins(SPACING_NONE, SPACING_NONE, SPACING_NONE, SPACING_NONE)
        row.setSpacing(SPACING_SM)

        self._temp_dir_edit = QLineEdit(get_temp_dir(self._settings))
        self._temp_dir_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        row.addWidget(self._temp_dir_edit, stretch=1)

        browse_btn = QPushButton(tr("Browse…"))
        browse_btn.clicked.connect(self._browse)
        browse_btn.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        row.addWidget(browse_btn)

        form.addRow(label, row)
        frame_layout.addWidget(group)
        frame_layout.addStretch()

        scroll_layout.addWidget(frame)
        scroll.setWidget(scroll_content)
        page_layout.addWidget(scroll)

    def _browse(self):

        path = QFileDialog.getExistingDirectory(self, tr("Choose temp directory"))
        if path:
            self._temp_dir_edit.setText(path)

    def commit(self):
        from .settings import save, set_temp_dir

        set_temp_dir(self._settings, self._temp_dir_edit.text())
        save(self._settings)
