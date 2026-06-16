"""
Icon manager — loads Tabler SVG icons and returns QIcon objects.

Qt's SVG renderer does not support ``currentColor``, so we replace it
with the theme's foreground colour before rendering.  The manager
re-renders all cached icons when the theme changes.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

_ICONS_DIR = Path(__file__).resolve().parent.parent.parent.parent / "icons"

_DEFAULT_COLOR = "#FFFFFF"
_DEFAULT_SIZE = 20


class IconManager:
    """Singleton that provides colour-aware QIcon objects."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._cache: dict[str, QIcon] = {}
            cls._instance._color = _DEFAULT_COLOR
            cls._instance._size = _DEFAULT_SIZE
        return cls._instance

    def icon(self, category: str, name: str) -> QIcon:
        key = f"{category}/{name}"
        if key not in self._cache:
            self._cache[key] = self._build_icon(key)
        return self._cache[key]

    def set_color(self, color: str):
        """Update the foreground colour and invalidate all cached icons."""
        if color != self._color:
            self._color = color
            self._cache.clear()

    def set_size(self, size: int):
        if size != self._size:
            self._size = size
            self._cache.clear()

    def _build_icon(self, key: str) -> QIcon:
        path = _ICONS_DIR / f"{key}.svg"
        if not path.exists():
            return QIcon()
        svg_text = path.read_text(encoding="utf-8")
        # Qt SVG does not understand currentColor — replace it.
        svg_text = svg_text.replace('"currentColor"', f'"{self._color}"')
        renderer = QSvgRenderer(svg_text.encode("utf-8"))
        pixmap = QPixmap(self._size, self._size)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()
        icon = QIcon(pixmap)
        # Also add a 2x version for HiDPI.
        pixmap2 = QPixmap(self._size * 2, self._size * 2)
        pixmap2.fill(Qt.GlobalColor.transparent)
        painter2 = QPainter(pixmap2)
        renderer.render(painter2)
        painter2.end()
        icon.addPixmap(pixmap2)
        return icon


def icon(category: str, name: str) -> QIcon:
    return IconManager().icon(category, name)
