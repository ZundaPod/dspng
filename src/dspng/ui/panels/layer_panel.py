"""
Layer panel — bottom-right area.

Displays the layer tree of the currently selected PSD document.
Each row shows: thumbnail | name | visibility toggle.

Supports:
  - Tree structure (groups containing layers).
  - Click visibility icon to toggle a layer/group (via custom delegate).
  - Drag-and-drop to reorder layers/groups.
  - Uniform row height with slider control.
  - Updates propagate to the renderer via signals.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6.QtCore import (
    QAbstractItemModel,
    QMimeData,
    QModelIndex,
    QObject,
    QSize,
    Qt,
    Signal,
)
from PySide6.QtGui import QColor, QImage, QPainter, QPixmap
from PySide6.QtWidgets import (
    QHBoxLayout,
    QHeaderView,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QStyledItemDelegate,
    QTreeView,
    QVBoxLayout,
    QWidget,
)

from ...models import LayerGroup, LayerNode, PsdDocument, TreeItem
from ...renderer import (
    generate_group_thumbnail,
    generate_layer_thumbnail,
)
from ..icon_manager import icon
from ..locale_manager import tr
from ..theme_tokens import SPACING_NONE


# ======================================================================
# Helper: PIL -> QPixmap
# ======================================================================

# Checkerboard tile for transparent backgrounds.
_CHECKER = None


def _checkerboard_pixmap(size: int = 64) -> QPixmap:
    """Return a cached checkerboard QPixmap of *size* x *size*."""
    global _CHECKER
    if _CHECKER is not None and _CHECKER.width() == size:
        return _CHECKER
    img = QImage(size, size, QImage.Format.Format_RGB32)
    c1 = QColor(204, 204, 204)
    c2 = QColor(255, 255, 255)
    cell = 8
    for y in range(0, size, cell):
        for x in range(0, size, cell):
            color = c1 if ((x // cell) + (y // cell)) % 2 == 0 else c2
            for dy in range(min(cell, size - y)):
                for dx in range(min(cell, size - x)):
                    img.setPixelColor(x + dx, y + dy, color)
    _CHECKER = QPixmap.fromImage(img)
    return _CHECKER


def _pil_to_qpixmap(pil_img) -> QPixmap:
    """Convert a PIL RGBA image to QPixmap.

    The thumbnail is composited onto a checkerboard background so
    transparent regions are visible.
    """
    w, h = pil_img.size
    result = QPixmap(w, h)
    result.fill(Qt.GlobalColor.transparent)

    painter = QPainter(result)
    # Tile the checkerboard.
    checker = _checkerboard_pixmap()
    for cy in range(0, h, checker.height()):
        for cx in range(0, w, checker.width()):
            painter.drawPixmap(cx, cy, checker)
    # Draw the thumbnail on top.
    data = pil_img.tobytes("raw", "RGBA")
    qimg = QImage(data, w, h, QImage.Format.Format_RGBA8888)
    painter.drawPixmap(0, 0, QPixmap.fromImage(qimg))
    painter.end()
    return result


# ======================================================================
# Visibility Delegate
# ======================================================================


class _VisibilityDelegate(QStyledItemDelegate):
    """Delegate for the visibility column (column 1).

    Renders an eye (visible) or eye-off (hidden) icon button.
    Using a real widget delegate avoids the PySide6 quirk where
    ItemIsUserCheckable + setData(CheckStateRole) does not reliably
    update the visual state.
    """

    visibility_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

    def createEditor(self, parent, option, index):
        btn = QPushButton(parent)
        btn.setFlat(True)
        btn.setIconSize(QSize(18, 18))
        btn.clicked.connect(lambda checked, idx=index: self._on_clicked(idx))
        return btn

    def setEditorData(self, editor: QPushButton, index: QModelIndex):
        state = index.data(Qt.ItemDataRole.CheckStateRole)
        visible = state == Qt.CheckState.Checked
        self._set_eye_icon(editor, visible)

    def setModelData(self, editor, model, index):
        pass

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)

    def paint(self, painter, option, index):
        pass

    def _on_clicked(self, index: QModelIndex):
        model = index.model()
        if model is None:
            return
        current = index.data(Qt.ItemDataRole.CheckStateRole)
        new_state = (
            Qt.CheckState.Unchecked
            if current == Qt.CheckState.Checked
            else Qt.CheckState.Checked
        )
        model.setData(index, new_state, Qt.ItemDataRole.CheckStateRole)
        self.visibility_changed.emit()

    @staticmethod
    def _set_eye_icon(btn: QPushButton, visible: bool):
        name = "eye" if visible else "eye-closed"
        btn.setIcon(icon("status", name))
        btn.setIconSize(QSize(18, 18))


# ======================================================================
# Tree Model
# ======================================================================


class _TreeItemWrapper:
    """Wraps a TreeItem so the QTreeView model can point to a unique node."""

    def __init__(
        self, item: TreeItem, parent_wrapper: Optional[_TreeItemWrapper] = None
    ):
        self.item = item
        self.parent_wrapper = parent_wrapper
        self.children_wrappers: list[_TreeItemWrapper] = []

    @property
    def row_in_parent(self) -> int:
        if self.parent_wrapper is None:
            return 0
        return self.parent_wrapper.children_wrappers.index(self)


class LayerTreeModel(QAbstractItemModel):
    """Qt model that exposes the PsdDocument layer tree."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._doc: Optional[PsdDocument] = None
        self._root = _TreeItemWrapper(LayerGroup(name="__root__", children=[]))
        self._thumb_size = 64  # default, updated by LayerPanel

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_document(self, doc: Optional[PsdDocument]):
        self.beginResetModel()
        self._doc = doc
        self._rebuild()
        self.endResetModel()

    def invalidate_all_thumbnails(self):
        """Clear every cached thumbnail in the tree + document."""
        if self._doc is None:
            return
        self._doc.invalidate_thumbnail()
        self._invalidate_recursive(self._doc.layer_tree)

    def refresh_thumbnails_for_size(self, size: tuple[int, int]):
        """Regenerate all thumbnails at the given pixel size."""
        if self._doc is None:
            return

        self._regen_recursive(self._doc.layer_tree, self._doc, size)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _invalidate_recursive(self, items: list[TreeItem]):
        for item in items:
            item.invalidate_thumbnail()
            if isinstance(item, LayerGroup):
                self._invalidate_recursive(item.children)

    def _regen_recursive(
        self, items: list[TreeItem], doc: PsdDocument, size: tuple[int, int]
    ):
        for item in items:
            if isinstance(item, LayerNode):
                generate_layer_thumbnail(item, size)
            elif isinstance(item, LayerGroup):
                self._regen_recursive(item.children, doc, size)
                generate_group_thumbnail(item, doc, size)

    def _rebuild(self):
        self._root = _TreeItemWrapper(LayerGroup(name="__root__", children=[]))
        if self._doc is None:
            return
        self._root.item = LayerGroup(name="__root__", children=self._doc.layer_tree)
        self._populate_children(self._root)

    def _populate_children(self, wrapper: _TreeItemWrapper):
        item = wrapper.item
        children: list[TreeItem] = []
        if isinstance(item, LayerGroup):
            children = item.children
        # Rebuild wrappers from scratch (reversed for display order).
        wrapper.children_wrappers.clear()
        for child in reversed(children):
            child_w = _TreeItemWrapper(child, parent_wrapper=wrapper)
            wrapper.children_wrappers.append(child_w)
            self._populate_children(child_w)

    def _wrapper_for_index(self, index: QModelIndex) -> _TreeItemWrapper:
        if not index.isValid():
            return self._root
        return index.internalPointer()

    # ------------------------------------------------------------------
    # QAbstractItemModel interface
    # ------------------------------------------------------------------

    def index(self, row: int, column: int, parent=QModelIndex()):
        if not self.hasIndex(row, column, parent):
            return QModelIndex()
        parent_w = self._wrapper_for_index(parent)
        if row >= len(parent_w.children_wrappers):
            return QModelIndex()
        child_w = parent_w.children_wrappers[row]
        return self.createIndex(row, column, child_w)

    def parent(self, index: QModelIndex):
        if not index.isValid():
            return QModelIndex()
        child_w: _TreeItemWrapper = index.internalPointer()
        parent_w = child_w.parent_wrapper
        if parent_w is None or parent_w is self._root:
            return QModelIndex()
        return self.createIndex(parent_w.row_in_parent, 0, parent_w)

    def rowCount(self, parent=QModelIndex()):
        parent_w = self._wrapper_for_index(parent)
        return len(parent_w.children_wrappers)

    def columnCount(self, parent=QModelIndex()):
        return 2  # 0 = name+thumb, 1 = visibility

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        wrapper: _TreeItemWrapper = index.internalPointer()
        item = wrapper.item

        col = index.column()

        if role == Qt.ItemDataRole.DisplayRole:
            if col == 0:
                return item.name
            return None

        if role == Qt.ItemDataRole.DecorationRole and col == 0:
            size = (self._thumb_size, self._thumb_size)
            if isinstance(item, LayerNode):
                thumb = generate_layer_thumbnail(item, size)
            elif isinstance(item, LayerGroup):
                if self._doc is not None:
                    thumb = generate_group_thumbnail(item, self._doc, size)
                else:
                    return None
            else:
                return None
            return _pil_to_qpixmap(thumb)

        if role == Qt.ItemDataRole.CheckStateRole and col == 1:
            return Qt.CheckState.Checked if item.visible else Qt.CheckState.Unchecked

        return None

    def setData(self, index: QModelIndex, value, role=Qt.ItemDataRole.EditRole):
        if not index.isValid():
            return False
        wrapper: _TreeItemWrapper = index.internalPointer()
        item = wrapper.item

        if role == Qt.ItemDataRole.CheckStateRole and index.column() == 1:
            new_visible = value == Qt.CheckState.Checked
            if item.visible == new_visible:
                return True
            item.visible = new_visible
            # Invalidate cached thumbnails for the item and its ancestors.
            item.invalidate_thumbnail()
            pw = wrapper.parent_wrapper
            while pw is not None and pw is not self._root:
                pw.item.invalidate_thumbnail()
                pw = pw.parent_wrapper
            if self._doc is not None:
                self._doc.invalidate_thumbnail()
            self.dataChanged.emit(index, index, [role])
            return True
        return False

    def move_item(self, index: QModelIndex, direction: int) -> bool:
        """Swap *index* with its sibling *direction* positions away.

        ``direction`` = -1 means "move up" in the data model (which is the
        top of the display list) and +1 means "move down".

        Returns True if the swap happened.
        """
        if not index.isValid():
            return False
        wrapper: _TreeItemWrapper = index.internalPointer()
        parent_w = wrapper.parent_wrapper
        if parent_w is None:
            return False

        children = parent_w.item.children
        idx = children.index(wrapper.item)
        target = idx + direction
        if target < 0 or target >= len(children):
            return False

        children[idx], children[target] = children[target], children[idx]
        self.beginResetModel()
        self._populate_children(parent_w)
        self.invalidate_all_thumbnails()
        self.endResetModel()
        return True

    def flags(self, index: QModelIndex):
        if not index.isValid():
            return Qt.ItemFlag.ItemIsDropEnabled
        base = (
            Qt.ItemFlag.ItemIsEnabled
            | Qt.ItemFlag.ItemIsSelectable
            | Qt.ItemFlag.ItemIsDragEnabled
            | Qt.ItemFlag.ItemIsDropEnabled
        )
        if index.column() == 1:
            base |= Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEditable
        return base

    # ------------------------------------------------------------------
    # Supported drag & drop
    # ------------------------------------------------------------------

    def supportedDropActions(self):
        return Qt.DropAction.MoveAction

    def mimeTypes(self):
        return ["application/x-dspng-layer"]

    def mimeData(self, indexes):
        mime = QMimeData()
        wrappers = [idx.internalPointer() for idx in indexes if idx.column() == 0]
        mime.setData(
            "application/x-dspng-layer",
            ",".join(str(id(w)) for w in wrappers).encode(),
        )
        # Also keep a direct reference so the objects stay alive.
        mime.setProperty("wrappers", wrappers)
        return mime

    def canDropMimeData(self, data, action, row, column, parent):
        """Allow drops at root level and into ``LayerGroup`` items only."""
        if action != Qt.DropAction.MoveAction:
            return False
        # Root level — always valid.
        if not parent.isValid():
            return True
        wrapper = parent.internalPointer()
        return isinstance(wrapper.item, LayerGroup)

    def dropMimeData(self, data, action, row, column, parent):
        if action != Qt.DropAction.MoveAction:
            return False

        wrappers = data.property("wrappers")
        if not wrappers:
            return False

        src_wrapper: _TreeItemWrapper = wrappers[0]
        if src_wrapper is self._root or src_wrapper.parent_wrapper is None:
            return False

        dest_wrapper = self._wrapper_for_index(parent)

        # Prevent dropping onto self or a descendant.
        if src_wrapper is dest_wrapper:
            return False
        pw = dest_wrapper
        while pw is not None and pw is not self._root:
            if pw is src_wrapper:
                return False
            pw = pw.parent_wrapper

        src_parent = src_wrapper.parent_wrapper
        same_parent = src_parent is dest_wrapper
        src_children: list = src_parent.item.children

        # For same-parent moves, compute the target data index *before*
        # removal because Qt's ``row`` is relative to the original layout.
        if same_parent:
            old_data_idx = src_children.index(src_wrapper.item)
            n_before = len(src_children)
            if row < 0 or row >= n_before:
                data_idx = 0  # bottom of display = start of data
            else:
                # item.children is bottom-to-top; display is top-to-bottom.
                # n - row converts display row to data insertion index.
                data_idx = n_before - row
            # If target is past the source, removal shifts it by one.
            if old_data_idx < data_idx:
                data_idx -= 1

        # Remove from source parent.
        src_children.remove(src_wrapper.item)

        # For cross-parent moves, compute position in the destination
        # (which never contained the source, so no shift is needed).
        dest_children: list = dest_wrapper.item.children
        if not same_parent:
            n = len(dest_children)
            if row < 0 or row >= n:
                data_idx = 0
            else:
                data_idx = n - row

        dest_children.insert(data_idx, src_wrapper.item)

        # Rebuild wrappers from the data model.
        self.beginResetModel()
        if not same_parent:
            self._populate_children(src_parent)
        self._populate_children(dest_wrapper)
        self.invalidate_all_thumbnails()
        self.endResetModel()
        return True


