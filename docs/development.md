# Development Guide

## Requirements

- Python 3.14+
- [uv](https://docs.astral.sh/uv/) package manager

## Install dependencies

```bash
uv sync
```

## Run

```bash
# Launch GUI
uv run dspng

# Open PSD file directly
uv run dspng path/to/file.psd

# Or via python -m
uv run python -m dspng
```

## Project structure

```
├── pyproject.toml           # Project config + dependencies
├── uv.lock                  # Locked dependency versions
├── src/dspng/               # Source code
│   ├── models.py            # Data models (pure data, zero GUI logic)
│   ├── psd_manager.py       # PSD loading + DocumentStore
│   ├── renderer.py          # Image compositing + thumbnails + export
│   ├── main.py              # Entry point
│   └── ui/                  # GUI layer
│       ├── main_window.py   # Main window layout + menus
│       ├── theme_manager.py # M3 theme engine (singleton)
│       ├── theme_tokens.py  # M3 spacing/colour/font tokens
│       ├── icon_manager.py  # SVG icon loader (theme-aware)
│       ├── locale_manager.py# i18n via gettext + tr()
│       ├── settings.py      # Persistent settings (~/.dspng/settings.json)
│       ├── settings_dialog.py
│       └── panels/          # Panel widgets
├── locales/                 # .po/.mo translation files
│   ├── en/LC_MESSAGES/
│   └── zh_CN/LC_MESSAGES/
├── icons/                   # SVG icons (by category)
├── tabler-icons/            # Upstream Tabler Icons
├── scripts/                 # Build + utility scripts
├── docs/                    # Documentation
└── issues/                  # Issue tracker
```

## Code conventions

- Use type hints throughout.
- Docstrings explain "why", not "what".
- Data models (`models.py`) contain zero GUI logic.
- GUI is signal-driven: panels communicate via Qt signals, never by direct
  method calls across modules.
- All user-visible strings go through `tr()` for i18n support.
- All styling lives in `ThemeManager.build_stylesheet()` — no inline
  `setStyleSheet()` on individual widgets (Rule 7 exception for runtime
  colour values only).
- Spacing tokens (`SPACING_XS`…`SPACING_2XL`) for all margins/padding —
  no hardcoded integer literals.

## Adding dependencies

```bash
uv add <package-name>
```

## i18n — adding translatable strings

1. Add `msgid`/`msgstr` entries to `locales/en/LC_MESSAGES/messages.po`
   and `locales/zh_CN/LC_MESSAGES/messages.po`.
2. Compile both `.mo` files:
   ```bash
   uv run scripts/compile_locales.py
   ```
3. Use `tr("Your string")` in widget code.  For strings that must update
   at runtime (tooltips, button text), connect to
   `LocaleManager().language_changed` and re-set them in a
   `_retranslate_ui()` method.

## Icons — adding new icons

1. Find the SVG in `tabler-icons/outline/`.
2. Copy it to `icons/{category}/{name}.svg` (use semantic categories:
   `actions/`, `arrows/`, `status/`).
3. Use in code: `btn.setIcon(icon("actions", "plus"))`.
4. The `IconManager` handles `currentColor` → theme colour replacement
   automatically.

## Linting

```bash
# Ruff is configured as pre-commit hook — run manually:
uv run ruff check src/
uv run ruff format --check src/
```

## Packaging

```bash
# Build standalone Windows executable
uv run scripts/build.py
```

Output lands in `dist/`.
