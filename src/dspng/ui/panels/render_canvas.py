"""
Render canvas — left area.

Displays the composited PSD image with:
  - Scroll-wheel zoom (centered on cursor).
  - Middle-button / Alt+left-button pan.
  - Left-button drag to export PNG to Premiere or the file system.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6.QtCore import QByteArray, QMimeData, QPointF, QRectF, Qt
from PySide6.QtGui import (
    QBrush,
    QColor,
    QDrag,
    QImage,
    QMouseEvent,
    QPainter,
    QPen,
    QPixmap,
    QWheelEvent,
)
from PySide6.QtWidgets import QGraphicsPixmapItem, QGraphicsScene, QGraphicsView, QWidget

from ...models import PsdDocument
from ...renderer import composite


class RenderCanvas(QGraphicsView):
    """Zoomable / pannable canvas that shows the composited PSD image."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)

        # --- Scene setup ---
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)

        self._pixmap_item: Optional[QGraphicsPixmapItem] = None
        self._doc: Optional[PsdDocument] = None

        # View settings
        self.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.SmoothPixmapTransform)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # Checkerboard background to indicate transparency.
        checker_brush = QBrush(QPixmap.fromImage(_checkerboard_image(16)))
        self.setBackgroundBrush(checker_brush)

        # Pan state
        self._panning = False
        self._pan_start = QPointF()

        # Drag-to-export state
        self._drag_origin = QPointF()
        self._drag_started = False
        self._DRAG_THRESHOLD = 5.0  # pixels before drag initiates

        # Zoom limits
        self._zoom_min = 0.05
        self._zoom_max = 40.0
        self._zoom = 1.0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_document(self, doc: Optional[PsdDocument]):
        """Display a new document (or None to clear).  Fits to view."""
        self._doc = doc
        self._rebuild_scene(fit=True)

    def refresh_composite(self):
        """Re-composite and re-display, keeping current zoom and pan."""
        self._rebuild_scene(fit=False)

    # ------------------------------------------------------------------
    # Scene management
    # ------------------------------------------------------------------

    def _rebuild_scene(self, fit: bool = True):
        self._scene.clear()
        self._pixmap_item = None

        if self._doc is None:
            return

        pil_img = composite(self._doc)
        qimg = _pil_to_qimage(pil_img)
        pixmap = QPixmap.fromImage(qimg)
        self._pixmap_item = self._scene.addPixmap(pixmap)
        self._scene.setSceneRect(QRectF(pixmap.rect()))

        if fit:
            self.fitInView(self._scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
            self._zoom = self.transform().m11()

    # ------------------------------------------------------------------
    # Zoom
    # ------------------------------------------------------------------

    def wheelEvent(self, event: QWheelEvent):
        """Zoom in/out with scroll wheel, centered on cursor."""
        factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
        new_zoom = self._zoom * factor
        if self._zoom_min <= new_zoom <= self._zoom_max:
            self.scale(factor, factor)
            self._zoom = new_zoom

    # ------------------------------------------------------------------
    # Pan (middle-click or Alt+left-click)
    # ------------------------------------------------------------------

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.MiddleButton or (
            event.button() == Qt.MouseButton.LeftButton
            and event.modifiers() & Qt.KeyboardModifier.AltModifier
        ):
            self._panning = True
            self._pan_start = event.position()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
            return

        # Left-click without modifiers → prepare for drag-to-export.
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_origin = event.position()
            self._drag_started = False
            event.accept()
            return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._panning:
            delta = event.position() - self._pan_start
            self._pan_start = event.position()
            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value() - int(delta.x())
            )
            self.verticalScrollBar().setValue(
                self.verticalScrollBar().value() - int(delta.y())
            )
            event.accept()
            return

        # Check if we should initiate a drag-to-export.
        if not self._drag_started and event.buttons() & Qt.MouseButton.LeftButton:
            delta = event.position() - self._drag_origin
            if delta.manhattanLength() > self._DRAG_THRESHOLD:
                self._drag_started = True
                self._start_drag(event)
                return

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if self._panning:
            self._panning = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
            event.accept()
            return
        self._drag_started = False
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        """Double-click: fit the entire image into the viewport."""
        if self._pixmap_item is not None:
            self.fitInView(self._scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
            self._zoom = self.transform().m11()
        event.accept()

    # ------------------------------------------------------------------
    # Drag-to-export
    # ------------------------------------------------------------------

    def _start_drag(self, event: QMouseEvent):
        """Initiate a drag that carries PNG data for Premiere / file manager."""
        if self._doc is None:
            return
        import tempfile
        from pathlib import Path

        from ...renderer import composite_to_bytes

        png_bytes = composite_to_bytes(self._doc)

        # Write to a temp file so Premiere / Explorer can receive a real path.
        tmp = tempfile.NamedTemporaryFile(
            suffix=".png", prefix="dspng_", delete=False
        )
        tmp.write(png_bytes)
        tmp.flush()
        tmp.close()
        tmp_path = Path(tmp.name)

        drag = QDrag(self)
        mime = QMimeData()
        mime.setData("image/png", QByteArray(png_bytes))
        mime.setUrls([tmp_path.as_uri()])

        drag.setMimeData(mime)

        # Use the thumbnail as the drag pixmap.
        thumb = self._doc.thumbnail
        if thumb is not None:
            qimg = _pil_to_qimage(thumb)
            drag.setPixmap(QPixmap.fromImage(qimg))

        # exec() blocks until the drop completes; clean up afterwards.
        drag.exec(Qt.DropAction.CopyAction)
        # Note: the temp file persists after the drag.  A production

        # implementation should schedule cleanup or use a cache directory.


# ======================================================================
# Helpers
# ======================================================================

def _pil_to_qimage(pil_img) -> QImage:
    """Convert a PIL RGBA image to QImage."""
    data = pil_img.tobytes("raw", "RGBA")
    return QImage(data, pil_img.width, pil_img.height, QImage.Format.Format_RGBA8888)


def _checkerboard_image(cell: int = 16, size: int = 64) -> QImage:
    """Create a small checkerboard pattern for the transparency background."""
    img = QImage(size, size, QImage.Format.Format_RGB32)
    c1 = QColor(204, 204, 204)
    c2 = QColor(255, 255, 255)
    for y in range(0, size, cell):
        for x in range(0, size, cell):
            color = c1 if ((x // cell) + (y // cell)) % 2 == 0 else c2
            for dy in range(cell):
                for dx in range(cell):
                    if x + dx < size and y + dy < size:
                        img.setPixelColor(x + dx, y + dy, color)
    return img
