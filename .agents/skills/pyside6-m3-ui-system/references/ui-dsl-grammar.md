# UI DSL Grammar — Intermediate Representation

When converting natural language to UI code, first produce a structured tree
in this DSL format before generating Python code.  This ensures the agent can
validate the structure independently of code generation.

---

## Grammar

```
ui          := Page(name) '{' section+ '}'
section     := Section(name) '{' widget+ '}'
widget      := container | leaf
container   := Row | Column | Grid | Form | Group | ScrollArea '{' widget+ '}'
leaf        := Label(text)
             | Button(text)
             | Input(placeholder) [type]
             | Checkbox(text)
             | Combo(label, items)
             | List(items)
             | Table(headers)
             | Spacer
             | Divider
             | Image(path)
```

---

## Example

Natural language: *"Create a settings page with sidebar navigation and a form area."*

```
Page("Settings"):
  Row:
    Column("sidebar", width=200):
      Button("General")
      Button("Advanced")
      Spacer
    ScrollArea:
      Form:
        Section("Appearance"):
          Combo("Theme", ["Light", "Dark"])
          Combo("Font size", ["Small", "Medium", "Large"])
        Section("Behaviour"):
          Checkbox("Auto-save")
          Checkbox("Check for updates")
```

---

## Layout semantics

| DSL node | PySide6 layout | Notes |
|---|---|---|
| `Row` | `QHBoxLayout` | Horizontal arrangement |
| `Column` | `QVBoxLayout` | Vertical arrangement |
| `Grid` | `QGridLayout` | 2D grid; `row`, `col` attrs on children |
| `Form` | `QFormLayout` | Label–widget pairs |
| `Group` | `QGroupBox` | Bordered section with title |
| `ScrollArea` | `QScrollArea` | Scrollable container |

---

## Validation rules applied to DSL

Before code generation, the DSL tree must pass:

1. Every container node has ≥ 1 child OR is explicitly marked `placeholder`.
2. No leaf widget appears outside a layout container.
3. `Grid` children specify `row` and `col` attributes.
4. `Form` children are pairs: label-like then input-like.
5. Nesting depth ≤ 4 (warn if exceeded).
