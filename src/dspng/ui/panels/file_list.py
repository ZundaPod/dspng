"""
File list panel — top-right area.

Displays loaded PSD files as thumbnail + filename entries.
Supports:
  - Drag-and-drop .psd files from the OS file manager.
  - Click to select a document for editing.
  - Add / remove buttons.
  - Three fixed row size presets: 32, 64, 128 px.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import (
    QAbstractListModel,
    QModelIndex,
    QSize,
    Qt,
    Signal,
)
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QImage, QPixmap
from PySide6.QtWidgets import (
    QHBoxLayout,
    QListView,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from ...psd_manager import DocumentStore
from ...renderer import generate_doc_thumbnail
from ..theme_tokens import SPACING_NONE

# Available row height presets.
_SIZE_PRESETS = [32, 64, 128]

# Maps pixel size → label for buttons.
_SIZE_LABELS = {32: "S", 64: "M", 128: "L"}


class FileListModel(QAbstractListModel):
    """Qt model backed by DocumentStore.

    Thumbnails are generated on the fly at the *icon_size* passed
    during construction.  Call `set_icon_size()` to resize.
    """

    def __init__(self, store: DocumentStore, icon_size: int = 64, parent=None):
        super().__init__(parent)
        self._store = store
        self._icon_size = icon_size

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_icon_size(self, size: int) -> None:
        """Change the thumbnail size and refresh all rows."""
        self._icon_size = size
        self.refresh()

    # ------------------------------------------------------------------
    # QAbstractListModel interface
    # ------------------------------------------------------------------

    def rowCount(self, parent=QModelIndex()):
        return len(self._store.documents)

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        doc = self._store.documents[index.row()]
        if role == Qt.ItemDataRole.DisplayRole:
            return doc.name
        if role == Qt.ItemDataRole.DecorationRole:
            thumb = generate_doc_thumbnail(doc, (self._icon_size, self._icon_size))
            return _pil_to_qpixmap(thumb)
        return None

    def refresh(self):
        self.beginResetModel()
        self.endResetModel()


class FileListPanel(QWidget):
    """The file list panel shown in the top-right of the main window."""

    document_selected = Signal(int)

    def __init__(self, store: DocumentStore, parent=None):
        super().__init__(parent)
        self._store = store
        self._current_size = 64
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            SPACING_NONE, SPACING_NONE, SPACING_NONE, SPACING_NONE
        )

        # --- Button row: size presets + add/remove buttons ---
        button_row = QHBoxLayout()
        self._size_buttons: list[QPushButton] = []

        # Size preset buttons (S / M / L).
        for px in _SIZE_PRESETS:
            label = _SIZE_LABELS.get(px, str(px))
            btn = QPushButton(label)
            btn.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
            btn.setCheckable(True)
            if px == self._current_size:
                btn.setChecked(True)
            btn.clicked.connect(lambda checked, s=px: self._set_size(s))
            button_row.addWidget(btn)
            self._size_buttons.append(btn)

        button_row.addStretch()

        self._btn_add = QPushButton("+ Add")
        self._btn_remove = QPushButton("− Remove")
        self._btn_reload = QPushButton("Reload")
        self._btn_add.clicked.connect(self._on_add)
        self._btn_remove.clicked.connect(self._on_remove)
        self._btn_reload.clicked.connect(self._on_reload)
        button_row.addWidget(self._btn_reload)
        button_row.addWidget(self._btn_add)
        button_row.addWidget(self._btn_remove)

        layout.addLayout(button_row)

        # --- List view ---
        self._model = FileListModel(self._store, self._current_size)
        self._list_view = QListView()
        self._list_view.setModel(self._model)
        self._list_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._list_view.setIconSize(QSize(self._current_size, self._current_size))
        self._list_view.setDragDropMode(QListView.DragDropMode.NoDragDrop)
        self._list_view.setSelectionMode(QListView.SelectionMode.SingleSelection)
        self._list_view.clicked.connect(self._on_clicked)
        layout.addWidget(self._list_view, stretch=1)

        # --- Accept drops ---
        self.setAcceptDrops(True)

    # ------------------------------------------------------------------
    # Size presets
    # ------------------------------------------------------------------

    def _set_size(self, px: int):
        """Switch to a new thumbnail size, regenerating all thumbnails."""
        if px == self._current_size:
            return
        self._current_size = px
        self._list_view.setIconSize(QSize(px, px))

        # Invalidate cached thumbnails so they regenerate at the new size.
        for doc in self._store.documents:
            doc.invalidate_thumbnail()

        self._model.set_icon_size(px)

        # Update the checked state on size buttons.
        label = _SIZE_LABELS.get(px, str(px))
        for btn in self._size_buttons:
            btn.setChecked(btn.text() == label)

    # ------------------------------------------------------------------
    # Drag-and-drop
    # ------------------------------------------------------------------

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        from PySide6.QtWidgets import QMessageBox

        errors: list[str] = []
        for url in event.mimeData().urls():
            path = Path(url.toLocalFile())
            if path.suffix.lower() == ".psd":
                try:
                    self._store.add_document(path)
                except Exception as e:
                    errors.append(f"{path.name}: {e}")
        self._model.refresh()
        if self._store.selected_index is not None:
            self.document_selected.emit(self._store.selected_index)
        if errors:
            msg = "Failed to load:\n" + "\n".join(errors)
            QMessageBox.warning(self, "Load Error", msg)

    # ------------------------------------------------------------------
    # Button / click handlers
    # ------------------------------------------------------------------

    def _on_clicked(self, index: QModelIndex):
        self._store.select(index.row())
        self.document_selected.emit(index.row())

    def _on_add(self):
        from PySide6.QtWidgets import QFileDialog, QMessageBox

        paths, _ = QFileDialog.getOpenFileNames(
            self, "Open PSD Files", "", "Photoshop Files (*.psd)"
        )
        loaded = 0
        errors: list[str] = []
        for p in paths:
            try:
                self._store.add_document(Path(p))
                loaded += 1
            except Exception as e:
                errors.append(f"{Path(p).name}: {e}")
        self._model.refresh()
        if self._store.selected_index is not None:
            self.document_selected.emit(self._store.selected_index)
        if errors:
            msg = "Failed to load:\n" + "\n".join(errors)
            QMessageBox.warning(self, "Load Error", msg)

    def _on_remove(self):
        idx = self._store.selected_index
        if idx is not None:
            self._store.remove_document(idx)
            self._model.refresh()
            self.document_selected.emit(
                self._store.selected_index
                if self._store.selected_index is not None
                else -1
            )

    def _on_reload(self):
        """Re-read the currently selected PSD file from disk."""
        idx = self._store.selected_index
        if idx is None:
            return
        doc = self._store.selected_document
        if doc is None:
            return
        path = doc.path
        # Remove and re-add to trigger a fresh parse.
        self._store.remove_document(idx)
        try:
            self._store.add_document(path)
        except Exception as e:
            from PySide6.QtWidgets import QMessageBox

            QMessageBox.warning(
                self, "Reload Error", f"Failed to reload {path.name}: {e}"
            )
            return
        self._model.refresh()
        if self._store.selected_index is not None:
            self.document_selected.emit(self._store.selected_index)

    def refresh(self):
        self._model.refresh()

    def refresh_current_thumbnail(self):
        if self._store.selected_index is None:
            return
        doc = self._store.selected_document
        if doc is None:
            return
        doc.invalidate_thumbnail()
        idx = self._model.index(self._store.selected_index, 0)
        if idx.isValid():
            self._model.dataChanged.emit(idx, idx, [Qt.ItemDataRole.DecorationRole])


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------


def _pil_to_qpixmap(pil_img) -> QPixmap:
    data = pil_img.tobytes("raw", "RGBA")
    qimg = QImage(data, pil_img.width, pil_img.height, QImage.Format.Format_RGBA8888)
    return QPixmap.fromImage(qimg)
