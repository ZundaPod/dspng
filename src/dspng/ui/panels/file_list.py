"""
File list panel — top-right area.

Displays loaded PSD files with per-item controls:
  thumbnail | inline-edit display name | export counter spinbox | undo button

Top row: size presets (S/M/L) + add / remove / reload.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import (
    QSize,
    Signal,
)
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QImage, QPixmap
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from ...psd_manager import DocumentStore
from ...renderer import generate_doc_thumbnail
from ..icon_manager import icon
from ..locale_manager import tr
from ..theme_tokens import SPACING_NONE

_SIZE_PRESETS = [32, 64, 128]
_SIZE_LABELS = {32: "S", 64: "M", 128: "L"}


class FileListPanel(QWidget):
    """The file list panel shown in the top-right of the main window."""

    document_selected = Signal(int)

    def __init__(self, store: DocumentStore, parent=None):
        super().__init__(parent)
        self._store = store
        self._current_size = 64
        self._item_widgets: dict[int, QWidget] = {}
        self._setup_ui()

        from ..locale_manager import LocaleManager

        LocaleManager().language_changed.connect(self._retranslate_ui)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            SPACING_NONE, SPACING_NONE, SPACING_NONE, SPACING_NONE
        )

        # --- Button row: size presets + add/remove/reload ---
        button_row = QHBoxLayout()
        self._size_buttons: list[QPushButton] = []

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

        self._btn_add = QPushButton()
        self._btn_add.setIcon(icon("actions", "plus"))
        self._btn_add.setIconSize(QSize(20, 20))
        self._btn_add.setToolTip(tr("Add file"))
        self._btn_remove = QPushButton()
        self._btn_remove.setIcon(icon("actions", "minus"))
        self._btn_remove.setIconSize(QSize(20, 20))
        self._btn_remove.setToolTip(tr("Remove file"))
        self._btn_reload = QPushButton()
        self._btn_reload.setIcon(icon("actions", "reload"))
        self._btn_reload.setIconSize(QSize(20, 20))
        self._btn_reload.setToolTip(tr("Reload file"))
        self._btn_add.clicked.connect(self._on_add)
        self._btn_remove.clicked.connect(self._on_remove)
        self._btn_reload.clicked.connect(self._on_reload)
        button_row.addWidget(self._btn_reload)
        button_row.addWidget(self._btn_add)
        button_row.addWidget(self._btn_remove)

        layout.addLayout(button_row)

        # --- List widget (per-item custom widgets) ---
        self._list = QListWidget()
        self._list.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._list.setIconSize(QSize(self._current_size, self._current_size))
        self._list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self._list.currentRowChanged.connect(self._on_row_changed)
        layout.addWidget(self._list, stretch=1)

        self.setAcceptDrops(True)

    # ------------------------------------------------------------------
    # Per-item widget factory
    # ------------------------------------------------------------------

    def _make_item_widget(self, index: int) -> QWidget:
        doc = self._store.documents[index]
        w = QWidget()
        row = QHBoxLayout(w)
        row.setContentsMargins(2, 2, 2, 2)
        row.setSpacing(4)

        # Thumbnail
        thumb_label = QLabel()
        thumb_label.setFixedSize(self._current_size, self._current_size)
        self._update_thumb(thumb_label, doc)
        row.addWidget(thumb_label)

        # Inline-edit display name
        name_edit = QLineEdit(doc.display_name or doc.name)
        name_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        name_edit.editingFinished.connect(
            lambda i=index, e=name_edit: self._on_name_changed(i, e)
        )
        row.addWidget(name_edit, stretch=1)

        # Export counter
        counter_spin = QSpinBox()
        counter_spin.setMinimum(1)
        counter_spin.setMaximum(9999)
        counter_spin.setValue(doc.export_counter)
        counter_spin.setToolTip(tr("Export counter"))
        counter_spin.valueChanged.connect(
            lambda v, i=index: self._on_counter_changed(i, v)
        )
        row.addWidget(counter_spin)

        return w

    def _update_thumb(self, label: QLabel, doc):
        thumb = generate_doc_thumbnail(doc, (self._current_size, self._current_size))
        data = thumb.tobytes("raw", "RGBA")
        qimg = QImage(data, thumb.width, thumb.height, QImage.Format.Format_RGBA8888)
        label.setPixmap(QPixmap.fromImage(qimg))

    # ------------------------------------------------------------------
    # Public refresh
    # ------------------------------------------------------------------

    def refresh(self):
        self._list.blockSignals(True)
        self._list.clear()
        self._item_widgets.clear()
        for i in range(len(self._store.documents)):
            item = QListWidgetItem()
            item.setSizeHint(QSize(0, self._current_size + 8))
            self._list.addItem(item)
            widget = self._make_item_widget(i)
            self._list.setItemWidget(item, widget)
            self._item_widgets[i] = widget
        if self._store.selected_index is not None:
            self._list.setCurrentRow(self._store.selected_index)
        self._list.blockSignals(False)

    def refresh_current_thumbnail(self):
        idx = self._store.selected_index
        if idx is None:
            return
        doc = self._store.selected_document
        if doc is None:
            return
        doc.invalidate_thumbnail()
        w = self._item_widgets.get(idx)
        if w:
            thumb_label = w.layout().itemAt(0).widget()
            if isinstance(thumb_label, QLabel):
                self._update_thumb(thumb_label, doc)

    # ------------------------------------------------------------------
    # Slots

    def refresh_counter(self):
        idx = self._store.selected_index
        if idx is None:
            return
        doc = self._store.selected_document
        if doc is None:
            return
        w = self._item_widgets.get(idx)
        if w:
            spin = w.layout().itemAt(2).widget()
            if isinstance(spin, QSpinBox):
                spin.blockSignals(True)
                spin.setValue(doc.export_counter)
                spin.blockSignals(False)

    # ------------------------------------------------------------------

    def _on_row_changed(self, row: int):
        if 0 <= row < len(self._store.documents):
            self._store.selected_index = row
            self.document_selected.emit(row)

    def _on_name_changed(self, index: int, edit: QLineEdit):
        doc = self._store.documents[index]
        text = edit.text().strip()
        if text:
            doc.display_name = text

    def _on_counter_changed(self, index: int, value: int):
        self._store.documents[index].export_counter = value

    def _set_size(self, px: int):
        if px == self._current_size:
            return
        self._current_size = px
        self._list.setIconSize(QSize(px, px))
        for doc in self._store.documents:
            doc.invalidate_thumbnail()
        label = _SIZE_LABELS.get(px, str(px))
        for btn in self._size_buttons:
            btn.setChecked(btn.text() == label)
        self.refresh()

    # ------------------------------------------------------------------
    # Drag-and-drop
    # ------------------------------------------------------------------

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        errors: list[str] = []
        for url in event.mimeData().urls():
            path = Path(url.toLocalFile())
            if path.suffix.lower() == ".psd":
                try:
                    self._store.add_document(path)
                except Exception as e:
                    errors.append(f"{path.name}: {e}")
        self.refresh()
        if self._store.selected_index is not None:
            self.document_selected.emit(self._store.selected_index)
        if errors:
            msg = "Failed to load:\n" + "\n".join(errors)
            QMessageBox.warning(self, tr("Load Error"), msg)

    # ------------------------------------------------------------------
    # Button handlers
    # ------------------------------------------------------------------

    def _on_add(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, tr("Open PSD Files"), "", tr("Photoshop Files (*.psd)")
        )
        loaded = 0
        errors: list[str] = []
        for p in paths:
            try:
                self._store.add_document(Path(p))
                loaded += 1
            except Exception as e:
                errors.append(f"{Path(p).name}: {e}")
        self.refresh()
        if self._store.selected_index is not None:
            self.document_selected.emit(self._store.selected_index)
        if errors:
            msg = "Failed to load:\n" + "\n".join(errors)
            QMessageBox.warning(self, tr("Load Error"), msg)

    def _on_remove(self):
        idx = self._store.selected_index
        if idx is not None:
            self._store.remove_document(idx)
            self.refresh()
            self.document_selected.emit(
                self._store.selected_index
                if self._store.selected_index is not None
                else -1
            )

    def _on_reload(self):
        idx = self._store.selected_index
        if idx is None:
            return
        doc = self._store.selected_document
        if doc is None:
            return
        path = doc.path
        self._store.remove_document(idx)
        try:
            self._store.add_document(path)
        except Exception as e:
            QMessageBox.warning(
                self, tr("Reload Error"), f"Failed to reload {path.name}: {e}"
            )
            return
        self.refresh()
        if self._store.selected_index is not None:
            self.document_selected.emit(self._store.selected_index)

    # ------------------------------------------------------------------
    # i18n
    # ------------------------------------------------------------------

    def _retranslate_ui(self):
        self._btn_reload.setToolTip(tr("Reload file"))
        self._btn_add.setToolTip(tr("Add file"))
        self._btn_remove.setToolTip(tr("Remove file"))
