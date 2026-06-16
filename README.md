# dspng

A standalone tool for rendering PSD files to PNG without Photoshop.

## Features

- **PSD Import**: Open PSD files via file dialog or drag-and-drop
- **Layer Management**: Toggle visibility (eye/eye-closed icons), reorder layers/groups via drag-and-drop or arrow buttons, expand/collapse all groups, tri-state bulk visibility, save state back to PSD
- **Real-time Rendering**: Composite preview with zoom, pan (middle-click, right-click, Alt+left-click), and fit-to-view
- **PNG Export**: Save dialog, drag-export with custom naming (`{name}_{counter:03d}.png`), per-file counter, configurable temp directory
- **Theme Customisation**: Dark/Light/System theme modes, 14 customisable colour tokens, font family/size/weight, live preview
- **i18n**: English + 简体中文, runtime language switching
- **Settings Dialog** (Ctrl+,): Appearance, Files, Keymaps tabs

## Quick Start

```bash
uv sync
uv run dspng
uv run dspng path/to/file.psd
```

## Build

```bash
uv run scripts/build.py
# Output: dist/dspng.exe
```

## Architecture

```
src/dspng/
├── models.py           # PsdDocument, LayerNode, LayerGroup
├── psd_manager.py      # PSD loading via psd-tools
├── renderer.py         # Compositing, thumbnails, PNG export
└── ui/
    ├── main_window.py       # Three-panel layout + menus
    ├── icon_manager.py      # SVG icon loading + colourisation
    ├── locale_manager.py    # gettext-based i18n
    ├── theme_manager.py     # Central stylesheet + font/colour customisation
    ├── theme_tokens.py      # M3 design tokens (spacing, colours, fonts)
    ├── settings.py          # ~/.dspng/settings.json persistence
    ├── settings_dialog.py   # Multi-tab settings (Appearance, Files, Keymaps)
    └── panels/
        ├── file_list.py      # File list with inline name/counter edit
        ├── layer_panel.py    # Layer tree with eye icons, drag-drop reorder, save to PSD
        └── render_canvas.py  # Zoom/pan/drag-export canvas

icons/                  # Tabler SVG icons
locales/                # .po/.mo translation files
scripts/                # Build + locale compilation
```

## Keyboard & Mouse

| Input | Action |
|---|---|
| Ctrl+O | Open PSD file |
| Ctrl+E | Export PNG |
| Ctrl+, | Settings |
| Ctrl+Q | Quit |
| Scroll wheel | Zoom in/out |
| Middle-click / Right-click / Alt+Left drag | Pan |
| Double-click | Fit to view |
| Left-click drag | Drag-export PNG |

## License

GPL-2.0 — see [LICENSE](LICENSE).
