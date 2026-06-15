---
name: pyside6-m3-ui-system
description: Generates, validates, and auto-fixes PySide6 GUIs with a Material Design 3 theme engine. Use when building or repairing PySide6/Qt widget-based interfaces with token-driven styling, layout enforcement, lint rules, or natural-language UI synthesis. Also use when the user asks to fix PySide6 layout bugs (overlapping widgets, missing layouts, broken resize, absolute positioning).
---

# PySide6 M3 UI System

Generates and repairs PySide6 GUIs through an integrated pipeline: Material 3 theme engine → natural-language UI synthesis → layout auto-fix → lint validation. Every output widget tree is guaranteed layout-based, token-styled, scroll-aware, and free of absolute positioning.

## Read also

- [Theme tokens](templates/theme-tokens.py) — copy-paste token definitions
- [ThemeManager](templates/theme-manager.py) — centralised theme engine base class
- [Layout hard constraints](references/layout-rules.md) — non-negotiable layout rules and severity levels
- [UI DSL grammar](references/ui-dsl-grammar.md) — intermediate representation for NL-to-UI conversion

## Non-negotiable safety policy

Must:

1. Never fabricate citations.
2. Never fabricate numeric results, experiment outcomes, or hardware specs.
3. If key info is missing, ask up to 5 targeted questions, then proceed with explicit placeholders.
4. Keep claims proportional to evidence.

In addition, for PySide6 code specifically:

5. Never emit `move()`, `setGeometry()`, or ad-hoc `setFixedSize()` — always use layout managers.
6. Never emit a `QWidget` with children but no layout — inject one if missing.
7. Never emit inline `setStyleSheet()` calls on individual widgets — styling is compiled centrally via ThemeManager.
8. Never emit hardcoded margin/spacing/radius integers — always reference the token system.
9. Always run the lint rule checklist against the final widget tree before delivering output.

## Mandatory intake questions

Ask before starting work (unless already answered):

1. What should the UI do? (Describe the purpose, key sections, and interactions.)
2. Is this a new UI from scratch, or are you repairing / extending existing PySide6 code? If existing, provide the file paths.
3. Which platforms must it support? (Windows, macOS, Linux — default: all three.)
4. Which theme modes are needed? (light only, dark only, or runtime switching between both.)
5. Are there PySide6 version constraints? (Default: PySide6 ≥ 6.5.)

## Standard workflow

### Step 0. Preflight

- Confirm PySide6 is available in the project environment (`pip list | grep PySide6` or check `requirements.txt` / `pyproject.toml`).
- If repairing existing code, read the target files in full before making changes.
- Identify whether the request is: (a) new UI generation, (b) layout repair, (c) theme application, or (d) lint pass only.
- Load the [layout rules reference](references/layout-rules.md) — all seven rules must be enforced.

---

### Step 1. Theme Engine Setup

When the project does not yet have a theme system:

1. Copy `templates/theme-tokens.py` into the project (suggest `theme_tokens.py`).
2. Copy `templates/theme-manager.py` into the project (suggest `theme_manager.py`).
3. Subclass `ThemeManager` and override `build_stylesheet()` with widget-class selectors that reference tokens:
   - Use class-based selectors only (`.MyWidget`, `QPushButton#primary`, etc.).
   - Reference token values via `self.get("primary")`, not hardcoded hex codes.
   - Apply the same token for the same semantic role across all platforms.
4. In the application entry point, instantiate the ThemeManager after `QApplication`:
   ```python
   app = QApplication(sys.argv)
   theme = ThemeManager()
   theme.set_theme("light")
   ```

When the project already has a theme manager, work within the existing pattern.

---

### Step 2. Natural Language → UI Generation

When building a new UI from a description:

1. Parse the user's intent into a structured UI tree using the [DSL grammar](references/ui-dsl-grammar.md).
2. Produce the DSL tree first — validate it structurally before writing any Python code.
3. Run the DSL validation checks:
   - Every container has ≥ 1 child.
   - No leaf widget outside a layout container.
   - Form children are label–input pairs.
   - Nesting depth ≤ 4 (flatten if exceeded).
4. Convert the validated DSL tree to PySide6 Python code:
   - Every `Row` → `QHBoxLayout`, `Column` → `QVBoxLayout`, `Grid` → `QGridLayout`, `Form` → `QFormLayout`.
   - Every container widget receives correct size policies per [Rule 4](references/layout-rules.md).
   - Every `setContentsMargins` and `setSpacing` call uses a spacing token.
   - Long content areas are wrapped in `QScrollArea`.
   - Zero uses of `move()`, `setGeometry()`, or ad-hoc `setFixedSize()`.
