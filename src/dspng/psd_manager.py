"""
PSD file loading and layer-tree extraction.

Responsibilities:
  - Open a PSD file with psd-tools.
  - Recursively walk the PSD layer hierarchy and build our own
    LayerNode / LayerGroup tree that is independent of the source file.
  - Provide a list of all loaded PsdDocuments for the application state.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from psd_tools import PSDImage

from .models import LayerGroup, LayerNode, PsdDocument, TreeItem


def _extract_layer(psd_layer) -> Optional[LayerNode]:
    """Convert a single PSD layer to a LayerNode, or None if it has no pixels."""
    # psd-tools exposes a topil() that composites the layer's own content
    # (respecting its mask and blending info).  We want the raw pixels so
    # that *we* control the compositing order.
    pil_image = psd_layer.topil()
    if pil_image is None:
        return None

    # Ensure RGBA so downstream compositing is consistent.
    pil_image = pil_image.convert("RGBA")

    return LayerNode(
        name=psd_layer.name or "<unnamed>",
        image=pil_image,
        offset=(psd_layer.offset or (0, 0)),
        visible=psd_layer.visible if psd_layer.visible is not None else True,
        opacity=(psd_layer.opacity or 255) / 255.0,
        blend_mode=str(psd_layer.blend_mode or "normal").lower(),
        original_index=0,  # Will be set by the caller
    )


def _extract_group(psd_group) -> LayerGroup:
    """Recursively convert a PSD group (folder) to a LayerGroup."""
    children: list[TreeItem] = []

    # psd-tools iterates children bottom-to-top (index 0 = bottommost).
    # We preserve this order so compositing is a simple left-to-right walk.
    for i, child in enumerate(psd_group):
        if child.is_group():
            group = _extract_group(child)
            group.original_index = i
            children.append(group)
        else:
            node = _extract_layer(child)
            if node is not None:
                node.original_index = i
                children.append(node)

    return LayerGroup(
        name=psd_group.name or "<unnamed group>",
        children=children,
        visible=psd_group.visible if psd_group.visible is not None else True,
        opacity=(psd_group.opacity or 255) / 255.0,
        original_index=0,
        open_folder=getattr(psd_group, "open_folder", True),
    )


def load_psd(path: Path) -> PsdDocument:
    """Load a PSD file and return an independent in-memory document.

    The returned document owns all pixel data and can be freely mutated
    without affecting the source file on disk.
    """
    psd = PSDImage.open(path)

    # psd-tools iterates bottom-to-top; index 0 is already the bottommost
    # layer, which is exactly the paint order we need.
    layer_tree: list[TreeItem] = []
    for i, child in enumerate(psd):
        if child.is_group():
            group = _extract_group(child)
            group.original_index = i
            layer_tree.append(group)
        else:
            node = _extract_layer(child)
            if node is not None:
                node.original_index = i
                layer_tree.append(node)

    return PsdDocument(
        path=path,
        name=path.stem,
        width=psd.width,
        height=psd.height,
        layer_tree=layer_tree,
        _psd=psd,
    )


class DocumentStore:
    """Application-level container for all loaded documents.

    Keeps track of which document is currently selected and provides
    convenience methods for adding / removing documents.
    """

    def __init__(self) -> None:
        self.documents: list[PsdDocument] = []
        self.selected_index: Optional[int] = None

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    @property
    def selected_document(self) -> Optional[PsdDocument]:
        if self.selected_index is not None and 0 <= self.selected_index < len(
            self.documents
        ):
            return self.documents[self.selected_index]
        return None

    def add_document(self, path: Path) -> PsdDocument:
        """Load and add a PSD, selecting it automatically."""
        doc = load_psd(path)
        if not doc.display_name:
            doc.display_name = doc.name
        self.documents.append(doc)
        self.selected_index = len(self.documents) - 1
        return doc

    def remove_document(self, index: int) -> None:
        """Remove a document by index, adjusting selection."""
        if 0 <= index < len(self.documents):
            self.documents.pop(index)
            if not self.documents:
                self.selected_index = None
            elif self.selected_index is not None:
                if self.selected_index >= len(self.documents):
                    self.selected_index = len(self.documents) - 1

    def select(self, index: int) -> None:
        if 0 <= index < len(self.documents):
            self.selected_index = index
