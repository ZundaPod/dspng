"""
Main application window.

Layout (all panels resizable via splitters):

┌──────────────────────────┬───────────────┐
│                          │  File List    │
│                          ├───────────────┤
│   Render Canvas          │  Layer Panel  │
│                          │               │
└──────────────────────────┴───────────────┘
"""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from ..psd_manager import DocumentStore
from .locale_manager import tr
from .panels.file_list import FileListPanel
from .panels.layer_panel import LayerPanel
from .panels.render_canvas import RenderCanvas
from .settings import get_mode, load
from .settings_dialog import SettingsDialog
from .theme_manager import ThemeManager, ThemeMode
from .theme_tokens import SPACING_NONE, SPACING_XS


class MainWindow(QMainWindow):
    """Top-level window that hosts all three panels."""

    def __init__(self):
        super().__init__()

        # Load settings and restore language BEFORE any tr() call.
        self._settings = load()
        self._mode = get_mode(self._settings)

        from .locale_manager import LocaleManager
        from .settings import get_language

        LocaleManager().set_language(get_language(self._settings))

        self.setWindowTitle(tr("dspng — PSD → PNG"))
        self.resize(1200, 800)
        self._set_window_icon()

        self._apply_theme()

        # Central state
        self._store = DocumentStore()

        # Build panels
        self._file_list = FileListPanel(self._store)
        self._layer_panel = LayerPanel()
        self._canvas = RenderCanvas()

        # Layout
        self._setup_layout()

        # Wire up signals
        self._file_list.document_selected.connect(self._on_document_selected)
        self._layer_panel.layer_visibility_changed.connect(self._on_visibility_changed)
        self._layer_panel.thumbnail_changed.connect(self._on_thumbnail_changed)
        self._canvas.export_occurred.connect(self._on_export_occurred)
        LocaleManager().language_changed.connect(self._retranslate_ui)

        # Menu bar
        self._setup_file_menu()
        self._setup_help_menu()

    # ------------------------------------------------------------------
    # Icon
    # ------------------------------------------------------------------

    def _set_window_icon(self):
        """Set the window/taskbar icon."""
        if getattr(sys, "frozen", False):
            # PyInstaller extracts embedded data to sys._MEIPASS.
            base = Path(sys._MEIPASS)
        else:
            base = Path(__file__).resolve().parent.parent.parent.parent

        for name in ("icon.ico", "icon.png"):
            icon_path = base / name
            if icon_path.exists():
                icon = QIcon(str(icon_path))
                if not icon.isNull():
                    self.setWindowIcon(icon)
                    app = QApplication.instance()
                    if app is not None:
                        app.setWindowIcon(icon)
                    return

    # ------------------------------------------------------------------
    # Theme
    # ------------------------------------------------------------------

    def _apply_theme(self):
        """Resolve the current mode and push the compiled stylesheet."""
        self._mode = get_mode(self._settings)
        theme = ThemeManager()
        from .settings import get_custom_colors, get_custom_fonts

        theme.set_custom_colors(get_custom_colors(self._settings))
        fonts = get_custom_fonts(self._settings)
        theme.set_custom_fonts(
            fonts.get("family"), fonts.get("size"), fonts.get("weight")
        )
        if self._mode == ThemeMode.SYSTEM:
            theme.set_theme(ThemeManager.detect_system_mode())
        else:
            theme.set_theme(self._mode.value)

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------

    @staticmethod
    def _make_panel(title: str, widget: QWidget) -> tuple[QWidget, QLabel]:
        """Wrap *widget* in a container with a title label and border.

        Returns (container, title_label) so callers can re-translate the
        title at runtime.
        """
        container = QFrame()
        container.setFrameShape(QFrame.Shape.StyledPanel)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(
            SPACING_NONE, SPACING_NONE, SPACING_NONE, SPACING_NONE
        )
        layout.setSpacing(SPACING_NONE)

        label = QLabel(title)
        label.setObjectName("panelTitle")
        layout.addWidget(label)
        layout.addWidget(widget, stretch=1)
        return container, label

    def _setup_layout(self):
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QHBoxLayout(central)
        root_layout.setContentsMargins(SPACING_XS, SPACING_XS, SPACING_XS, SPACING_XS)

        h_splitter = QSplitter(Qt.Orientation.Horizontal)
        render_panel, self._title_render = self._make_panel(tr("Render"), self._canvas)
        h_splitter.addWidget(render_panel)
        h_splitter.setStretchFactor(0, 3)

        v_splitter = QSplitter(Qt.Orientation.Vertical)
        files_panel, self._title_files = self._make_panel(tr("Files"), self._file_list)
        layers_panel, self._title_layers = self._make_panel(
            tr("Layers"), self._layer_panel
        )
        v_splitter.addWidget(files_panel)
        v_splitter.addWidget(layers_panel)
        v_splitter.setStretchFactor(0, 1)
        v_splitter.setStretchFactor(1, 2)

        h_splitter.addWidget(v_splitter)
        h_splitter.setStretchFactor(1, 1)
        h_splitter.setSizes([840, 360])
        v_splitter.setSizes([250, 550])

        root_layout.addWidget(h_splitter)

    # ------------------------------------------------------------------
    # Menus
    # ------------------------------------------------------------------

    def _setup_file_menu(self):
        self._menu_file = self.menuBar().addMenu(tr("&File"))

        self._act_open = QAction(tr("&Open…"), self)
        self._act_open.setShortcut("Ctrl+O")
        self._act_open.triggered.connect(self._on_open)
        self._menu_file.addAction(self._act_open)

        self._act_export = QAction(tr("&Export PNG…"), self)
        self._act_export.setShortcut("Ctrl+E")
        self._act_export.triggered.connect(self._on_export)
        self._menu_file.addAction(self._act_export)

        self._menu_file.addSeparator()

        self._act_settings = QAction(tr("&Settings…"), self)
        self._act_settings.setShortcut("Ctrl+,")
        self._act_settings.triggered.connect(self._on_settings)
        self._menu_file.addAction(self._act_settings)

        self._menu_file.addSeparator()

        self._act_quit = QAction(tr("&Quit"), self)
        self._act_quit.setShortcut("Ctrl+Q")
        self._act_quit.triggered.connect(self.close)
        self._menu_file.addAction(self._act_quit)

    # ------------------------------------------------------------------
    # Runtime re-translation
    # ------------------------------------------------------------------

    def _retranslate_ui(self):
        """Re-translate all user-visible strings after a language change."""
        self.setWindowTitle(tr("dspng — PSD → PNG"))

        self._menu_file.setTitle(tr("&File"))
        self._menu_help.setTitle(tr("&Help"))

        self._act_open.setText(tr("&Open…"))
        self._act_export.setText(tr("&Export PNG…"))
        self._act_quit.setText(tr("&Quit"))
        self._act_settings.setText(tr("&Settings…"))

        self._act_about.setText(tr("&About"))

        self._title_render.setText(tr("Render"))
        self._title_files.setText(tr("Files"))
        self._title_layers.setText(tr("Layers"))

    # ------------------------------------------------------------------
    # Help menu
    # ------------------------------------------------------------------

    def _setup_help_menu(self):
        self._menu_help = self.menuBar().addMenu(tr("&Help"))

        self._act_about = QAction(tr("&About"), self)
        self._act_about.triggered.connect(self._on_about)
        self._menu_help.addAction(self._act_about)

    def _on_about(self):
        from PySide6.QtWidgets import QApplication

        version = QApplication.instance().applicationVersion()
        QMessageBox.about(
            self,
            tr("About dspng"),
            f"<h2>dspng v{version}</h2>"
            + tr(
                "<p>A standalone tool for rendering PSD files to PNG<br>"
                "without launching Photoshop.</p>"
                "<p><b>Author:</b> johanvx "
                "(<a href='https://github.com/johanvx'>github.com/johanvx</a>)</p>"
                "<p><b>Source:</b> "
                "<a href='https://github.com/ZundaPod/dspng'>github.com/ZundaPod/dspng</a></p>"
                "<p><b>License:</b> GPL-2.0 "
                "(<a href='https://spdx.org/licenses/GPL-2.0-only.html'>spdx.org</a>)</p>"
            ),
        )

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _on_document_selected(self, index: int):
        doc = self._store.selected_document
        self._canvas.set_document(doc)
        self._layer_panel.set_document(doc)

    def _on_visibility_changed(self):
        self._canvas.refresh_composite()

    def _on_thumbnail_changed(self):
        self._file_list.refresh_current_thumbnail()

    def _on_export_occurred(self):
        self._file_list.refresh_counter()

    def _on_settings(self):
        dlg = SettingsDialog(self._settings, self)
        dlg.settings_changed.connect(self._apply_theme)
        dlg.exec()

    def _on_open(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, tr("Open PSD Files"), "", tr("Photoshop Files (*.psd)")
        )
        for p in paths:
            self._store.add_document(Path(p))
        self._file_list.refresh_counter()
        doc = self._store.selected_document
        self._canvas.set_document(doc)
        self._layer_panel.set_document(doc)

    def _on_export(self):
        doc = self._store.selected_document
        if doc is None:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, tr("Export PNG"), f"{doc.name}.png", tr("PNG Image (*.png)")
        )
        if path:
            from ..renderer import export_png

            export_png(doc, Path(path))
