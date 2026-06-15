"""
Data models for PSD documents and their layer trees.

These are pure data containers — no GUI logic lives here.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from PIL import Image


@dataclass
class LayerNode:
    """A single raster layer extracted from a PSD file.

    Attributes:
        name:         Human-readable layer name from the PSD.
        image:        The pre-extracted PIL image for this layer (RGBA).
        offset:       (x, y) position within the document canvas.
        visible:      Current visibility state (can be toggled by the user).
        opacity:      Layer opacity 0.0–1.0 as stored in the PSD.
        blend_mode:   Blend mode identifier string (e.g. "normal").
        original_index: Index in the original PSD layer order, used for
                        stable identification when layers are reordered.
    """

    name: str
    image: Image.Image
    offset: tuple[int, int]
    visible: bool = True
    opacity: float = 1.0
    blend_mode: str = "normal"
    original_index: int = 0

    # Thumbnail cache — lazily populated by the renderer.
    thumbnail: Optional[Image.Image] = field(default=None, repr=False)

    def invalidate_thumbnail(self) -> None:
        """Clear the cached thumbnail so it is regenerated on next access."""
        self.thumbnail = None


@dataclass
class LayerGroup:
    """A folder / group that contains layers or other groups.

    Groups in PSD files have their own visibility and opacity, and they
    define the hierarchical structure visible in Photoshop's Layers panel.

    Attributes:
        name:           Group name from the PSD.
        children:       Ordered list of children (LayerNode or LayerGroup).
        visible:        Current visibility state.
        opacity:        Group opacity 0.0–1.0.
        original_index: Index in the original PSD layer order.
    """

    name: str
    children: list[LayerNode | LayerGroup] = field(default_factory=list)
    visible: bool = True
    opacity: float = 1.0
    original_index: int = 0

    # Thumbnail cache — lazily populated by the renderer.
    thumbnail: Optional[Image.Image] = field(default=None, repr=False)

    def invalidate_thumbnail(self) -> None:
        """Clear cached thumbnail for this group (does not recurse into children)."""
        self.thumbnail = None


# A tree item is either a leaf layer or a group container.
TreeItem = LayerNode | LayerGroup


@dataclass
class PsdDocument:
    """In-memory representation of a loaded PSD file.

    The layer tree mirrors the PSD structure but is fully independent of
    the original file — all mutations (visibility, order) happen here
    without touching the source PSD.

    Attributes:
        path:       Filesystem path to the source PSD.
        name:       Display name (filename without extension).
        width:      Document width in pixels.
        height:     Document height in pixels.
        layer_tree: Top-level list of TreeItems in bottom-to-top order
                    (index 0 is the bottom-most layer/group).
    """

    path: Path
    name: str
    width: int
    height: int
    layer_tree: list[TreeItem] = field(default_factory=list)

    # Thumbnail cache for the file list panel.
    thumbnail: Optional[Image.Image] = field(default=None, repr=False)

    def invalidate_thumbnail(self) -> None:
        """Clear cached thumbnail for the document (does not recurse into tree)."""
        self.thumbnail = None
