"""
Theme definitions based on the Lettepa color palette.

Lettepa is a restrained palette inspired by solarized and gruvbox,
using traditional Chinese color names.
https://github.com/lettepa/lettepa
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


# ==============================================================================
# Lettepa palette — raw colors
# ==============================================================================

# Background tones (gray, warm undertone)
ANLAN = "#101f30"  # darkest
QINGHUI = "#2b333e"
WAGUANHUI = "#47484c"
YUWEIHUI = "#5e616d"
XINGHUI = "#b2bbbe"
DALISHIHUI = "#c4cbcf"
ZHENZHUHUI = "#e4dfd7"
HANBAIYU = "#f8f4ed"  # lightest

# Accent colors
HAITANGHONG = "#f03752"  # red (bright)
FENGYEHONG = "#c21f30"  # red (dark)
SHILV = "#57c3c2"  # teal (bright)
MEIDIELV = "#12aa9c"  # teal (dark)
JIANSHILAN = "#66a9c9"  # blue (bright)
DIANQING = "#1661ab"  # blue (dark)
PUBULAN = "#51c4d3"  # cyan (bright)
CUILAN = "#1e9eb3"  # cyan (dark)
FENGXIANHUAHONG = "#ea7293"  # pink (bright)
ZIJINGHONG = "#ee2c79"  # magenta (bright)
MIHUANG = "#fbb957"  # orange (bright)
CANGHUANG = "#806332"  # orange (dark)


# ==============================================================================
# Theme mode & accent enums
# ==============================================================================


class ThemeMode(Enum):
    LIGHT = "light"
    DARK = "dark"
    SYSTEM = "system"


class Accent(Enum):
    BLUE = "blue"
    CYAN = "cyan"
    TEAL = "teal"
    RED = "red"
    ORANGE = "orange"
    MAGENTA = "magenta"


# ==============================================================================
# Theme dataclass
# ==============================================================================


@dataclass(frozen=True)
class Theme:
    """All semantic colors for the application UI."""

    # Backgrounds (darkest → lightest)
    bg_primary: str  # window / canvas surround
    bg_secondary: str  # panels, lists, trees
    bg_tertiary: str  # hover, selected rows, elevated surfaces

    # Foregrounds (brightest → dimmest)
    fg_primary: str  # main text
    fg_secondary: str  # dimmed / placeholder text

    # Accent
    accent: str  # selection, focus, active buttons
    accent_hover: str  # hover state for accent elements

    # Borders & separators
    border: str  # panel borders, splitter handles

    # Checkmark / indicator on accent background
    indicator: str  # usually white or very light


# ==============================================================================
# Accent pair definitions
# ==============================================================================

# Each accent has a (bright, dark) pair:
#   bright → used in dark mode (high contrast on dark bg)
#   dark   → used in light mode (high contrast on light bg)

_ACCENT_PAIRS: dict[Accent, tuple[str, str]] = {
    Accent.BLUE: (JIANSHILAN, DIANQING),
    Accent.CYAN: (PUBULAN, CUILAN),
    Accent.TEAL: (SHILV, MEIDIELV),
    Accent.RED: (HAITANGHONG, FENGYEHONG),
    Accent.ORANGE: (MIHUANG, CANGHUANG),
    Accent.MAGENTA: (ZIJINGHONG, FENGXIANHUAHONG),
}

# Hover is a slightly lighter version of the accent.
_ACCENT_HOVER: dict[Accent, tuple[str, str]] = {
    Accent.BLUE: ("#7bbad9", "#2a7bc4"),
    Accent.CYAN: ("#6dd4e3", "#2eb5c8"),
    Accent.TEAL: ("#6dd3d2", "#22bbae"),
    Accent.RED: ("#f54d67", "#d43347"),
    Accent.ORANGE: ("#fcc970", "#967740"),
    Accent.MAGENTA: ("#f24d94", "#f589a8"),
}


# ==============================================================================
# Theme constructors
# ==============================================================================


def make_dark(accent: Accent = Accent.BLUE) -> Theme:
    """Create a dark theme with the given accent."""
    acc, _ = _ACCENT_PAIRS[accent]
    acc_h, _ = _ACCENT_HOVER[accent]
    return Theme(
        bg_primary=ANLAN,
        bg_secondary=QINGHUI,
        bg_tertiary=WAGUANHUI,
        fg_primary=XINGHUI,
        fg_secondary=YUWEIHUI,
        accent=acc,
        accent_hover=acc_h,
        border=WAGUANHUI,
        indicator="#ffffff",
    )


def make_light(accent: Accent = Accent.BLUE) -> Theme:
    """Create a light theme with the given accent."""
    _, acc = _ACCENT_PAIRS[accent]
    _, acc_h = _ACCENT_HOVER[accent]
    return Theme(
        bg_primary=HANBAIYU,
        bg_secondary=ZHENZHUHUI,
        bg_tertiary=DALISHIHUI,
        fg_primary=QINGHUI,
        fg_secondary=YUWEIHUI,
        accent=acc,
        accent_hover=acc_h,
        border=DALISHIHUI,
        indicator="#ffffff",
    )


# ==============================================================================
# Label helpers (for UI display)
# ==============================================================================

ACCENT_LABELS: dict[Accent, str] = {
    Accent.BLUE: "Blue",
    Accent.CYAN: "Cyan",
    Accent.TEAL: "Teal",
    Accent.RED: "Red",
    Accent.ORANGE: "Orange",
    Accent.MAGENTA: "Magenta",
}

MODE_LABELS: dict[ThemeMode, str] = {
    ThemeMode.LIGHT: "Light",
    ThemeMode.DARK: "Dark",
    ThemeMode.SYSTEM: "System",
}
