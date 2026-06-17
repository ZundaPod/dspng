"""
Material Design 3 Design Tokens for PySide6.

All spacing, radius, and colour values live here so widgets never hardcode
styling constants.  ThemeManager resolves these at stylesheet-compile time.
"""

from __future__ import annotations

import sys

# ==============================================================================
# Spacing Tokens (dp)
# ==============================================================================
SPACING_NONE = 0
SPACING_XS = 4
SPACING_SM = 8
SPACING_MD = 12
SPACING_LG = 16
SPACING_XL = 24
SPACING_2XL = 32

# ==============================================================================
# Radius Tokens (px)
# ==============================================================================
RADIUS_SM = 6
RADIUS_MD = 10
RADIUS_LG = 14

# ==============================================================================
# Light Theme Palette
# ==============================================================================
LIGHT = {
    "background": "#FFFFFF",
    "surface": "#F7F7F7",
    "surface_variant": "#E7E0EC",
    "primary": "#6750A4",
    "primary_container": "#EADDFF",
    "on_primary": "#FFFFFF",
    "secondary": "#625B71",
    "text_primary": "#1C1B1F",
    "text_secondary": "#49454F",
    "text_on_primary": "#FFFFFF",
    "border": "#E0E0E0",
    "outline": "#79747E",
    "error": "#B3261E",
}

# ==============================================================================
# Dark Theme Palette
# ==============================================================================
DARK = {
    "background": "#1C1B1F",
    "surface": "#2B2930",
    "surface_variant": "#49454F",
    "primary": "#D0BCFF",
    "primary_container": "#4F378B",
    "on_primary": "#381E72",
    "secondary": "#CCC2DC",
    "text_primary": "#E6E1E5",
    "text_secondary": "#CAC4D0",
    "text_on_primary": "#1C1B1F",
    "border": "#3C3A3F",
    "outline": "#938F99",
    "error": "#F2B8B5",
}

# ==============================================================================
# Typography
# ==============================================================================
_FONT_WIN = "Segoe UI"
_FONT_MAC = "SF Pro Display"
_FONT_LINUX = "Noto Sans"

if sys.platform == "win32":
    FONT_FAMILY = _FONT_WIN
elif sys.platform == "darwin":
    FONT_FAMILY = _FONT_MAC
else:
    FONT_FAMILY = _FONT_LINUX

DEFAULT_FONT_SIZE = "9pt"
