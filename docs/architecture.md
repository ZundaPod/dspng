# dspng Architecture

## Overview

dspng is a standalone PSD → PNG render/export tool that does not require
Photoshop.  Users import PSD files, adjust layer visibility and order in
memory, preview the composited result in real time, and export PNGs via
drag-and-drop or the File menu.

## Tech stack

| Component       | Technology                         |
|-----------------|------------------------------------|
| Language        | Python 3.14                        |
| Package manager | uv                                 |
| PSD parsing     | psd-tools3                         |
| GUI             | PySide6 (Qt for Python)            |
| Image processing| Pillow (PIL)                       |
| Packaging       | PyInstaller                        |
| Linting         | Ruff (pre-commit hooks)            |

## Directory structure

```
src/dspng/
├── __init__.py
├── __main__.py               # python -m dspng entry point
├── main.py                   # QApplication bootstrap + CLI args
├── models.py                 # Data models (LayerNode, LayerGroup, PsdDocument)
├── psd_manager.py            # PSD loading + DocumentStore state management
├── renderer.py               # Image compositing + thumbnails + PNG export
└── ui/
    ├── __init__.py
    ├── main_window.py         # Main window (three-panel layout + menus + signals)
    ├── theme_manager.py       # Central M3 theme engine (singleton), stylesheet compiles
    ├── theme_tokens.py        # M3 spacing/radius/colour/font tokens (LIGHT, DARK)
    ├── icon_manager.py        # SVG icon loader with theme-aware colour replacement
    ├── locale_manager.py      # gettext i18n, tr() shortcut, runtime language switch
    ├── settings.py            # Persistent user settings (~/.dspng/settings.json)
    ├── settings_dialog.py     # Settings dialog (Appearance, Files, Keymaps pages)
    └── panels/
        ├── __init__.py
        ├── file_list.py       # File list panel (top-right)
        ├── layer_panel.py     # Layer tree panel (bottom-right)
        └── render_canvas.py   # Render canvas (left, zoomable/pannable QGraphicsView)

scripts/
├── build.py                  # PyInstaller packaging script
├── compile_locales.py        # .po → .mo compiler (custom, no msgfmt dependency)
└── make_icon.py              # App icon generator

locales/
├── en/LC_MESSAGES/           # English .po/.mo (pass-through)
└── zh_CN/LC_MESSAGES/        # Simplified Chinese .po/.mo

icons/                        # SVG icons organised by semantic category
├── actions/                  # plus, minus, reload, device-floppy, …
├── arrows/                   # arrow-up, arrow-down, layout-navbar-*, …
└── status/                   # eye, eye-closed, eye-dotted, eye-off

tabler-icons/                 # Upstream Tabler Icons source (outline + filled)
docs/                         # Documentation
issues/                       # Issue tracker
icon.ico / icon.png           # App icons
```

## Core modules

### models.py — Data models

Pure data containers, zero GUI logic:

- **`LayerNode`**: single raster layer — holds PIL image, offset, visibility,
  opacity, blend mode, and a back-reference (`_psd_ref`) for save-to-PSD sync.
- **`LayerGroup`**: folder/group — recursive list of children, own visibility
  and opacity, `open_folder` flag for expand/collapse persistence.
- **`PsdDocument`**: full in-memory representation of a PSD file — layer tree,
  dimensions, editable `display_name`, `export_counter`, and thumbnail cache.

Every model provides `invalidate_thumbnail()` to clear cached thumbnails.

### psd_manager.py — PSD loading

- `load_psd(path)` opens a PSD via psd-tools3, recursively extracts the layer
  tree, and attaches `_psd_ref` back-references to every model node for
  save-back support.
- Layers are traversed bottom-to-top (index 0 = bottom-most), matching
  Photoshop's compositing order.
- `DocumentStore` manages all loaded documents and the current selection.
- `PsdLoadError` custom exception raised on parse failure.

### renderer.py — Image compositing

- `composite(doc)` walks the layer tree in paint order and alpha-composites
  each visible layer onto an RGBA canvas.  Layer opacity is applied by
  scaling the alpha channel.  Group opacity propagates recursively.
- Only the "normal" blend mode is implemented; all other modes fall back
  to normal.
- `make_thumbnail(image, size)` creates fixed-square thumbnails (aspect
  ratio is NOT preserved — fills to fit).
