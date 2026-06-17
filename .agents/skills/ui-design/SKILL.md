---
name: ui-design
description: Generates, validates, and auto-fixes PySide6 GUIs with production-grade layout patterns. Use when building settings dialogs, repairing broken layouts, or designing new PySide6 widget-based interfaces. All patterns are battle-tested against real-world desktop applications.
---

# PySide6 UI Design System

Generates and repairs PySide6 GUIs using layout patterns proven in production desktop applications.  Every output widget tree is layout-based, scroll-aware, properly sized, and free of absolute positioning.  No inline stylesheets, no hardcoded dimensions, no wasted space.

## Non-negotiable safety policy

1. Never fabricate citations or references.
2. If key info is missing, ask up to 5 targeted questions, then proceed.
3. Never emit `move()`, `setGeometry()`, or ad-hoc `setFixedSize()` — use layout managers.  The only exception: `setFixedSize()` on truly fixed-content widgets (colour swatches, icons).
4. Never emit a `QWidget` with children but no layout — inject one if missing.
5. Never emit inline `setStyleSheet()` calls on individual widgets — all styling is compiled centrally.  The only exception: runtime-determined colour values where no Qt CSS mechanism exists (see Rule 7 exceptions).
6. Never emit hardcoded margin/spacing integer literals — use a spacing token system.
7. Always run the seven-rule lint checklist before delivering output.

## Mandatory intake questions

1. **What should the UI do?**
2. **New or repair?**  New from scratch, or fixing existing code?  If existing, provide file paths.
3. **Target platforms?**  Default: all three (Windows, macOS, Linux).
4. **Light/dark/system theme?**  Default: runtime switching between all three.
5. **PySide6 version?**  Default: PySide6 ≥ 6.5.

## The Seven Layout Rules

### Rule 1 — No Absolute Positioning `[ERROR]`

**Forbidden**: `move()`, `setGeometry()`, ad-hoc `setFixedSize()`.
**Exception**: `setFixedSize()` on truly fixed-content widgets (colour swatches, icons).
**Fix**: Replace with a layout manager.

### Rule 2 — Mandatory Layout `[ERROR]`

Every `QWidget` with children must call `setLayout()`.
**Fix**: Inject `QVBoxLayout` as the default.

### Rule 3 — Overflow Protection `[WARNING]`

If content height exceeds viewport: wrap in `QScrollArea` with `setWidgetResizable(True)`.

### Rule 4 — Size Policy Correctness `[ERROR]`

| Widget | Horizontal | Vertical |
|---|---|---|
| `QLabel` | `Preferred` or `Maximum` | `Preferred` |
| `QLineEdit`, `QTextEdit` | `Expanding` | depends on content |
| `QPushButton`, `QToolButton` | `Preferred` or `Minimum` | `Fixed` |
| `QGroupBox`, `QFrame`, container | `Expanding` | `Expanding` |
| `QListWidget`, `QTreeView`, `QListView` | `Expanding` | `Expanding` |
| `QScrollArea` | `Expanding` | `Expanding` |
| `QComboBox`, `QFontComboBox` | `Expanding` | `Fixed` |
| `QSlider` | `Expanding` | `Fixed` |

### Rule 5 — Spacing Consistency `[WARNING]`

Use a token system: `SPACING_NONE(0)`, `SPACING_XS(4)`, `SPACING_SM(8)`, `SPACING_MD(12)`, `SPACING_LG(16)`, `SPACING_XL(24)`, `SPACING_2XL(32)`.

### Rule 6 — Nesting Depth `[WARNING]`

Layout depth ≤ 4.  Flatten redundant single-child containers.

### Rule 7 — No Inline Stylesheets `[ERROR]`

All styling via a central `build_stylesheet()` method on a ThemeManager or equivalent.

**Exception A**: Dynamic property styling — `widget.setProperty("error", True)` + `widget.style().unpolish(widget); widget.style().polish(widget)` — matched with `[error="true"]` selectors in the central stylesheet.

