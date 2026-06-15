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
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QActionGroup, QIcon
from PySide6.QtWidgets import (
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
from .panels.file_list import FileListPanel
from .panels.layer_panel import LayerPanel
from .panels.render_canvas import RenderCanvas
from .settings import get_accent, get_mode, load, save
from .styles import generate_stylesheet
from .themes import (
    ACCENT_LABELS,
    MODE_LABELS,
    Accent,
    Theme,
    ThemeMode,
    make_dark,
    make_light,
)


class MainWindow(QMainWindow):
    """Top-level window that hosts all three panels."""

    def __init__(self):
        super().__init__()

        self.setWindowTitle("dspng — PSD → PNG")
        self.resize(1200, 800)
        self._set_window_icon()

        # Load persisted settings and apply theme.
        self._settings = load()
        self._mode = get_mode(self._settings)
        self._accent = get_accent(self._settings)
        self._theme: Theme = make_dark(self._accent)
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

        # Menu bar
        self._setup_file_menu()
        self._setup_view_menu()

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
                    from PySide6.QtWidgets import QApplication
                    app = QApplication.instance()
                    if app is not None:
                        app.setWindowIcon(icon)
                    return

    # ------------------------------------------------------------------
    # Theme
    # ------------------------------------------------------------------

    def _apply_theme(self):
        """Resolve the current mode (handle SYSTEM) and apply the stylesheet."""
        mode = self._mode
        if mode == ThemeMode.SYSTEM:
            # Detect system preference via palette.
            # PySide6 doesn't expose a direct API, so use a heuristic:
            # check if the window's default background is light or dark.
            from PySide6.QtGui import QGuiApplication

            palette = QGuiApplication.palette()
            bg = palette.window().color()
            is_dark = bg.lightnessF() < 0.5
            mode = ThemeMode.DARK if is_dark else ThemeMode.LIGHT

        self._theme = make_dark(self._accent) if mode == ThemeMode.DARK else make_light(self._accent)
        self.setStyleSheet(generate_stylesheet(self._theme))

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------

    @staticmethod
    def _make_panel(title: str, widget: QWidget) -> QWidget:
        """Wrap *widget* in a container with a title label and border."""
        container = QFrame()
        container.setFrameShape(QFrame.Shape.StyledPanel)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        label = QLabel(title.upper())
        label.setObjectName("panelTitle")
        layout.addWidget(label)
        layout.addWidget(widget, stretch=1)
        return container

    def _setup_layout(self):
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QHBoxLayout(central)
        root_layout.setContentsMargins(4, 4, 4, 4)

        h_splitter = QSplitter(Qt.Orientation.Horizontal)
        h_splitter.addWidget(self._make_panel("Render", self._canvas))
        h_splitter.setStretchFactor(0, 3)

        v_splitter = QSplitter(Qt.Orientation.Vertical)
        v_splitter.addWidget(self._make_panel("Files", self._file_list))
        v_splitter.addWidget(self._make_panel("Layers", self._layer_panel))
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
        menu = self.menuBar().addMenu("&File")

        act_open = QAction("&Open…", self)
        act_open.setShortcut("Ctrl+O")
        act_open.triggered.connect(self._on_open)
        menu.addAction(act_open)

        act_export = QAction("&Export PNG…", self)
        act_export.setShortcut("Ctrl+E")
        act_export.triggered.connect(self._on_export)
        menu.addAction(act_export)

        menu.addSeparator()

        act_quit = QAction("&Quit", self)
        act_quit.setShortcut("Ctrl+Q")
        act_quit.triggered.connect(self.close)
        menu.addAction(act_quit)

    def _setup_view_menu(self):
        menu = self.menuBar().addMenu("&View")

        # ---- Theme mode submenu ----
        mode_menu = menu.addMenu("Theme")
        mode_group = QActionGroup(self)
        mode_group.setExclusive(True)

        for mode in ThemeMode:
            act = QAction(MODE_LABELS[mode], self)
            act.setCheckable(True)
            act.setChecked(self._mode == mode)
            act.triggered.connect(lambda checked, m=mode: self._set_mode(m))
            mode_group.addAction(act)
            mode_menu.addAction(act)

        menu.addSeparator()

        # ---- Accent submenu ----
        accent_menu = menu.addMenu("Accent")
        accent_group = QActionGroup(self)
        accent_group.setExclusive(True)

        for accent in Accent:
            act = QAction(ACCENT_LABELS[accent], self)
            act.setCheckable(True)
            act.setChecked(self._accent == accent)
            act.triggered.connect(lambda checked, a=accent: self._set_accent(a))
            accent_group.addAction(act)
            accent_menu.addAction(act)

    # ------------------------------------------------------------------
    # Theme actions
    # ------------------------------------------------------------------

    def _set_mode(self, mode: ThemeMode):
        self._mode = mode
        self._settings["theme_mode"] = mode.value
        save(self._settings)
        self._apply_theme()

    def _set_accent(self, accent: Accent):
        self._accent = accent
        self._settings["accent"] = accent.value
        save(self._settings)
        self._apply_theme()

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

    def _on_open(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Open PSD Files", "", "Photoshop Files (*.psd)"
        )
        for p in paths:
            self._store.add_document(Path(p))
        self._file_list.refresh()
        doc = self._store.selected_document
        self._canvas.set_document(doc)
        self._layer_panel.set_document(doc)

    def _on_export(self):
        doc = self._store.selected_document
        if doc is None:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Export PNG", f"{doc.name}.png", "PNG Image (*.png)"
        )
        if path:
            from ..renderer import export_png

            export_png(doc, Path(path))