- `generate_*_thumbnail()` helpers with size-aware caching.
- `export_png()` and `composite_to_bytes()` for file-save and drag-drop.

### UI layer

- **Main window**: three-panel resizable layout via `QSplitter`:
  - Left: Render canvas with temp-directory row and (future) flip controls.
  - Top-right: File list panel.
  - Bottom-right: Layer panel.
  - File menu: Open, Export PNG, Settings, Quit.
  - Help menu: About dialog.
  - Settings persisted to `~/.dspng/settings.json`.
- **File list**: drag-drop PSD files, click to select, add/remove/reload.
  Per-item: thumbnail, inline-edit display name, export counter spinbox.
  S/M/L thumbnail size presets (32/64/128 px).
- **Layer panel**: tree view with custom `_VisibilityDelegate` for per-row
  eye-icon toggles.  Drag-drop reorder.  Expand/collapse all, tri-state
  visibility toggle (all/none/mixed).  Move-up/move-down buttons.
  Save-to-PSD button syncs visibility, order, and expand state back to the
  source file via `_psd_ref` back-references.
  S/M/L row-height presets (32/64/128 px) via dynamic property styling.
- **Render canvas**: `QGraphicsView` with checkerboard transparency
  background.  Scroll-wheel zoom (centered on cursor), middle/right/Alt+left
  pan, double-click fit-to-view, left-drag PNG export (writes to temp dir,
  advances counter).

### Theme system

- **`theme_tokens.py`**: defines Material Design 3 spacing tokens
  (`SPACING_XS`…`SPACING_2XL`), radius tokens (`RADIUS_SM`…`RADIUS_LG`),
  and `LIGHT`/`DARK` colour palettes.  Platform-adaptive font defaults
  (Segoe UI / SF Pro Display / Noto Sans).
- **`theme_manager.py`**: singleton `ThemeManager` that compiles the full Qt
  stylesheet from token values via `build_stylesheet()`.  Supports runtime
  light/dark/system mode switching, custom colour overrides (per-token),
  and custom font family/size/weight overrides.  Pushes the compiled
  stylesheet, font, and icon colour to `QApplication` on every change.
  **All widget styling is centralised here — no inline `setStyleSheet()`.**

### i18n / Locale system

- **`locale_manager.py`**: singleton `LocaleManager` wrapping Python's
  `gettext`.  Pre-loads compiled `.mo` files from `locales/`.  Emits
  `language_changed` signal so widgets can re-translate themselves.
- **`tr(message)`**: shortcut that returns the translation for the active
  language, falling back to the original string.
- Available languages: English (`en`), Simplified Chinese (`zh_CN`).
- `.po` → `.mo` compilation via `scripts/compile_locales.py` (pure Python,
  no `msgfmt` dependency).

### Icon system

- **`icon_manager.py`**: singleton `IconManager` that loads Tabler outline
  SVG icons from `icons/{category}/{name}.svg`.  Qt's SVG renderer does not
  support `currentColor`, so the manager replaces it with the theme's
  `text_primary` colour at render time.  Caches rendered `QIcon` objects;
  clears cache on theme change (`set_color()`).
- **`icon(category, name)`**: convenience shortcut.

## Signal flow

```
User clicks visibility eye-icon
  → _VisibilityDelegate._on_clicked
  → LayerTreeModel.setData (toggle item.visible + invalidate ancestor thumbnails)
  → LayerPanel._on_visibility_toggled
    → regenerate thumbnails at current size
    → emit layer_visibility_changed → RenderCanvas.refresh_composite (keep zoom)
    → emit thumbnail_changed → FileListPanel.refresh_current_thumbnail

Language changed in settings
  → LocaleManager.set_language
    → emit language_changed
      → MainWindow._retranslate_ui (window title, menus, panel titles, tooltips)
      → FileListPanel._retranslate_ui (button tooltips)
      → LayerPanel._retranslate_ui (button tooltips)

Theme changed in settings
  → MainWindow._apply_theme
    → ThemeManager.set_theme / set_custom_colors
      → ThemeManager._apply → rebuild stylesheet + update icon colour + set app font
```

## Known limitations

- Only the "normal" blend mode is supported; other modes fall back to normal.
- Drag-export temp files are not automatically cleaned up.
- Initial load of large PSDs (100+ layers) can be slow.
- Layer visibility/size-panel nesting depth ~5 — deferred per AGENTS.md.
