"""
Material Design 3 Design Tokens for PySide6.

Copy this file into your project. Import tokens by name.
Never hardcode these values in widget code; always reference tokens directly.
"""

import sys

# ==============================================================================
# Spacing Tokens (dp)
# ==============================================================================
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
# Elevation Tokens
# ==============================================================================
ELEVATION_0 = 0  # flat
ELEVATION_1 = 1  # border only
ELEVATION_2 = 2  # soft shadow (cards)
ELEVATION_3 = 3  # dialog shadow

# ==============================================================================
# Light Theme Colors
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
# Dark Theme Colors
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
# Typography Tokens
# ==============================================================================
_FONT_MAP = {"win32": "Segoe UI", "darwin": "SF Pro Display"}
FONT_FAMILY = _FONT_MAP.get(sys.platform, "Noto Sans")

TYPOGRAPHY = {
    "display_large": {"size": 57, "weight": 400, "line_height": 64},
    "display_medium": {"size": 45, "weight": 400, "line_height": 52},
    "display_small": {"size": 36, "weight": 400, "line_height": 44},
    "headline_large": {"size": 32, "weight": 400, "line_height": 40},
    "headline_medium": {"size": 28, "weight": 400, "line_height": 36},
    "headline_small": {"size": 24, "weight": 400, "line_height": 32},
    "title_large": {"size": 22, "weight": 500, "line_height": 28},
    "title_medium": {"size": 16, "weight": 500, "line_height": 24},
    "title_small": {"size": 14, "weight": 500, "line_height": 20},
    "body_large": {"size": 16, "weight": 400, "line_height": 24},
    "body_medium": {"size": 14, "weight": 400, "line_height": 20},
    "body_small": {"size": 12, "weight": 400, "line_height": 16},
    "label_large": {"size": 14, "weight": 500, "line_height": 20},
    "label_medium": {"size": 12, "weight": 500, "line_height": 16},
    "label_small": {"size": 11, "weight": 500, "line_height": 16},
}
