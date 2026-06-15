"""
File list panel — top-right area.

Displays loaded PSD files as thumbnail + filename entries.
Supports:
  - Drag-and-drop .psd files from the OS file manager.
  - Click to select a document for editing.
  - Add / remove buttons.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6.QtCore import QAbstractListModel, QMimeData, QModelIndex, Qt, Signal
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QImage, QPixmap
from PySide6.QtWidgets import (
    QHBoxLayout,
    QListView,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ...models import PsdDocument
from ...psd_manager import DocumentStore
from ...renderer import generate_doc_thumbnail


class FileListModel(QAbstractListModel):
    """Qt model backed by DocumentStore."""

    def __init__(self, store: DocumentStore, parent=None):
        super().__init__(parent)
        self._store = store

    def rowCount(self, parent=QModelIndex()):
        return len(self._store.documents)

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        doc = self._store.documents[index.row()]
        if role == Qt.ItemDataRole.DisplayRole:
            return doc.name
        if role == Qt.ItemDataRole.DecorationRole:
            thumb = generate_doc_thumbnail(doc)
            return _pil_to_qpixmap(thumb)
        return None

    def refresh(self):
        self.beginResetModel()
        self.endResetModel()


class FileListPanel(QWidget):
    """The file list panel shown in the top-right of the main window."""

    # Emitted when the user selects a different document.
    document_selected = Signal(int)  # index in store

    def __init__(self, store: DocumentStore, parent=None):
        super().__init__(parent)
        self._store = store
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # --- List view ---
        self._model = FileListModel(self._store)
        self._list_view = QListView()
        self._list_view.setModel(self._model)
        self._list_view.setIconSize(self._list_view.iconSize())  # default
        self._list_view.setDragDropMode(QListView.DragDropMode.NoDragDrop)
        self._list_view.setSelectionMode(QListView.SelectionMode.SingleSelection)
        self._list_view.clicked.connect(self._on_clicked)
        layout.addWidget(self._list_view)

        # --- Buttons ---
        btn_row = QHBoxLayout()
        self._btn_add = QPushButton("+ Add")
        self._btn_remove = QPushButton("− Remove")
        self._btn_add.clicked.connect(self._on_add)
        self._btn_remove.clicked.connect(self._on_remove)
        btn_row.addWidget(self._btn_add)
        btn_row.addWidget(self._btn_remove)
        layout.addLayout(btn_row)

        # --- Accept drops ---
        self.setAcceptDrops(True)

    # ------------------------------------------------------------------
    # Drag-and-drop
    # ------------------------------------------------------------------

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        for url in event.mimeData().urls():
            path = Path(url.toLocalFile())
            if path.suffix.lower() == ".psd":
                self._store.add_document(path)
        self._model.refresh()
        if self._store.selected_index is not None:
            self.document_selected.emit(self._store.selected_index)

    # ------------------------------------------------------------------
    # Button / click handlers
    # ------------------------------------------------------------------

    def _on_clicked(self, index: QModelIndex):
        self._store.select(index.row())
        self.document_selected.emit(index.row())

    def _on_add(self):
        from PySide6.QtWidgets import QFileDialog

        paths, _ = QFileDialog.getOpenFileNames(
            self, "Open PSD Files", "", "Photoshop Files (*.psd)"
        )
        for p in paths:
            self._store.add_document(Path(p))
        self._model.refresh()
        if self._store.selected_index is not None:
            self.document_selected.emit(self._store.selected_index)

    def _on_remove(self):
        idx = self._store.selected_index
        if idx is not None:
            self._store.remove_document(idx)
            self._model.refresh()
            self.document_selected.emit(
                self._store.selected_index if self._store.selected_index is not None else -1
            )

    def refresh(self):
        """Refresh the list after external changes."""
        self._model.refresh()

    def refresh_current_thumbnail(self):
        """Refresh the thumbnail for the currently selected document."""
        if self._store.selected_index is None:
            return
        doc = self._store.selected_document
        if doc is None:
            return
        # Invalidate so it is regenerated on next access.
        doc.invalidate_thumbnail()
        idx = self._model.index(self._store.selected_index, 0)
        if idx.isValid():
            self._model.dataChanged.emit(
                idx, idx, [Qt.ItemDataRole.DecorationRole]
            )


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _pil_to_qpixmap(pil_img) -> QPixmap:
    """Convert a PIL RGBA image to a QPixmap."""
    from PySide6.QtGui import QImage, QPixmap

    data = pil_img.tobytes("raw", "RGBA")
    qimg = QImage(data, pil_img.width, pil_img.height, QImage.Format.Format_RGBA8888)
    return QPixmap.fromImage(qimg)
