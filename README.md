# dspng

A standalone tool for rendering PSD files to PNG without launching Photoshop.

## Features

- **PSD Import**: Open PSD files via file dialog or drag-and-drop
- **Layer Management**: Toggle visibility, reorder layers/groups with drag or buttons
- **Real-time Rendering**: Composite preview with zoom, pan, and fit-to-view
- **PNG Export**: Save dialog, drag-export to Premiere/file manager, batch export
- **Thumbnails**: Square thumbnails in file list and layer panel with S/M/L size presets
- **Dark Theme**: Lettepa color palette with Light/Dark/System toggle and 6 accent colors
- **Keyboard Shortcuts**: Ctrl+O/E/Q, scroll zoom, middle-click pan, double-click fit

## Quick Start

```bash
# Install dependencies
uv sync

# Run
uv run dspng

# Open a specific file
uv run dspng path/to/file.psd
```

## Build Standalone EXE

```bash
uv run scripts/build.py
# Output: dist/dspng.exe (~63MB, no Python required)
```

## Architecture

```
src/dspng/
├── models.py           # LayerNode, LayerGroup, PsdDocument
├── psd_manager.py      # PSD loading via psd-tools
├── renderer.py         # Compositing, thumbnails, PNG export
└── ui/
    ├── main_window.py  # Three-panel layout + menus
    ├── themes.py       # Lettepa palette + theme definitions
    ├── styles.py       # Dynamic QSS stylesheet
    ├── settings.py     # ~/.dspng/settings.json persistence
    └── panels/
        ├── file_list.py      # File list with S/M/L presets
        ├── layer_panel.py    # Layer tree with visibility/reorder
        └── render_canvas.py  # Zoom/pan/drag-export canvas
```

## Keyboard Shortcuts

| Shortcut | Action |
|---|---|
| Ctrl+O | Open PSD file |
| Ctrl+E | Export PNG |
| Ctrl+Q | Quit |
| F1 | Keyboard shortcuts help |
| Scroll wheel | Zoom in/out |
| Middle-click drag | Pan |
| Alt+Left-click drag | Pan |
| Double-click | Fit to view |
| Left-click drag | Drag export PNG |

## License

GPL-2.0 — see [LICENSE](LICENSE).

## Author

[johanvx](https://github.com/johanvx)