# ======================================================================
# Panel Widget
# ======================================================================


class LayerPanel(QWidget):
    """Layer panel shown in the bottom-right of the main window."""

    # Emitted whenever a layer's visibility changes.
    layer_visibility_changed = Signal()

    # Emitted when layers are reordered.
    layer_order_changed = Signal()

    # Emitted when a visibility change should refresh the file list thumbnail.
    thumbnail_changed = Signal()

    # Available row height presets.
    _SIZE_PRESETS = [32, 64, 128]
    _SIZE_LABELS = {32: "S", 64: "M", 128: "L"}

    def __init__(self, parent=None):
        super().__init__(parent)
        self._doc: Optional[PsdDocument] = None
        self._thumb_size = self._SIZE_PRESETS[1]  # default: M
        self._setup_ui()
        self._update_vis_all_button()

        from ..locale_manager import LocaleManager

        LocaleManager().language_changed.connect(self._retranslate_ui)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            SPACING_NONE, SPACING_NONE, SPACING_NONE, SPACING_NONE
        )

        # --- Button row: size presets + up/down buttons ---
        button_row = QHBoxLayout()
        self._size_buttons: list[QPushButton] = []
        for px in self._SIZE_PRESETS:
            label = self._SIZE_LABELS.get(px, str(px))
            btn = QPushButton(label)
            btn.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
            btn.setCheckable(True)
            if px == self._thumb_size:
                btn.setChecked(True)
            btn.clicked.connect(lambda checked, s=px: self._set_size(s))
            button_row.addWidget(btn)
            self._size_buttons.append(btn)

        button_row.addStretch()

        # Expand/collapse all
        self._btn_expand_all = QPushButton()
        self._btn_expand_all.setIcon(icon("arrows", "layout-navbar-expand"))
        btn.setIconSize(QSize(20, 20))
        self._btn_expand_all.setToolTip(tr("Expand all groups"))
        self._btn_expand_all.clicked.connect(self._expand_all)
        button_row.addWidget(self._btn_expand_all)

        self._btn_collapse_all = QPushButton()
        self._btn_collapse_all.setIcon(icon("arrows", "layout-navbar-collapse"))
        btn.setIconSize(QSize(20, 20))
        self._btn_collapse_all.setToolTip(tr("Collapse all groups"))
        self._btn_collapse_all.clicked.connect(self._collapse_all)
        button_row.addWidget(self._btn_collapse_all)

        # Tri-state visibility (eye icon)
        self._btn_vis_all = QPushButton()
        self._btn_vis_all.setFlat(True)
        self._btn_vis_all.setIconSize(QSize(18, 18))
        self._btn_vis_all.setToolTip(tr("Toggle all visibility"))
        self._btn_vis_all.clicked.connect(self._on_vis_all_clicked)
        button_row.addWidget(self._btn_vis_all)

        # Up/down
        self._btn_up = QPushButton()
        self._btn_up.setIcon(icon("arrows", "arrow-up"))
        btn.setIconSize(QSize(20, 20))
        self._btn_up.setToolTip(tr("Move up"))
        self._btn_down = QPushButton()
        self._btn_down.setIcon(icon("arrows", "arrow-down"))
        btn.setIconSize(QSize(20, 20))
        self._btn_down.setToolTip(tr("Move down"))
        self._btn_up.clicked.connect(lambda: self._move_selected(1))
        self._btn_down.clicked.connect(lambda: self._move_selected(-1))
        button_row.addWidget(self._btn_up)
        button_row.addWidget(self._btn_down)

        # Save to PSD
        self._btn_save_psd = QPushButton()
        self._btn_save_psd.setIcon(icon("actions", "device-floppy"))
        btn.setIconSize(QSize(20, 20))
        self._btn_save_psd.setToolTip(tr("Save visibility and expand state to PSD"))
        self._btn_save_psd.clicked.connect(self._save_to_psd)
        button_row.addWidget(self._btn_save_psd)

        layout.addLayout(button_row)

        # --- Tree view ---
        self._model = LayerTreeModel()
        self._tree = QTreeView()
        self._tree.setModel(self._model)
        self._tree.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._tree.setHeaderHidden(True)
        self._tree.setExpandsOnDoubleClick(True)
        self._tree.setDragDropMode(QTreeView.DragDropMode.InternalMove)
        self._tree.setDefaultDropAction(Qt.DropAction.MoveAction)
        self._tree.setAnimated(True)

        # Uniform row heights so every row is the same.
        self._tree.setUniformRowHeights(True)

        # Stretch columns
        header = self._tree.header()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header.resizeSection(1, 40)

        # Custom delegate for the visibility checkbox.
        self._vis_delegate = _VisibilityDelegate(self._tree)
        self._vis_delegate.visibility_changed.connect(self._on_visibility_toggled)
        self._tree.setItemDelegateForColumn(1, self._vis_delegate)

        # Keep model open_folder in sync with tree view expand/collapse.
        self._tree.expanded.connect(self._on_item_expanded)
        self._tree.collapsed.connect(self._on_item_collapsed)

        # Persistent editors: keep the checkbox widgets always visible.
        self._model.modelReset.connect(self._on_model_reset)

        layout.addWidget(self._tree, stretch=1)

        # Apply initial icon size.
        self._apply_icon_size()

    def _retranslate_ui(self):
        """Re-translate button tooltips after a language change."""
        self._btn_up.setToolTip(tr("Move up"))
        self._btn_down.setToolTip(tr("Move down"))

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_document(self, doc: Optional[PsdDocument]):
        self._doc = doc
        self._model.set_document(doc)
        self._expand_from_psd()
        self._open_persistent_editors()
        self._update_vis_all_button()

    # ------------------------------------------------------------------
    # Visibility toggled (from delegate)
    # ------------------------------------------------------------------

    def _expand_from_psd(self):
        """Expand groups based on their PSD open_folder state, collapsing
        the rest.  Called on initial document load."""
        if self._doc is None:
            return
        self._loading = True
        self._tree.collapseAll()
        self._expand_recursive(QModelIndex())
        self._loading = False

    def _expand_recursive(self, parent: QModelIndex):
        """Recursively expand groups whose open_folder is True."""
        model = self._model
        for row in range(model.rowCount(parent)):
            idx = model.index(row, 0, parent)
            wrapper = idx.internalPointer()
            if wrapper and isinstance(wrapper.item, LayerGroup):
                if wrapper.item.open_folder:
                    self._tree.expand(idx)
                    self._expand_recursive(idx)

    def _on_visibility_toggled(self):
        """Called when a checkbox is toggled in the delegate."""
        if self._doc is not None:
            size = (self._thumb_size, self._thumb_size)
            self._model.refresh_thumbnails_for_size(size)
            self._refresh_tree_decorations()
        self.layer_visibility_changed.emit()
        self.thumbnail_changed.emit()
        self._update_vis_all_button()

    def _set_size(self, px: int):
        """Switch to a new thumbnail/row size."""
        if px == self._thumb_size:
            return
        self._thumb_size = px
        self._model._thumb_size = px
        self._apply_icon_size()

        # Invalidate cached thumbnails.
        for doc_items in [self._doc] if self._doc else []:
            doc_items.invalidate_thumbnail()
        if self._doc is not None:
            self._model.invalidate_all_thumbnails()
            size = (px, px)
            self._model.refresh_thumbnails_for_size(size)
        self._refresh_tree_decorations()

        # Update button checked state.
        label = self._SIZE_LABELS.get(px, str(px))
        for btn in self._size_buttons:
            btn.setChecked(btn.text() == label)

    def _apply_icon_size(self):
        """Set the tree view's icon size and row height from current thumb size."""
        px = self._thumb_size
        self._tree.setIconSize(QSize(px, px))
        # Use a dynamic property so the central stylesheet can target the
        # correct row height via QTreeView[thumbSize="s"|"m"|"l"]::item.
        size_label = self._SIZE_LABELS.get(px, "m").lower()
        self._tree.setProperty("thumbSize", size_label)
        self._tree.style().unpolish(self._tree)
        self._tree.style().polish(self._tree)
        self._tree.doItemsLayout()

    def _move_selected(self, direction: int):
        """Move the selected layer/group up (+1) or down (-1) in its parent."""
        indexes = self._tree.selectedIndexes()
        if not indexes:
            return
        idx = indexes[0]
        # Remember the item name so we can re-select after model reset.
        name = idx.data(Qt.ItemDataRole.DisplayRole)
        if self._model.move_item(idx, direction):
            # Restore selection.
            self._select_by_name(name)
            self.layer_order_changed.emit()
            self.layer_visibility_changed.emit()
            self.thumbnail_changed.emit()

    def _select_by_name(self, name: str):
        """Find a top-level item by display name and select it."""
        model = self._model
        for row in range(model.rowCount()):
            idx = model.index(row, 0)
            if idx.data(Qt.ItemDataRole.DisplayRole) == name:
                self._tree.setCurrentIndex(idx)
                return

    def _save_to_psd(self):
        """Write current visibility and expand state back to the PSD file."""
        if self._doc is None:
            return

        reply = QMessageBox.question(
            self,
            tr("Save to PSD"),
            tr("This will modify the original PSD file. Continue?"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        # Collect current visibility/expand state so the worker thread can
        # apply it to a freshly-opened PSD without touching the model.
        layers_visible = []
        groups_open = {}

        def _collect_state(items, prefix=""):
            for item in items:
                path = f"{prefix}/{item.name}" if prefix else item.name
                layers_visible.append((path, item.visible))
                if isinstance(item, LayerGroup):
                    groups_open[path] = item.open_folder
                    _collect_state(item.children, path)

        _collect_state(self._doc.layer_tree)

        from PySide6.QtCore import QThread

        self._save_thread = QThread(self)
        self._save_worker = _PsdSaveWorker(self._doc.path, layers_visible, groups_open)
        self._save_worker.moveToThread(self._save_thread)
        self._save_thread.started.connect(self._save_worker.run)
        self._save_worker.finished.connect(self._on_save_done)
        self._save_worker.error.connect(self._on_save_error)
        self._save_worker.finished.connect(self._save_thread.quit)
        self._save_worker.error.connect(self._save_thread.quit)
        self._save_thread.finished.connect(self._save_thread.deleteLater)
        self._save_thread.finished.connect(self._save_worker.deleteLater)
        self._save_thread.start()

        self._btn_save_psd.setEnabled(False)
        from PySide6.QtWidgets import QProgressDialog

        self._progress = QProgressDialog(tr("Saving PSD..."), "", 0, 0, self)
        self._progress.setWindowTitle(tr("Save to PSD"))
        self._progress.setCancelButton(None)
        self._progress.setWindowModality(Qt.WindowModal)
        self._progress.show()

    def _on_save_done(self):
        self._progress.close()
        self._btn_save_psd.setEnabled(True)
        QMessageBox.information(self, tr("Save to PSD"), tr("Saved successfully."))

    def _on_save_error(self, msg: str):
        self._progress.close()
        self._btn_save_psd.setEnabled(True)
        QMessageBox.warning(self, tr("Save to PSD"), tr("Failed to save: ") + msg)

    def _apply_state_to_psd(self, psd_layer, our_item):
        psd_layer.visible = our_item.visible
        if hasattr(our_item, "children") and hasattr(psd_layer, "open_folder"):
            psd_layer.open_folder = our_item.open_folder
            for psd_child, our_child in zip(psd_layer, our_item.children):
                self._apply_state_to_psd(psd_child, our_child)

    # ------------------------------------------------------------------
    # Tree decoration refresh
    # ------------------------------------------------------------------

    def _refresh_tree_decorations(self):
        """Force the tree to repaint all DecorationRole and CheckStateRole
        cells without resetting expand state."""
        top_left = self._model.index(0, 0)
        bottom_right = self._model.index(self._model.rowCount() - 1, 1)
        self._model.dataChanged.emit(
            top_left,
            bottom_right,
            [Qt.ItemDataRole.DecorationRole, Qt.ItemDataRole.CheckStateRole],
        )

    # ------------------------------------------------------------------
    # Persistent editors for visibility checkboxes
    # ------------------------------------------------------------------

    def _on_item_expanded(self, index: QModelIndex):
        """Sync model open_folder when user expands a group."""
        wrapper = index.internalPointer()
        if (
            wrapper
            and isinstance(wrapper.item, LayerGroup)
            and not getattr(self, "_loading", False)
        ):
            wrapper.item.open_folder = True

    def _on_item_collapsed(self, index: QModelIndex):
        """Sync model open_folder when user collapses a group."""
        wrapper = index.internalPointer()
        if (
            wrapper
            and isinstance(wrapper.item, LayerGroup)
            and not getattr(self, "_loading", False)
        ):
            wrapper.item.open_folder = False

    def _expand_all(self):
        self._tree.expandAll()
        self._sync_all_open_folders(True)

    def _collapse_all(self):
        self._tree.collapseAll()
        self._sync_all_open_folders(False)

    def _sync_all_open_folders(self, value: bool):
        """Recursively set open_folder on all groups to *value*."""
        self._sync_open_recursive(QModelIndex(), value)

    def _sync_open_recursive(self, parent: QModelIndex, value: bool):
        model = self._model
        for row in range(model.rowCount(parent)):
            idx = model.index(row, 0, parent)
            wrapper = idx.internalPointer()
            if wrapper and isinstance(wrapper.item, LayerGroup):
                wrapper.item.open_folder = value
                self._sync_open_recursive(idx, value)

    def _on_vis_all_clicked(self):
        """Eye button: toggle between all-visible and all-hidden."""
        if self._doc is None:
            return
        visible_count, total = self._count_visible(self._doc.layer_tree)
        target = visible_count < total  # not all visible => show all
        self._set_all_visibility(self._doc.layer_tree, target)
        self._update_vis_all_button()
        self._on_visibility_toggled()
        self._reopen_persistent_editors()

    def _count_visible(self, items):
        """Recursively count (visible, total) items."""
        vis = total = 0
        for item in items:
            total += 1
            if item.visible:
                vis += 1
            if isinstance(item, LayerGroup):
                cv, ct = self._count_visible(item.children)
                vis += cv
                total += ct
        return vis, total

    def _update_vis_all_button(self):
        """Update eye icon to reflect current visibility."""
        if self._doc is None or not self._doc.layer_tree:
            self._btn_vis_all.setIcon(icon("status", "eye-off"))
            return
        visible_count, total = self._count_visible(self._doc.layer_tree)
        if visible_count == total:
            icon_name = "eye"
        elif visible_count == 0:
            icon_name = "eye-off"
        else:
            icon_name = "eye-dotted"
        self._btn_vis_all.setIcon(icon("status", icon_name))

    def _set_all_visibility(self, items: list, visible: bool):
        """Recursively set visibility on all items."""
        for item in items:
            item.visible = visible
            item.invalidate_thumbnail()
            if isinstance(item, LayerGroup):
                self._set_all_visibility(item.children, visible)
        if self._doc:
            self._doc.invalidate_thumbnail()

    def _on_model_reset(self):
        self._expand_from_psd()
        self._open_persistent_editors()
        self.layer_order_changed.emit()
        self.thumbnail_changed.emit()

    def _open_persistent_editors(self):
        """Open persistent editor on column 1 for every visible row."""
        self._open_editors_recursive(QModelIndex())

    def _open_editors_recursive(self, parent: QModelIndex):
        model = self._model
        for row in range(model.rowCount(parent)):
            idx = model.index(row, 1, parent)
            if idx.isValid():
                self._tree.openPersistentEditor(idx)
            child_idx = model.index(row, 0, parent)
            if model.hasChildren(child_idx):
                self._open_editors_recursive(child_idx)

    def _reopen_persistent_editors(self):
        """Close and reopen all persistent editors to refresh eye icons."""
        self._close_editors_recursive(QModelIndex())
        self._open_persistent_editors()

    def _close_editors_recursive(self, parent: QModelIndex):
        model = self._model
        for row in range(model.rowCount(parent)):
            idx = model.index(row, 1, parent)
            if idx.isValid():
                self._tree.closePersistentEditor(idx)
            child_idx = model.index(row, 0, parent)
            if model.hasChildren(child_idx):
                self._close_editors_recursive(child_idx)


class _PsdSaveWorker(QObject):
    """Runs psd.save() in a background thread without blocking the UI."""

    finished = Signal()
    error = Signal(str)

    def __init__(
        self,
        path: Path,
        layers_visible: list[tuple[str, bool]],
        groups_open: dict[str, bool],
    ):
        super().__init__()
        self._path = path
        self._layers_visible = layers_visible
        self._groups_open = groups_open

    def run(self):
        try:
            from psd_tools import PSDImage

            psd = PSDImage.open(self._path)
            visible_map = {name: vis for name, vis in self._layers_visible}
            open_map = self._groups_open

            def _apply(psd_layers, prefix):
                for psd_layer in psd_layers:
                    layer_path = (
                        f"{prefix}/{psd_layer.name}" if prefix else psd_layer.name
                    )
                    if layer_path in visible_map:
                        psd_layer.visible = visible_map[layer_path]
                    if layer_path in open_map:
                        try:
                            psd_layer.open_folder = open_map[layer_path]
                        except AttributeError, ValueError:
                            pass
                    if hasattr(psd_layer, "_layers"):
                        _apply(psd_layer, layer_path)

            _apply(psd, "")
            # Skip expensive preview-image recomposite; layer data is still
            # written correctly and visibility/expand state is what matters.
            psd._updated = False
            tmp = self._path.with_suffix(".psd.tmp")
            psd.save(tmp)
            tmp.replace(self._path)
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))
            import traceback

            traceback.print_exc()
