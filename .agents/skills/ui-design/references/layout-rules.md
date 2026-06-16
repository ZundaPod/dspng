# PySide6 Layout Hard Constraints

These rules are **non-negotiable** for any generated or repaired UI.

---

## Rule 1 — Absolute Positioning Ban

**Severity: ERROR**

The following APIs are forbidden in any generated or repaired code:

- `QWidget.move(x, y)`
- `QWidget.setGeometry(x, y, w, h)`
- `QWidget.setFixedSize(w, h)` (unless the widget truly has fixed content, e.g. an icon)

**Required fix**: Replace with a layout manager (`QVBoxLayout`, `QHBoxLayout`, `QGridLayout`, `QFormLayout`).

---

## Rule 2 — Mandatory Layout for Parent Widgets

**Severity: ERROR**

If a `QWidget` (or subclass) has one or more child widgets, it **must** have a layout set via `setLayout()`.

**Required fix**: Inject `QVBoxLayout` as the default and reparent children into it.

---

## Rule 3 — Overflow Protection

**Severity: WARNING**

If the estimated content height exceeds the viewport / container height:

- Wrap the content widget in a `QScrollArea`.
- Enable `wordWrap` on text widgets when their container may be narrow.

---

## Rule 4 — Size Policy Correctness

**Severity: ERROR**

| Widget type | Horizontal policy | Vertical policy |
|---|---|---|
| `QLabel`, `QLineEdit`, `QTextEdit` | `Expanding` | `Preferred` (label) / `Expanding` (text edit) |
| `QPushButton`, `QToolButton` | `Preferred` or `Minimum` | `Fixed` |
| `QGroupBox`, `QFrame`, container `QWidget` | `Expanding` | `Expanding` |
| `QListWidget`, `QTableView`, `QTreeView` | `Expanding` | `Expanding` |
| `QScrollArea` | `Expanding` | `Expanding` |

---

## Rule 5 — Spacing Consistency

**Severity: WARNING**

All `setContentsMargins` and `setSpacing` values must use tokens from the spacing system
(`SPACING_XS` … `SPACING_2XL`).  Hardcoded integer literals are a violation.

**Required fix**: Replace literal with the semantically closest token.

---

## Rule 6 — Nesting Depth Limit

**Severity: WARNING**

Layout nesting depth > 4 should trigger a flattening pass: merge redundant container widgets
that only hold a single child layout with no additional styling purpose.

---

## Rule 7 — No Inline Styles

**Severity: ERROR**

Widgets must not carry inline `setStyleSheet()` calls.  All styling is compiled centrally
by the ThemeManager.  The only exception is dynamic property-based styling
(e.g. `setProperty("error", True)` + a stylesheet selector matching `[error="true"]`).
