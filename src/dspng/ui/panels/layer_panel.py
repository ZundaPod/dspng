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

from typing import Optional

from PySide6.QtCore import (
    QAbstractItemModel,
    QMimeData,
    QModelIndex,
    QSize,
    Qt,
    Signal,
)
from PySide6.QtGui import QColor, QImage, QPainter, QPixmap
from PySide6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QHeaderView,
    QStyledItemDelegate,
    QTreeView,
    QVBoxLayout,
    QWidget,
)

from ...models import LayerGroup, LayerNode, PsdDocument, TreeItem
from ...renderer import (
    DEFAULT_THUMB_SIZE,
    generate_group_thumbnail,
    generate_layer_thumbnail,
)


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

    Renders a centered QCheckBox.  Using a real widget delegate avoids
    the PySide6 quirk where ItemIsUserCheckable + setData(CheckStateRole)
    does not reliably update the visual state.
    """

    visibility_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

    def createEditor(self, parent, option, index):
        cb = QCheckBox(parent)
        cb.setAutoFillBackground(True)
        cb.setStyleSheet("QCheckBox { margin: 0px; padding: 0px; }")
        cb.toggled.connect(lambda checked, idx=index: self._on_toggled(idx, checked))
        return cb

    def setEditorData(self, editor: QCheckBox, index: QModelIndex):
        editor.blockSignals(True)
        state = index.data(Qt.ItemDataRole.CheckStateRole)
        editor.setChecked(state == Qt.CheckState.Checked)
        editor.blockSignals(False)

    def setModelData(self, editor, model, index):
        pass  # the toggled signal already wrote the value

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)

    def paint(self, painter, option, index):
        pass  # the persistent editor widget is always visible

    def _on_toggled(self, index: QModelIndex, checked: bool):
        model = index.model()
        if model is None:
            return
        new_state = Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked
        model.setData(index, new_state, Qt.ItemDataRole.CheckStateRole)
        self.visibility_changed.emit()


# ======================================================================
# Tree Model
# ======================================================================

class _TreeItemWrapper:
    """Wraps a TreeItem so the QTreeView model can point to a unique node."""

    def __init__(self, item: TreeItem, parent_wrapper: Optional[_TreeItemWrapper] = None):
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
        self._root = _TreeItemWrapper(
            LayerGroup(name="__root__", children=[])
        )

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
        from ...renderer import generate_group_thumbnail, generate_layer_thumbnail

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
        self._root = _TreeItemWrapper(
            LayerGroup(name="__root__", children=[])
        )
        if self._doc is None:
            return
        self._root.item = LayerGroup(
            name="__root__", children=self._doc.layer_tree
        )
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
            if isinstance(item, LayerNode):
                thumb = generate_layer_thumbnail(item)
            elif isinstance(item, LayerGroup):
                if self._doc is not None:
                    thumb = generate_group_thumbnail(item, self._doc)
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
            return Qt.ItemFlag.NoItemFlags
        base = (
            Qt.ItemFlag.ItemIsEnabled
            | Qt.ItemFlag.ItemIsSelectable
            | Qt.ItemFlag.ItemIsDragEnabled
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

        # Only same-parent moves are supported for now.
        if src_wrapper.parent_wrapper is not dest_wrapper:
            return False

        n = len(dest_wrapper.children_wrappers)

        # Convert view row to data-model index.
        # children_wrappers is reversed (top-to-bottom),
        # item.children is bottom-to-top.
        if row < 0 or row >= n:
            data_idx = n - 1  # append after display last = data first
        else:
            data_idx = n - 1 - row  # reverse mapping

        children: list = dest_wrapper.item.children
        old_data_idx = children.index(src_wrapper.item)

        # Adjust for removal shift.
        if old_data_idx < data_idx:
            data_idx -= 1

        children.pop(old_data_idx)
        children.insert(data_idx, src_wrapper.item)

        # Rebuild wrappers from the data model.
        self.beginResetModel()
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
    _SIZE_PRESETS = [20, 32, 48]
    _SIZE_LABELS = {20: "S", 32: "M", 48: "L"}

    def __init__(self, parent=None):
        super().__init__(parent)
        self._doc: Optional[PsdDocument] = None
        self._thumb_size = self._SIZE_PRESETS[0]  # default: S
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # --- Tree view ---
        self._model = LayerTreeModel()
        self._tree = QTreeView()
        self._tree.setModel(self._model)
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

        # Persistent editors: keep the checkbox widgets always visible.
        self._model.modelReset.connect(self._on_model_reset)
        self._model.layoutChanged.connect(self._on_layout_changed)

        layout.addWidget(self._tree, stretch=1)

        # --- Bottom row: size presets + up/down buttons ---
        from PySide6.QtWidgets import QPushButton

        bottom_row = QHBoxLayout()
        self._size_buttons: list[QPushButton] = []
        for px in self._SIZE_PRESETS:
            label = self._SIZE_LABELS.get(px, str(px))
            btn = QPushButton(label)
            btn.setFixedWidth(30)
            btn.setCheckable(True)
            if px == self._thumb_size:
                btn.setChecked(True)
            btn.clicked.connect(lambda checked, s=px: self._set_size(s))
            bottom_row.addWidget(btn)
            self._size_buttons.append(btn)

        bottom_row.addStretch()

        self._btn_up = QPushButton("↑ Up")
        self._btn_down = QPushButton("↓ Down")
        self._btn_up.clicked.connect(lambda: self._move_selected(1))
        self._btn_down.clicked.connect(lambda: self._move_selected(-1))
        bottom_row.addWidget(self._btn_up)
        bottom_row.addWidget(self._btn_down)
        layout.addLayout(bottom_row)

        # Apply initial icon size.
        self._apply_icon_size()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_document(self, doc: Optional[PsdDocument]):
        self._doc = doc
        self._model.set_document(doc)
        self._tree.expandAll()
        self._open_persistent_editors()

    # ------------------------------------------------------------------
    # Visibility toggled (from delegate)
    # ------------------------------------------------------------------

    def _on_visibility_toggled(self):
        """Called when a checkbox is toggled in the delegate."""
        if self._doc is not None:
            size = (self._thumb_size, self._thumb_size)
            self._model.refresh_thumbnails_for_size(size)
            self._refresh_tree_decorations()
        self.layer_visibility_changed.emit()
        self.thumbnail_changed.emit()

    def _set_size(self, px: int):
        """Switch to a new thumbnail/row size."""
        if px == self._thumb_size:
            return
        self._thumb_size = px
        self._apply_icon_size()

        # Invalidate cached thumbnails.
        for doc_items in ([self._doc] if self._doc else []):
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
        from PySide6.QtCore import QSize
        px = self._thumb_size
        self._tree.setIconSize(QSize(px, px))
        # Row height is controlled via stylesheet alongside iconSize.
        self._tree.setStyleSheet(
            f"QTreeView::item {{ height: {px}px; min-height: {px}px; padding: 1px; }}"
        )

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

    # ------------------------------------------------------------------
    # Tree decoration refresh
    # ------------------------------------------------------------------

    def _refresh_tree_decorations(self):
        """Force the tree to repaint all DecorationRole cells."""
        self._model.layoutChanged.emit()

    # ------------------------------------------------------------------
    # Persistent editors for visibility checkboxes
    # ------------------------------------------------------------------

    def _on_model_reset(self):
        self._tree.expandAll()
        self._open_persistent_editors()

    def _on_layout_changed(self, _1, _2):
        """Called after drag-and-drop reorder."""
        self._tree.expandAll()
        self._open_persistent_editors()
        self.layer_order_changed.emit()
        self.layer_visibility_changed.emit()
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
