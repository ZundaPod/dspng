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
container   := Row | Column | Grid | Form | Group | ScrollArea | TabView '{' widget+ '}'
leaf        := Label(text)
             | Button(text)
             | Input(placeholder) [type]
             | TextEdit(placeholder)
             | Checkbox(text)
             | Combo(label, items)
             | SpinBox(label, min, max, step)
             | Slider(label, min, max)
             | Progress(label)
             | RadioGroup(label, options)
             | List(items)
             | Table(headers)
             | Spacer
             | Divider
             | Image(path)
```

---

## Leaf widget attributes (optional)

| Attribute   | Applies to          | Example                     |
|-------------|---------------------|-----------------------------|
| `width`     | any container       | `Column(width=200)`         |
| `height`    | any container       | `Row(height=48)`            |
| `stretch`   | layout children     | `Button("OK", stretch=0)`   |
| `tooltip`   | any leaf            | `Input("Name", tooltip="Full name")` |
| `enabled`   | any leaf            | `Button("Save", enabled=false)` |

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

| DSL node    | PySide6 widget / layout | Notes                                      |
|-------------|--------------------------|--------------------------------------------|
| `Row`       | `QHBoxLayout`            | Horizontal arrangement                     |
| `Column`    | `QVBoxLayout`            | Vertical arrangement; default for Page body|
| `Grid`      | `QGridLayout`            | Children specify `row` and `col`           |
| `Form`      | `QFormLayout`            | Label–widget pairs; `Section` → `QGroupBox`|
| `Group`     | `QGroupBox`              | Bordered section with title                |
| `ScrollArea`| `QScrollArea`            | Must enable `setWidgetResizable(True)`     |
| `TabView`   | `QTabWidget`             | Children are named tabs                    |

---

## Validation rules applied to DSL

Before code generation, the DSL tree must pass:

1. Every container node has ≥ 1 child OR is explicitly marked `placeholder`.
2. No leaf widget appears outside a layout container (Page itself is a container).
3. `Grid` children specify `row` and `col` attributes.
4. `Form` children are pairs: label-like then input-like.
5. Nesting depth ≤ 4 (warn if exceeded; flatten redundant single-child containers).
