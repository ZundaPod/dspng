"""
Dynamic QSS stylesheet generator.

Accepts a Theme object and produces a complete Qt stylesheet string.
"""

from __future__ import annotations

from .themes import Theme


def generate_stylesheet(t: Theme) -> str:
    """Return a full QSS string for the given theme."""

    return f"""
/* ---- Global ---- */
QMainWindow, QWidget {{
    background-color: {t.bg_primary};
    color: {t.fg_primary};
    font-size: 11px;
    font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif;
}}

/* ---- Frames / panels ---- */
QFrame[frameShape="6"] {{
    background-color: {t.bg_secondary};
    border: 1px solid {t.border};
    border-radius: 2px;
}}

/* ---- Panel title labels ---- */
QLabel#panelTitle {{
    background-color: {t.bg_primary};
    color: {t.fg_secondary};
    font-size: 10px;
    font-weight: bold;
    letter-spacing: 1px;
    padding: 3px 6px;
    border-bottom: 1px solid {t.border};
}}

/* ---- Push buttons ---- */
QPushButton {{
    background-color: transparent;
    color: {t.fg_primary};
    border: 1px solid transparent;
    border-radius: 2px;
    padding: 3px 8px;
    min-height: 20px;
}}
QPushButton:hover {{
    background-color: {t.bg_tertiary};
    border-color: {t.border};
}}
QPushButton:pressed {{
    background-color: {t.border};
}}
QPushButton:checked {{
    background-color: {t.accent};
    color: {t.indicator};
    border-color: {t.accent};
}}

/* ---- Tree / List views ---- */
QTreeView, QListView {{
    background-color: {t.bg_secondary};
    alternate-background-color: {t.bg_primary};
    border: 1px solid {t.border};
    outline: none;
    font-size: 11px;
}}
QTreeView::item, QListView::item {{
    padding: 2px 4px;
    border: none;
}}
QTreeView::item:selected, QListView::item:selected {{
    background-color: {t.accent};
    color: {t.indicator};
}}
QTreeView::item:hover, QListView::item:hover {{
    background-color: {t.bg_tertiary};
}}

/* ---- Header ---- */
QHeaderView::section {{
    background-color: {t.bg_primary};
    color: {t.fg_secondary};
    border: none;
    border-right: 1px solid {t.border};
    padding: 2px 4px;
    font-size: 10px;
}}

/* ---- Scroll bars ---- */
QScrollBar:vertical {{
    background: transparent;
    width: 8px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: {t.bg_tertiary};
    border-radius: 4px;
    min-height: 20px;
}}
QScrollBar::handle:vertical:hover {{
    background: {t.border};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
QScrollBar:horizontal {{
    background: transparent;
    height: 8px;
    margin: 0;
}}
QScrollBar::handle:horizontal {{
    background: {t.bg_tertiary};
    border-radius: 4px;
    min-width: 20px;
}}
QScrollBar::handle:horizontal:hover {{
    background: {t.border};
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0;
}}

/* ---- Checkboxes ---- */
QCheckBox {{
    spacing: 4px;
}}
QCheckBox::indicator {{
    width: 14px;
    height: 14px;
    border: 1px solid {t.border};
    border-radius: 2px;
    background-color: {t.bg_secondary};
}}
QCheckBox::indicator:checked {{
    background-color: {t.accent};
    border-color: {t.accent};
}}
QCheckBox::indicator:hover {{
    border-color: {t.accent};
}}

/* ---- Splitter ---- */
QSplitter::handle {{
    background-color: {t.border};
}}
QSplitter::handle:horizontal {{
    width: 2px;
}}
QSplitter::handle:vertical {{
    height: 2px;
}}

/* ---- Menu bar ---- */
QMenuBar {{
    background-color: {t.bg_primary};
    color: {t.fg_primary};
    border-bottom: 1px solid {t.border};
    padding: 2px;
}}
QMenuBar::item:selected {{
    background-color: {t.bg_tertiary};
}}
QMenu {{
    background-color: {t.bg_secondary};
    color: {t.fg_primary};
    border: 1px solid {t.border};
}}
QMenu::item:selected {{
    background-color: {t.accent};
    color: {t.indicator};
}}
QMenu::separator {{
    height: 1px;
    background: {t.border};
    margin: 4px 8px;
}}

/* ---- Slider ---- */
QSlider::groove:horizontal {{
    height: 4px;
    background: {t.bg_tertiary};
    border-radius: 2px;
}}
QSlider::handle:horizontal {{
    background: {t.fg_primary};
    width: 12px;
    height: 12px;
    margin: -4px 0;
    border-radius: 6px;
}}
QSlider::handle:horizontal:hover {{
    background: {t.accent};
}}

/* ---- Tooltip ---- */
QToolTip {{
    background-color: {t.bg_secondary};
    color: {t.fg_primary};
    border: 1px solid {t.border};
    padding: 4px;
    font-size: 11px;
}}

/* ---- Message box ---- */
QMessageBox {{
    background-color: {t.bg_secondary};
}}
QMessageBox QLabel {{
    color: {t.fg_primary};
}}
"""