5. Wire up the ThemeManager: widgets reference theme tokens via the manager, not inline style strings.

---

### Step 3. Layout Auto-Fix (Repair Mode)

When repairing existing code that has layout violations:

1. Read the existing widget file(s) in full.
2. Build a mental / AST model of the widget tree — identify parent–child relationships.
3. Run every rule from the [layout rules reference](references/layout-rules.md) against the tree:
   - **Rule 1 (abs positioning)** — Scan for `move()`, `setGeometry()`. Replace with layout manager.
   - **Rule 2 (missing layout)** — For each `QWidget` with children, confirm `setLayout()` is called. Inject `QVBoxLayout` if missing.
   - **Rule 3 (overflow)** — Estimate content height. Wrap in `QScrollArea` if exceeds viewport.
   - **Rule 4 (size policy)** — Check each widget's policy against the table. Correct mismatches.
   - **Rule 5 (spacing)** — Replace hardcoded integer margins/spacing with tokens.
   - **Rule 6 (nesting)** — Count layout depth. Flatten if > 4.
   - **Rule 7 (inline styles)** — Remove `setStyleSheet()` calls. Add selectors to `ThemeManager.build_stylesheet()` instead.
4. For each fix, explain the violation found and the transformation applied.
5. Revalidate the tree after all fixes — no error-level violations must remain.

---

### Step 4. Lint & Final Validation

Before delivering any output (new or repaired):

1. Run the full seven-rule checklist.
2. Categorise each finding by severity:
   - **ERROR** — Must be fixed before delivery (Rules 1, 2, 4, 7).
   - **WARNING** — Should be fixed; flag for user if not (Rules 3, 5, 6).
3. Produce a lint report listing: rule violated, location (widget/line), severity, fix applied or recommended.
4. Verify zero ERROR-level violations remain.
5. Confirm the ThemeManager is wired and the `build_stylesheet()` method covers all widget classes used.

---

### Step 5. Main Output Assembly

Prepare deliverables per the output contract below.

- For **new UIs**: deliver the complete Python file(s) — theme tokens, theme manager subclass, and widget class(es).
- For **repairs**: deliver a diff or edited file with a summary of each fix applied.
- For **lint-only**: deliver the lint report with violations and recommended fixes.

## Standard output contract (every run)

1. **Assumptions** — what was inferred from the user's description (layout structure, theme mode, platform defaults).
2. **Missing info** — any unanswered intake questions; explicit placeholders used.
3. **Risks** — cross-platform behaviour that could not be verified, Qt version-specific API differences, or untested edge cases.
4. **Main output(s)**
   - Generated or repaired Python source file(s).
   - Lint report (if lint was run).
   - DSL tree (if NL-to-UI generation was performed).
5. **Evidence/citation/integrity flags**
   - `[EVIDENCE NEEDED: <claim>]`
   - `[REFERENCE NEEDED: <claim>]`
   - `[VERIFY DETAIL: <statement>]`
6. **Next actions for user** — run the file, verify appearance, test resize behaviour, test theme switching if applicable.

## Domain-specific sections

### Cross-platform font fallback

The token system defaults to platform-appropriate sans-serif fonts. When overriding, test on all target platforms — font metrics differ, which affects label truncation and minimum widget sizes.

### QScrollArea gotcha

`QScrollArea` requires `setWidgetResizable(True)` for the content to expand with the viewport. Always include this when wrapping content.

### Layout stretch factors

When a `QHBoxLayout` or `QVBoxLayout` has mixed fixed/flexible children, apply stretch factors to avoid collapsed flexible regions:

```python
layout.addWidget(sidebar, stretch=0)   # fixed width
layout.addWidget(content, stretch=1)   # takes remaining space
```

### Avoid QWidget as layout-only container

Prefer `QFrame` (with `QFrame.NoFrame` if no border needed) over bare `QWidget` for layout-only containers. `QFrame` supports stylesheet styling more predictably across platforms.

### Dynamic property styling

For state-based styling that is not structural (active, hover, error, selected), use Qt dynamic properties instead of inline stylesheets:

```python
widget.setProperty("error", True)
widget.style().unpolish(widget)
widget.style().polish(widget)
```

Then match in the central stylesheet: `QLineEdit[error="true"] { border: 1px solid red; }`

## Deviation note

None.