**Exception B**: Runtime-determined colour values that can't be expressed via property selectors (Qt CSS can test property existence but not property *values*).  The inline fragment must be minimal — only `background-color`, with border/radius/padding in the central stylesheet via an `objectName` selector.

---

## Standard workflow

### Step 0. Preflight

1. Confirm PySide6 is available.
2. Determine mode:
   - **A — New UI**: build from scratch → Step 2A
   - **B — Layout repair**: fix existing code → Step 2B
   - **C — Lint only**: validate, no code changes → Step 2C
3. If building a settings dialog or any form-heavy UI, read [Settings Dialog Architecture](#settings-dialog-architecture) before writing layout code.
4. If repairing, read all target files in full.

### Step 1. Theme Setup (skip if project already has one)

Ensure a central theme manager exists that compiles all widget styles into one stylesheet.  Widget code must never contain `setStyleSheet()`.

### Step 2A. New UI Generation

Build the widget tree following the canonical patterns below.  Every container gets correct size policies.  Every `setContentsMargins`/`setSpacing` uses tokens.  Long content goes in `QScrollArea`.  Zero `move()`/`setGeometry()`/ad-hoc `setFixedSize()`.

### Step 2B. Layout Repair

Run all seven rules against the widget tree.  For each violation: annotate `[Rule N] <violation> → <fix applied>`.  Revalidate — zero ERROR violations must remain.  See [Common repair patterns](#common-repair-patterns) for the most frequent issues and their fixes.

### Step 2C. Lint Only

Run the seven rules, produce a report, do not modify files.

### Step 3. Final Lint

Run all seven rules.  Zero ERROR violations.  Confirm central stylesheet covers every widget class.

---

## Settings Dialog Architecture

*Derived from OBS Studio's production settings dialog.  These patterns have been tested across millions of users.  Do not deviate from this hierarchy — each layer serves a purpose.*

### Canonical component hierarchy

```
QDialog
└── QVBoxLayout                         # main_layout (margins=0, spacing=0)
    ├── QHBoxLayout                     # content_row (spacing=0)
    │   ├── QListWidget (sidebar)       # max 180px, icons + text, Minimum×Expanding
    │   └── QStackedWidget             # stretch=1
    │       └── QWidget (page) × N
    │           └── QVBoxLayout         # page_layout (leftMargin=9, others=0)
    │               └── QScrollArea     # (widgetResizable=True, NoFrame)
    │                   └── QWidget     # scroll_content
    │                       └── QVBoxLayout  # (margins=0)
    │                           └── QFrame  # styling surface
    │                               └── QVBoxLayout  # (margins=0)
    │                                   ├── QGroupBox
    │                                   │   └── QFormLayout (topMargin=2)
    │                                   ├── addSpacing(LG)
    │                                   ├── QGroupBox
    │                                   │   └── QGridLayout
    │                                   └── addStretch()  # pushes content to top
    └── QDialogButtonBox (OK / Cancel)
```

### Why each layer exists

- **Dialog → QVBoxLayout**: Separates the content row from the button box.  The button box is never inside the scroll area.
- **QHBoxLayout for sidebar + stack**: Sidebar is fixed, stack takes remaining space.  Zero spacing between them — the visual gap comes from widget margins.
- **QScrollArea per page**: Every settings page goes in its own scroll area.  This handles overflow when the dialog is resized smaller, and allows the page to grow when fonts are scaled up.
- **QGroupBox per logical section**: The primary unit of organisation.  Every group uses either `QFormLayout` (label–field pairs) or `QGridLayout` (multi-column rows).
- **QFormLayout for label–field pairs**: The standard pattern.  Labels are right-aligned; fields grow to fill remaining space.  Always set `fieldGrowthPolicy` to `AllNonFixedFieldsGrow`.

### Sidebar

```python
sidebar = QListWidget()
sidebar.setMaximumWidth(180)            # NOT setFixedWidth — allows shrinking
sidebar.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding)
sidebar.setIconSize(QSize(16, 16))      # 16×16 icons for each tab
sidebar.currentRowChanged.connect(self._on_sidebar_changed)

for name, icon_path in tabs:
    item = QListWidgetItem(QIcon(icon_path), name)
    item.setSizeHint(QSize(0, 36))       # comfortable touch target
    sidebar.addItem(item)
```

- Use `setMaximumWidth(180)` (not `setFixedWidth`) so the sidebar can shrink below the max.
- 16×16 icons for each tab — dramatically improves scannability.
- `setSizeHint(QSize(0, 36))` gives each item a comfortable touch target.
- The sidebar's size policy is `Minimum, Expanding` — it keeps its content width but can expand vertically.

### Page structure — the OBS pattern

Every settings page follows this exact nesting:

```
QWidget (page)
└── QVBoxLayout (leftMargin=9, top/right/bottom=0)
    └── QScrollArea (NoFrame, widgetResizable=True)
        └── QWidget (scroll content)
            └── QVBoxLayout (margins=0, spacing=0)
                └── QFrame
                    └── QVBoxLayout (margins=0)
                        ├── QGroupBox
                        │   └── QFormLayout (topMargin=2, AllNonFixedFieldsGrow)
                        │       ├── row: QLabel | QComboBox
                        │       ├── row: QLabel | QHBoxLayout(QLineEdit+QSlider)
                        │       └── row: QLabel | QHBoxLayout(QPushButton×4)
                        └── QSpacerItem (vertical, expanding)
```

**Why each layer exists:**

- **Page margin (left=9, others=0)**: Asymmetric — breathing room on the left, no wasted vertical space.  This is the OBS convention; 9px matches the sidebar's right edge padding.
- **QScrollArea with NoFrame**: Every page scrolls independently.  NoFrame keeps it visually clean.
- **QScrollArea → QWidget → QVBoxLayout → QFrame**: The QFrame is a styling surface.  It separates the scroll mechanics from the content.  All margins inside the QFrame are 0 — the page margin handles the outer spacing.
- **QGroupBox directly receives QFormLayout**: No need for an intermediate QVBoxLayout unless the group has multiple sections.
- **QFormLayout topMargin=2**: A tiny top margin inside the group box for visual breathing room.
- **QFormLayout with AllNonFixedFieldsGrow**: Fields expand to fill the column.  Without this, each field is only as wide as its content.
- **QFormLayout labelAlignment Right | AlignVCenter**: Labels form a clean right-aligned column.
- **QSpacerItem at the bottom**: Pushes all content to the top.  Without it, content is vertically centered in the scroll area.

### Page margin convention

```python
page_layout = QVBoxLayout(page)
page_layout.setContentsMargins(9, 0, 0, 0)   # OBS convention: left=9, rest=0
page_layout.setSpacing(0)
```

This asymmetric margin (left only) is the OBS standard.  When building new pages, follow it exactly — consistency across pages matters more than the specific pixel value.

### Vertical spacing — spacers, not margins

OBS uses `QSpacerItem` for vertical gaps between groups, NOT large `setSpacing()` values or `setContentsMargins()`.  This gives precise control over which gaps stretch and which are fixed:

```python
# Fixed gap between groups (invisible separator):
content_layout.addSpacing(SPACING_LG)

# Stretching spacer at the bottom (pushes content up):
content_layout.addStretch()
```

`addStretch()` at the bottom of the content layout is critical — without it, content floats in the vertical center of the scroll area instead of being top-aligned.

### Dialog sizing — auto-size, don't hardcode

```python
# WRONG — causes horizontal scroll bars, clipped content:
self.resize(700, 500)

# CORRECT — let the layout determine size:
self.setMinimumWidth(560)
self.setMinimumHeight(400)
self.setSizeGripEnabled(True)
```

If the dialog opens too small, check that every `QComboBox` and `QFontComboBox` has `setSizePolicy(Expanding, Fixed)` and that grid columns containing wide widgets have `setColumnStretch(col, 1)`.

### OK/Cancel vs OK/Cancel/Apply

| Pattern | When |
|---|---|
| **OK / Cancel** | Changes preview live in the main window.  OK saves, Cancel reverts. |
| **OK / Cancel / Apply** | Changes are complex or non-previewable.  Apply saves without closing. |

For live-preview settings (theme, colours, fonts), **OK / Cancel** is sufficient.

### Live preview with Cancel support

When settings apply live, save snapshots on dialog open and restore on Cancel:

```python
class AppearancePage(QWidget):
    def __init__(self, settings):
        self._saved_mode = get_mode(settings)
        self._saved_colors = dict(get_custom_colors(settings))
        self._saved_language = settings.get("app", {}).get("language", "en")
        # … fonts too …

    def _on_changed(self):
        self._apply_live()           # push to main window immediately

    def cancel(self):
        # restore all state from snapshots
        set_mode(settings, self._saved_mode)
        set_custom_colors(settings, self._saved_colors)
        # … fonts too …
        # push restored state to main window

    def commit(self):
        save(settings)               # persist to disk
```

Call `cancel()` from `SettingsDialog.reject()` — this catches Escape and title-bar close, not just the Cancel button click.

---

## Canonical patterns

### QFormLayout — the primary pattern for label–field pairs

This is the most important pattern in the skill.  Every group of label–widget pairs should use `QFormLayout`.

```python
group = QGroupBox("Section Title")
form = QFormLayout(group)
form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
form.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
form.setContentsMargins(SPACING_NONE, SPACING_SM, SPACING_NONE, SPACING_NONE)
form.setSpacing(SPACING_SM)

label = QLabel("Theme:")
combo = QComboBox()
combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
label.setBuddy(combo)                  # accessibility: click label → focus combo
form.addRow(label, combo)
```

Key properties:
- `AllNonFixedFieldsGrow`: Fields expand to fill the column.  Without this, each field is only as wide as its content.
- `labelAlignment`: Right-align labels for a clean vertical edge.
- `setBuddy()`: Accessibility — clicking the label focuses its buddy.

**Anti-pattern — do NOT use QFormLayout for rows with multiple field widgets.**  Use `QGridLayout` instead.

**Anti-pattern — do NOT nest QFormLayouts.**  Use separate `QGroupBox` widgets for sub-sections.

### QGridLayout — for multi-column aligned rows

When rows have multiple widgets that must align across rows (e.g., label | swatch | hex value | reset button), use `QGridLayout`.  Never use independent `QHBoxLayout` instances per row — labels won't align.

```python
group = QGroupBox("Colours")
grid = QGridLayout(group)
grid.setSpacing(SPACING_XS)
grid.setColumnStretch(0, 0)   # label column — natural width
grid.setColumnStretch(1, 0)   # swatch — fixed 28px
grid.setColumnStretch(2, 0)   # hex value — natural width
grid.setColumnStretch(3, 0)   # reset button — natural width

for i, (name, key) in enumerate(tokens):
    label = QLabel(name)
    label.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
    grid.addWidget(label, i, 0, Qt.AlignmentFlag.AlignLeft)

    swatch = QPushButton(objectName="colorSwatch")
    swatch.setFixedSize(28, 28)       # justified: icon-like fixed content
    swatch.setToolTip(f"{key} — {color.hex}")
    grid.addWidget(swatch, i, 1)

    hex_label = QLabel(color.hex)
    grid.addWidget(hex_label, i, 2)

    reset_btn = QPushButton("↺")
    reset_btn.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
    reset_btn.setToolTip("Reset to default")
    grid.addWidget(reset_btn, i, 3)
```

**Why column stretch = 0**: The grid fills the group box width, but we don't want columns to stretch — that creates gaps between swatch and hex label.  Columns take their natural widths.

**Why label.setSizePolicy(Maximum, Preferred)**: Labels take only the space they need, never more.  The grid column width is determined by the longest label; shorter labels don't stretch to fill.

### QGroupBox — the standard section container

```python
group = QGroupBox("Title")
layout = QVBoxLayout(group)            # or QFormLayout / QGridLayout directly
layout.setContentsMargins(SPACING_NONE, SPACING_SM, SPACING_NONE, SPACING_NONE)
layout.setSpacing(SPACING_SM)
```

If the group contains a single QFormLayout, set it directly as the group's layout — no need for a wrapping QVBoxLayout.

### QScrollArea — the standard page wrapper

```python
scroll = QScrollArea()
scroll.setWidgetResizable(True)        # MANDATORY
scroll.setFrameShape(QFrame.NoFrame)   # cleaner look
scroll.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

content = QWidget()
content_layout = QVBoxLayout(content)
content_layout.setContentsMargins(SPACING_NONE, SPACING_NONE, SPACING_NONE, SPACING_NONE)
content_layout.setSpacing(SPACING_LG)
# … add QGroupBox children …

scroll.setWidget(content)
```

### Button groups for mutually exclusive options

Stack them vertically — a horizontal row wastes space and forces a wider dialog.

```python
group = QGroupBox("Theme")
layout = QVBoxLayout(group)
layout.setSpacing(SPACING_XS)

for mode in [LIGHT, DARK, SYSTEM]:
    btn = QPushButton(label)
    btn.setCheckable(True)
    btn.setChecked(mode == current)
    btn.clicked.connect(lambda checked, m=mode: self._on_changed(m))
    btn.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
    layout.addWidget(btn)
```

For truly exclusive options, use `QButtonGroup` with `autoExclusive` — this is more declarative and handles mutual exclusion automatically:

```python
mode_group = QButtonGroup(self)
mode_group.setExclusive(True)

for mode in [LIGHT, DARK, SYSTEM]:
    btn = QPushButton(label)
    btn.setCheckable(True)
    btn.setChecked(mode == current)
    mode_group.addButton(btn)
    layout.addWidget(btn)

mode_group.buttonClicked.connect(self._on_mode_changed)
```

### QSlider + QLineEdit readout for numeric values

OBS Studio's font scaling uses this pattern: a slider for the value, with a read-only QLineEdit showing the current number.  This is more intuitive than a QComboBox for small numeric ranges.

```python
row = QHBoxLayout()

readout = QLineEdit(str(current_value))
readout.setReadOnly(True)
readout.setAlignment(Qt.AlignmentFlag.AlignCenter)
readout.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
readout.setMaximumWidth(40)
row.addWidget(readout)

slider = QSlider(Qt.Orientation.Horizontal)
slider.setMinimum(7)
slider.setMaximum(12)
slider.setValue(current_value)
slider.setTickPosition(QSlider.TickPosition.TicksBothSides)
slider.setTickInterval(1)
slider.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
slider.valueChanged.connect(
    lambda v: readout.setText(str(v))
)
row.addWidget(slider, stretch=1)
```

### Color preview as a styled QLabel (OBS pattern)

Instead of a separate swatch button + hex label, OBS uses a single QLabel that shows both the colour preview (via background styling) and the hex value (via text).  This is more compact and eliminates alignment issues between separate widgets.

```python
preview = QLabel("#RRGGBB")
preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
preview.setMinimumWidth(80)
# The background colour is set via dynamic property or minimal inline:
preview.setProperty("swatchColor", color.name())
preview.style().unpolish(preview)
preview.style().polish(preview)

choose_btn = QPushButton("Select Color")
choose_btn.clicked.connect(lambda: self._pick_color(key))

row = QHBoxLayout()
row.addWidget(preview)
row.addWidget(choose_btn)
row.addStretch()
```

Match in the central stylesheet:
```css
QLabel[swatchColor] {
    background-color: qproperty-swatchColor;  /* via Qt property */
    color: white;
    border-radius: 4px;
    padding: 4px 8px;
}
```

Note: Qt CSS `qproperty-` works for Q_PROPERTY declared properties.  For dynamic properties set via `setProperty()`, use the attribute selector in the stylesheet and style via the widget's palette or accept the minimal inline stylesheet exception for the background-color value.

### Mixed layouts — fixed sidebar + flexible content

```python
content_row = QHBoxLayout()
content_row.setSpacing(SPACING_NONE)
content_row.addWidget(sidebar)           # stretch=0 (default)
content_row.addWidget(stack, stretch=1)  # stretch=1 — takes remaining space
```

### Theme/language selection — QComboBox vs stacked buttons

For settings with 2–4 mutually exclusive options, a **QComboBox** is often more space-efficient than stacked buttons.  OBS uses a combo for theme selection (20+ themes).  For 3 options (Light/Dark/System), a combo keeps the dialog narrow:

```python
# In a QFormLayout:
form.addRow(QLabel("Theme:"), theme_combo)
```

Stacked buttons are better when the options need descriptive labels or the user benefits from seeing all choices at once (e.g., density: Classic, Compact, Normal, Comfortable).

### Dynamic property styling (Rule 7 Exception A)

```python
widget.setProperty("active", True)
widget.style().unpolish(widget)
widget.style().polish(widget)
```

Matched in central stylesheet: `QPushButton[active="true"] { … }`

---

## Common repair patterns

### Pattern: Rows don't align because each uses its own QHBoxLayout

**Symptom**: Labels in a group are misaligned — "Background" and "Primary Container" start at different horizontal positions.

**Fix**: Replace individual `QHBoxLayout` instances with one `QGridLayout` per group.  See [QGridLayout pattern](#qgridlayout--for-multi-column-aligned-rows).

### Pattern: Dialog too wide — too many controls in one horizontal row

**Symptom**: Font controls (`Family | Size | Weight`) in one row force a wide dialog.

**Fix**: Use a 2-row grid: `Family` full-width on row 0, `Size | Weight` side-by-side on row 1.  Stack theme-mode buttons vertically instead of horizontally.  See [Button groups](#button-groups-for-mutually-exclusive-options).

### Pattern: Horizontal scrolling because of hardcoded dialog size

**Symptom**: Dialog is `resize(700, 500)` — opening it shows horizontal scroll or clipped content.

**Fix**: Remove `resize()`.  Let the dialog auto-size.  Set `setMinimumWidth(560)`, `setMinimumHeight(400)`, `setSizeGripEnabled(True)`.  Ensure `QFontComboBox` has `setSizePolicy(Expanding, Fixed)`.

### Pattern: Wasted horizontal space from trailing addStretch()

**Symptom**: Each color row uses only ~40% of the available width, with empty space on the right.

**Fix**: Remove `row.addStretch()`.  The layout should fill the available space naturally.  If you want the row to not stretch, use a `QGridLayout` with column stretch values of 0.

### Pattern: Duplicate widget added to layout

**Symptom**: Console warnings: `QLayout::addChildLayout: layout already has a parent`.

**Fix**: Each widget must be added to a layout exactly once.  Search for accidental duplicate `addWidget()` calls.

### Pattern: setFixedWidth on non-icon widgets

**Symptom**: Sidebar: `sidebar.setFixedWidth(160)` prevents shrinking.  Label: `label.setMinimumWidth(120)` forces fixed column width.

**Fix**: Sidebar: use `setMaximumWidth(180)`.  Labels in grids: use `setSizePolicy(Maximum, Preferred)`.

### Pattern: Lazy import inside _setup_ui

**Symptom**: `from PySide6.QtWidgets import QFontComboBox` inside a method body.

**Fix**: Move to module-level imports.  PySide6 imports are cheap and module-level is the Python standard.

---

## Lint report format

```
Rule | Severity | Location            | Issue
-----|----------|---------------------|------------------------------------------
1    | ERROR    | main_window.py:42   | move(0,0) — replace with layout
2    | ERROR    | main_window.py:58   | QWidget has children but no setLayout()
4    | ERROR    | main_window.py:73   | QPushButton has Expanding×Expanding; should be Preferred×Fixed
5    | WARNING  | main_window.py:90   | setContentsMargins(10,10,10,10) — use SPACING_MD
```

Sorted by severity (ERROR first), then rule number, then location.

---

## Cross-platform guidance

### Font fallback

Platform defaults: `Segoe UI` (Windows), `SF Pro Display` (macOS), `Noto Sans` (Linux).  Always provide a fallback chain in stylesheets: `font-family: "CustomFont", "Segoe UI", "Helvetica Neue", Arial, sans-serif;`

### QFontComboBox warnings

On Windows, `QFontComboBox` emits `DirectWrite: CreateFontFaceFromHDC() failed` for legacy bitmap fonts (MS Sans Serif, Fixedsys).  These are **harmless** — do not replace `QFontComboBox` with a curated `QComboBox` to suppress them.  Users deserve access to all installed fonts.

### QScrollArea checklist

- `setWidgetResizable(True)` — mandatory
- `setFrameShape(QFrame.NoFrame)` — cleaner look
- `setSizePolicy(Expanding, Expanding)` — grows with dialog

### Prefer QFrame over QWidget for containers

`QFrame` (with `QFrame.NoFrame` for no border) supports stylesheet styling more predictably across platforms.

---

## Icon System

### SVG-first, centrally managed

Use SVG icons exclusively.  Never inline raster PNGs or base64-encoded images.  All icon access goes through a single `IconManager` singleton:

```python
from ui.icon_manager import icon

btn.setIcon(icon("actions", "plus"))
btn.setIconSize(QSize(20, 20))
```

### Icon directory structure

Organise by semantic category, not by visual style:

```
icons/
  actions/       # plus, minus, reload, save, settings
  arrows/        # arrow-up, arrow-down, arrow-back, arrows-maximize
  forms/         # check, checkbox
  navigation/    # back, forward, home
  status/        # warning, error, info
```

Use semantic names, not visual descriptions.  Good: `search.svg`, `settings.svg`.  Bad: `magnifier_icon.svg`, `gear_blue.svg`.

### Icon sizing

| Context | Size |
|---|---|
| Toolbar buttons | 16–20 px |
| Regular buttons | 18–24 px |
| Sidebar | 20–28 px |
| Primary action buttons | 32–48 px |

Always call `setIconSize(QSize(w, h))` explicitly — never rely on Qt's default.

### Theme-aware colouring

Tabler Icons use SVG `currentColor`.  Qt's SVG renderer does not support `currentColor`, so the `IconManager` must replace it at render time:

```python
svg_text = path.read_text()
svg_text = svg_text.replace('"currentColor"', f'"{theme_color}"')
renderer = QSvgRenderer(svg_text.encode("utf-8"))
```

Cache the rendered `QIcon` and clear the cache on theme change.  Call `IconManager().set_color(hex)` from `ThemeManager._apply()`.

### Qt Resource System (optional, for production)

For frozen executables, embed icons via `.qrc`:

```xml
<RCC>
  <qresource prefix="/icons">
    <file>icons/actions/plus.svg</file>
  </qresource>
</RCC>
```

Compile with `pyside6-rcc resources.qrc -o resources_rc.py` and import the generated module.  Then use `QIcon(":/icons/actions/plus.svg")`.

Alternatively, bundle the `icons/` directory via PyInstaller `--add-data` (simpler, no compile step).

### Anti-patterns

- Hardcoded icon paths in widget code
- Mixing icon libraries (stick to one set)
- Raster icons (PNG) for scalable UI
- Glyph characters (⊕, ↺) as icon substitutes — they render inconsistently across platforms
- Inline base64-encoded icon data

---

## When not to use this skill

- Non-GUI PySide6: threading, data models, network, file I/O.
- PyQt or C++ Qt code.
- Web or mobile UIs.
