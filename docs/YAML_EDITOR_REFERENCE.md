# YAML Editor Quick Reference

## File Structure

```
s2ibispy_new/
├── yaml_editor.py                  # Main GUI application (refactored)
├── yaml_editor_config.py           # Configuration & schema (NEW)
├── yaml_editor_model.py            # Business logic model (NEW)
└── REFACTORING_NOTES.md           # Full documentation (NEW)
```

## Class Reference

### yaml_editor_model.YamlModel
**Business logic for YAML data management (no GUI dependencies)**

```python
model = YamlModel()

# Data operations
model.reset()                              # Reset to defaults
model.load_from_file(path)                 # Load from YAML
model.save_to_file(path)                   # Save to YAML
model.load_from_dict(data)                 # Load from dict

# Field access
model.get_data()                           # Get all data
model.set_field(key, value)                # Set single field
model.get_field(key, default=None)         # Get single field

# Models & pins
model.update_models(models_list)           # Update models
model.update_pins(pins_list)               # Update pins
model.get_models()                         # Get models
model.get_pins()                           # Get pins

# Validation
errors = model.validate()                  # Returns list of error strings
```

### yaml_editor_model.FieldValidator
**Static validation methods**

```python
FieldValidator.validate_numeric(value)              # Float with scientific notation
FieldValidator.validate_range(value, min, max)      # Numeric with bounds
FieldValidator.validate_required(value, field_name) # Non-empty string
```

### yaml_editor.S2IbispyEditor
**Main GUI application**

```python
app = S2IbispyEditor(root)

# Public methods
app.new_file()        # Create new file
app.open_yaml()       # Open YAML file
app.save()            # Save current file
app.save_as()         # Save with new name
```

## Configuration

### UI_SCHEMA (yaml_editor_config.py)
Define form structure:
```python
UI_SCHEMA = {
    "section_name": {
        "title": "Display Title",
        "fields": [
            ("Label", "key_name", "Tooltip text"),
            ...
        ],
        "cols": 3  # optional columns
    },
    ...
}
```

### DEFAULTS (yaml_editor_config.py)
Set default values:
```python
DEFAULTS = {
    "field_key": "default_value",
    "callable_field": lambda: datetime.now(),  # Callable for dynamic defaults
    ...
}
```

### COLORS & FONTS (yaml_editor_config.py)
Customize appearance:
```python
COLORS = {"log_bg": "#0d1117", "log_fg_info": "#d4d4d4", ...}
FONTS = {"title_large": ("Helvetica", 18, "bold"), ...}
```

## Adding New Fields

### 1. Add to yaml_editor_config.py

```python
# In UI_SCHEMA under appropriate section:
"fields": [
    ("New Field Label", "new_field_key", "Tooltip text"),
]

# In DEFAULTS:
DEFAULTS = {
    ...
    "new_field_key": "default_value",
}
```

### 2. No changes needed to yaml_editor.py or yaml_editor_model.py!

The schema-driven architecture automatically handles new fields.

## Adding a New Section

### 1. Add to UI_SCHEMA in yaml_editor_config.py

```python
UI_SCHEMA["my_section"] = {
    "title": "My Section",
    "fields": [
        ("Field 1", "field1", "Tooltip"),
        ("Field 2", "field2", "Tooltip"),
    ],
    "cols": 2
}
```

### 2. Call builder in _build_form() in yaml_editor.py

```python
def _build_form(self):
    # ... existing sections ...
    row = self._build_section(self.content, row, "my_section")
    row += 1
```

## Common Tasks

### Validate numeric input
```python
from yaml_editor_model import FieldValidator

try:
    value = FieldValidator.validate_numeric("3.14")
    bounded = FieldValidator.validate_range("50", 0, 100)
except ValidationError as e:
    print(f"Invalid: {e}")
```

### Work with data model (testing)
```python
from yaml_editor_model import YamlModel

model = YamlModel()
model.set_field("component", "TestIC")
model.set_field("sim_time", "1e-9")

errors = model.validate()
if not errors:
    model.save_to_file("test.yaml")
```

### Customize colors
```python
# In yaml_editor_config.py, modify COLORS dict:
COLORS = {
    "log_fg_success": "#00FF00",  # Change to neon green
    "tooltip_bg": "#FFFFCC",      # Change tooltip background
}
```

## Error Handling

```python
from yaml_editor_model import ValidationError, YamlModel

model = YamlModel()
try:
    model.load_from_file(path)
except ValidationError as e:
    print(f"Validation error: {e}")  # Specific error
except IOError as e:
    print(f"File error: {e}")        # File system error
```

## Testing (Examples)

```python
# test_yaml_editor_model.py
from yaml_editor_model import YamlModel, FieldValidator, ValidationError

def test_validate_numeric():
    assert FieldValidator.validate_numeric("3.14") == 3.14
    assert FieldValidator.validate_numeric("1e-9") == 1e-9

def test_model_reset():
    model = YamlModel()
    model.reset()
    assert len(model.get_models()) == 1
    assert len(model.get_pins()) == 3

def test_model_validation():
    model = YamlModel()
    model.set_field("component", "")  # Required field empty
    errors = model.validate()
    assert len(errors) > 0

def test_yaml_roundtrip():
    model = YamlModel()
    model.set_field("component", "TestIC")
    model.save_to_file("test.yaml")
    
    model2 = YamlModel()
    model2.load_from_file("test.yaml")
    assert model2.get_field("component") == "TestIC"
```

## Architecture Diagram

```
┌─────────────────────────────────────────────┐
│         yaml_editor.py (GUI Layer)          │
│  - S2IbispyEditor class                    │
│  - tkinter widgets & layout                │
│  - User event handling                      │
└────────────────┬────────────────────────────┘
                 │ imports & uses
┌────────────────▼────────────────────────────┐
│    yaml_editor_model.py (Business Logic)    │
│  - YamlModel class                         │
│  - FieldValidator class                    │
│  - YAML I/O & serialization                │
│  - Data validation                         │
│  - NO GUI dependencies                     │
└────────────────┬────────────────────────────┘
                 │ imports
┌────────────────▼────────────────────────────┐
│   yaml_editor_config.py (Configuration)    │
│  - UI_SCHEMA definitions                   │
│  - DEFAULTS values                         │
│  - COLORS & FONTS constants                │
│  - EDITOR_CONFIG settings                  │
│  - Pure data, no logic                     │
└─────────────────────────────────────────────┘
```

## Key Benefits of New Architecture

✓ **Testable** - Business logic has zero GUI dependencies
✓ **Maintainable** - Clear separation of concerns  
✓ **Extensible** - Add features without modifying core logic
✓ **Reusable** - Model can be used in CLI, API, or other UIs
✓ **Configurable** - Change behavior via config without coding
✓ **Robust** - Proper validation and error handling
