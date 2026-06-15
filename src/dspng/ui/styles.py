"""
Global dark-theme stylesheet for dspng.

Inspired by Adobe Photoshop / Affinity Photo UI conventions:
  - Dark gray palette (#1e1e1e → #4d4d4d)
  - Subtle borders between panels
  - Compact, flat controls
  - Blue accent for selection (#2a6ad4)
"""

# ==============================================================================
# Color palette
# ==============================================================================

BG_DARKEST   = "#1e1e1e"  # window / canvas background
BG_DARK      = "#252525"  # panel background
BG_MID       = "#2d2d2d"  # tree / list background
BG_LIGHT     = "#3a3a3a"  # hover / selected row
BG_LIGHTER   = "#4d4d4d"  # pressed / active

BORDER       = "#3a3a3a"  # panel borders
BORDER_LIGHT = "#555555"  # splitter handle

TEXT         = "#cccccc"  # primary text
TEXT_DIM     = "#888888"  # secondary text
TEXT_BRIGHT  = "#ffffff"  # selected text

ACCENT       = "#2a6ad4"  # selection / focus
ACCENT_HOVER = "#3b7be5"

CHECKMARK    = "#ffffff"

# ==============================================================================
# Stylesheet
# ==============================================================================

STYLESHEET = f"""
/* ---- Global ---- */
QMainWindow, QWidget {{
    background-color: {BG_DARKEST};
    color: {TEXT};
    font-size: 11px;
    font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif;
}}

/* ---- Frames / panels ---- */
QFrame[frameShape="6"] /* StyledPanel */ {{
    background-color: {BG_DARK};
    border: 1px solid {BORDER};
    border-radius: 2px;
}}

/* ---- Panel title labels ---- */
QLabel#panelTitle {{
    background-color: {BG_DARKEST};
    color: {TEXT_DIM};
    font-size: 10px;
    font-weight: bold;
    text-transform: uppercase;
    letter-spacing: 1px;
    padding: 3px 6px;
    border-bottom: 1px solid {BORDER};
}}

/* ---- Push buttons ---- */
QPushButton {{
    background-color: transparent;
    color: {TEXT};
    border: 1px solid transparent;
    border-radius: 2px;
    padding: 3px 8px;
    min-height: 20px;
}}
QPushButton:hover {{
    background-color: {BG_LIGHT};
    border-color: {BORDER_LIGHT};
}}
QPushButton:pressed {{
    background-color: {BG_LIGHTER};
}}
QPushButton:checked {{
    background-color: {ACCENT};
    color: {TEXT_BRIGHT};
    border-color: {ACCENT};
}}

/* ---- Tree / List views ---- */
QTreeView, QListView {{
    background-color: {BG_MID};
    alternate-background-color: {BG_DARK};
    border: 1px solid {BORDER};
    outline: none;
    font-size: 11px;
}}
QTreeView::item, QListView::item {{
    padding: 2px 4px;
    border: none;
}}
QTreeView::item:selected, QListView::item:selected {{
    background-color: {ACCENT};
    color: {TEXT_BRIGHT};
}}
QTreeView::item:hover, QListView::item:hover {{
    background-color: {BG_LIGHT};
}}

/* ---- Header (hidden but keep styling) ---- */
QHeaderView::section {{
    background-color: {BG_DARKEST};
    color: {TEXT_DIM};
    border: none;
    border-right: 1px solid {BORDER};
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
    background: {BG_LIGHTER};
    border-radius: 4px;
    min-height: 20px;
}}
QScrollBar::handle:vertical:hover {{
    background: {BORDER_LIGHT};
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
    background: {BG_LIGHTER};
    border-radius: 4px;
    min-width: 20px;
}}
QScrollBar::handle:horizontal:hover {{
    background: {BORDER_LIGHT};
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
    border: 1px solid {BORDER_LIGHT};
    border-radius: 2px;
    background-color: {BG_MID};
}}
QCheckBox::indicator:checked {{
    background-color: {ACCENT};
    border-color: {ACCENT};
}}
QCheckBox::indicator:hover {{
    border-color: {ACCENT};
}}

/* ---- Splitter ---- */
QSplitter::handle {{
    background-color: {BORDER};
}}
QSplitter::handle:horizontal {{
    width: 2px;
}}
QSplitter::handle:vertical {{
    height: 2px;
}}

/* ---- Menu bar ---- */
QMenuBar {{
    background-color: {BG_DARKEST};
    color: {TEXT};
    border-bottom: 1px solid {BORDER};
    padding: 2px;
}}
QMenuBar::item:selected {{
    background-color: {BG_LIGHT};
}}
QMenu {{
    background-color: {BG_DARK};
    color: {TEXT};
    border: 1px solid {BORDER};
}}
QMenu::item:selected {{
    background-color: {ACCENT};
}}

/* ---- Slider ---- */
QSlider::groove:horizontal {{
    height: 4px;
    background: {BG_LIGHTER};
    border-radius: 2px;
}}
QSlider::handle:horizontal {{
    background: {TEXT};
    width: 12px;
    height: 12px;
    margin: -4px 0;
    border-radius: 6px;
}}
QSlider::handle:horizontal:hover {{
    background: {ACCENT};
}}

/* ---- Tooltip ---- */
QToolTip {{
    background-color: {BG_DARK};
    color: {TEXT};
    border: 1px solid {BORDER_LIGHT};
    padding: 4px;
    font-size: 11px;
}}

/* ---- Message box ---- */
QMessageBox {{
    background-color: {BG_DARK};
}}
QMessageBox QLabel {{
    color: {TEXT};
}}
"""
