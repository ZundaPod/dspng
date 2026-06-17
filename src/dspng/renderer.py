"""
Image compositing engine.

Responsibilities:
  - Composite a PsdDocument's visible layers into a single RGBA image.
  - Generate small thumbnails for the file list and layer panel.
  - Provide the composited image for display and PNG export.

Design:
  We cache each layer's PIL image when the PSD is loaded (done in
  psd_manager).  Compositing walks the layer tree in paint order and
  alpha-composites each visible layer onto a canvas.  This is O(n) in
  the number of *visible* layers per frame.

  For the MVP we only support the "normal" blend mode.  Other modes
  (multiply, screen, etc.) are treated as normal.
"""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

from PIL import Image

from .models import LayerGroup, LayerNode, PsdDocument, TreeItem

# Default thumbnail size; callers can override per call.
DEFAULT_THUMB_SIZE = (64, 64)


def _alpha_composite_onto(canvas: Image.Image, layer: LayerNode) -> None:
    """Composite a single layer onto *canvas* in place.

    Handles the layer's offset, opacity, and visibility.
    Only the "normal" blend mode is implemented; other modes fall back
    to normal.
    """
    if not layer.visible:
        return

    img = layer.image
    if img is None:
        return

    # Apply opacity by scaling the alpha channel.
    opacity = layer.opacity
    if opacity < 1.0:
        # Split into channels, scale alpha, recombine.
        r, g, b, a = img.split()
        a = a.point(lambda px: int(px * opacity))
        img = Image.merge("RGBA", (r, g, b, a))

    x, y = layer.offset
    canvas.alpha_composite(img, dest=(x, y))


def _collect_visible_layers(tree: list[TreeItem]) -> list[LayerNode]:
    """Flatten the layer tree, yielding only visible leaves in paint order."""
    result: list[LayerNode] = []
    for item in tree:
        if isinstance(item, LayerGroup):
            if item.visible:
                result.extend(_collect_visible_layers(item.children))
        elif isinstance(item, LayerNode):
            if item.visible:
                result.append(item)
    return result


def composite(doc: PsdDocument) -> Image.Image:
    """Render the full document composite from its current layer state.

    Returns an RGBA PIL image of size (doc.width, doc.height).
    """
    canvas = Image.new("RGBA", (doc.width, doc.height), (0, 0, 0, 0))
    for layer in _collect_visible_layers(doc.layer_tree):
        _alpha_composite_onto(canvas, layer)
    return canvas


def make_thumbnail(
    image: Image.Image, size: tuple[int, int] = DEFAULT_THUMB_SIZE
) -> Image.Image:
    """Create a square thumbnail of *image* at exactly *size*.

    The image is scaled to fill the square (aspect ratio is NOT preserved).
    Always creates a fresh copy — the caller is responsible for caching.
    """
    return image.resize(size, Image.Resampling.LANCZOS)


def generate_layer_thumbnail(
    layer: LayerNode, size: tuple[int, int] = DEFAULT_THUMB_SIZE
) -> Image.Image:
    """Generate (or return cached) thumbnail for a single layer.

    Regenerates automatically if the cached size does not match *size*.
    """
    if layer.thumbnail is not None and layer.thumbnail.size == size:
        return layer.thumbnail
    layer.thumbnail = make_thumbnail(layer.image, size)
    return layer.thumbnail


def generate_group_thumbnail(
    group: LayerGroup,
    doc: PsdDocument,
    size: tuple[int, int] = DEFAULT_THUMB_SIZE,
) -> Image.Image:
    """Generate a thumbnail for a group by compositing its children.

    Regenerates automatically if the cached size does not match *size*.
    """
    if group.thumbnail is not None and group.thumbnail.size == size:
        return group.thumbnail
    tmp_doc = PsdDocument(
        path=doc.path,
        name=doc.name,
        width=doc.width,
        height=doc.height,
        layer_tree=group.children,
    )
    full = composite(tmp_doc)
    group.thumbnail = make_thumbnail(full, size)
    return group.thumbnail


def generate_doc_thumbnail(
    doc: PsdDocument, size: tuple[int, int] = DEFAULT_THUMB_SIZE
) -> Image.Image:
    """Generate (or return cached) thumbnail for the file list.

    Regenerates automatically if the cached size does not match *size*.
    """
    if doc.thumbnail is not None and doc.thumbnail.size == size:
        return doc.thumbnail
    full = composite(doc)
    doc.thumbnail = make_thumbnail(full, size)
    return doc.thumbnail


def export_png(doc: PsdDocument, dest: Path) -> Path:
    """Composite and save the document as a PNG file.  Returns the path."""
    img = composite(doc)
    img.save(dest, "PNG")
    return dest


def composite_to_bytes(doc: PsdDocument) -> bytes:
    """Composite and return PNG-encoded bytes (useful for drag-and-drop)."""
    img = composite(doc)
    buf = BytesIO()
    img.save(buf, "PNG")
    return buf.getvalue()
