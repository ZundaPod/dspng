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

from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QMainWindow,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from ..psd_manager import DocumentStore
from .panels.file_list import FileListPanel
from .panels.layer_panel import LayerPanel
from .panels.render_canvas import RenderCanvas


class MainWindow(QMainWindow):
    """Top-level window that hosts all three panels."""

    def __init__(self):
        super().__init__()

        self.setWindowTitle("dspng — PSD → PNG")
        self.resize(1200, 800)

        # Central state
        self._store = DocumentStore()

        # Build panels
        self._file_list = FileListPanel(self._store)
        self._layer_panel = LayerPanel()
        self._canvas = RenderCanvas()

        # Layout: horizontal splitter (canvas | right column)
        # Right column: vertical splitter (file list | layer panel)
        self._setup_layout()

        # Wire up signals
        self._file_list.document_selected.connect(self._on_document_selected)
        self._layer_panel.layer_visibility_changed.connect(self._on_visibility_changed)
        self._layer_panel.thumbnail_changed.connect(self._on_thumbnail_changed)

        # Menu bar (File → Open / Export / Quit)
        self._setup_menu()

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------

    def _setup_layout(self):
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QHBoxLayout(central)
        root_layout.setContentsMargins(4, 4, 4, 4)

        # Horizontal splitter: canvas (left) | right column (right)
        h_splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left: render canvas
        h_splitter.addWidget(self._canvas)
        h_splitter.setStretchFactor(0, 3)  # canvas gets 3/4 of space

        # Right column: vertical splitter (file list on top, layers on bottom)
        v_splitter = QSplitter(Qt.Orientation.Vertical)
        v_splitter.addWidget(self._file_list)
        v_splitter.addWidget(self._layer_panel)
        v_splitter.setStretchFactor(0, 1)  # file list gets 1/3
        v_splitter.setStretchFactor(1, 2)  # layer panel gets 2/3

        h_splitter.addWidget(v_splitter)
        h_splitter.setStretchFactor(1, 1)  # right column gets 1/4

        root_layout.addWidget(h_splitter)

    # ------------------------------------------------------------------
    # Menu
    # ------------------------------------------------------------------

    def _setup_menu(self):
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
        """Refresh the file list thumbnail for the current document."""
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
