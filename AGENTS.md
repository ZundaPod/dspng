# Agent instructions for dspng

## Git policy

- **Do NOT commit unless the user explicitly asks.**  No auto-commits, no
  commits at the end of a fix.  Wait for "commit" or equivalent.
- When the user does ask to commit, use the `commit-writer` skill.
- Rearrange/squash commits when asked — the user prefers compact history.
- Never force-push without explicit permission.

## Fixup discipline

- After implementing a feature, test it in the user's environment before
  committing.  The user will report bugs and iterate.  Do NOT commit
  intermediate fixes — batch them into the feature commit when the user
  is satisfied.
- If a bug is caused by a too-early commit, squash the fix into the
  original feature commit during the next rearrangement.

## Project conventions

- Python 3.14+, PySide6 6.11+
- `uv` for package management
- Ruff for linting and formatting (run via pre-commit hooks)
- Spacing tokens (`SPACING_XS`…`SPACING_2XL`) for all margins/padding
- No inline `setStyleSheet()` (Rule 7 exception for runtime colour values)
- Use `tr()` for all user-visible strings (101 strings, en + zh_CN)
- Icons from `icons/` via `IconManager`, SVG Tabler icons with theme-aware coloring
- `ui-design` skill for all layout work — follow its rules strictly

## Key files

| File | Purpose |
|---|---|
| `src/dspng/ui/theme_manager.py` | Central stylesheet, custom colours/fonts |
| `src/dspng/ui/theme_tokens.py` | M3 spacing/colour/font tokens |
| `src/dspng/ui/icon_manager.py` | SVG icon loading + color replacement |
| `src/dspng/ui/locale_manager.py` | gettext i18n, `tr()` function |
| `src/dspng/ui/settings_dialog.py` | Settings dialog (Appearance, Files, Keymaps) |
| `scripts/compile_locales.py` | .po → .mo compiler |

## Known issues

- Rule 6 nesting depth ~5 in panel containers — deferred.
