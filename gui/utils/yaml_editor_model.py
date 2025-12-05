# yaml_editor_model.py — Business logic layer (no GUI dependencies)
# Handles data validation, serialization, and YAML I/O

import yaml
from pathlib import Path
from typing import Dict, Any, Optional, Callable
from .yaml_editor_config import DEFAULTS, EXAMPLE_MODELS, EXAMPLE_PINS


class ValidationError(Exception):
    """Raised when data validation fails."""
    pass


class FieldValidator:
    """Validates field values."""
    
    @staticmethod
    def validate_numeric(value: str, allow_scientific: bool = True) -> float:
        """Validate numeric input (int or float, optionally scientific notation)."""
        if not value or not value.strip():
            return None
        try:
            return float(value)
        except ValueError:
            raise ValidationError(f"Invalid numeric value: {value}")
    
    @staticmethod
    def validate_range(value: str, min_val: Optional[float] = None, 
                      max_val: Optional[float] = None) -> float:
        """Validate numeric value with optional min/max bounds."""
        num = FieldValidator.validate_numeric(value)
        if num is None:
            return None
        if min_val is not None and num < min_val:
            raise ValidationError(f"Value {num} is less than minimum {min_val}")
        if max_val is not None and num > max_val:
            raise ValidationError(f"Value {num} is greater than maximum {max_val}")
        return num
    
    @staticmethod
    def validate_required(value: str, field_name: str) -> str:
        """Validate that a required field is not empty."""
        if not value or not value.strip():
            raise ValidationError(f"Required field '{field_name}' is empty")
        return value.strip()


class YamlModel:
    """Business logic for YAML data management."""
    
    def __init__(self):
        self.data: Dict[str, Any] = {}
        self._init_defaults()
    
    def _init_defaults(self):
        """Initialize data with defaults."""
        self.data = self._get_defaults()
    
    @staticmethod
    def _get_defaults() -> Dict[str, Any]:
        """Create a new data dict with all default values."""
        data = {}
        global_defaults = {}
        
        for key, value in DEFAULTS.items():
            # Handle callable defaults (e.g., datetime.now())
            val = value() if callable(value) else value
            
            # Map global_defaults fields to nested structure
            if key in ['sim_time', 'r_load']:
                global_defaults[key] = val
            elif key.startswith('temp_'):
                if 'temp_range' not in global_defaults:
                    global_defaults['temp_range'] = {}
                global_defaults['temp_range'][key[5:]] = val  # typ, min, max
            elif key.startswith('voltage_'):
                if 'voltage_range' not in global_defaults:
                    global_defaults['voltage_range'] = {}
                global_defaults['voltage_range'][key[8:]] = val
            elif key.startswith('vil_'):
                if 'vil' not in global_defaults:
                    global_defaults['vil'] = {}
                global_defaults['vil'][key[4:]] = val
            elif key.startswith('vih_'):
                if 'vih' not in global_defaults:
                    global_defaults['vih'] = {}
                global_defaults['vih'][key[4:]] = val
            elif key.startswith('pullup_'):
                if 'pullup' not in global_defaults:
                    global_defaults['pullup'] = {}
                if val is not None:
                    global_defaults['pullup'][key[7:]] = val
            elif key.startswith('pulldown_'):
                if 'pulldown' not in global_defaults:
                    global_defaults['pulldown'] = {}
                if val is not None:
                    global_defaults['pulldown'][key[9:]] = val
            elif key.startswith('power_clamp_'):
                if 'power_clamp' not in global_defaults:
                    global_defaults['power_clamp'] = {}
                if val is not None:
                    global_defaults['power_clamp'][key[12:]] = val
            elif key.startswith('gnd_clamp_'):
                if 'gnd_clamp' not in global_defaults:
                    global_defaults['gnd_clamp'] = {}
                if val is not None:
                    global_defaults['gnd_clamp'][key[10:]] = val
            elif key.startswith('r_pkg_') or key.startswith('l_pkg_') or key.startswith('c_pkg_'):
                if 'pin_parasitics' not in global_defaults:
                    global_defaults['pin_parasitics'] = {}
                pkg_type = key[:5].upper() + '_pkg'  # R_pkg, L_pkg, C_pkg
                suffix = key[6:]  # typ, min, max
                if pkg_type not in global_defaults['pin_parasitics']:
                    global_defaults['pin_parasitics'][pkg_type] = {}
                if val is not None:
                    global_defaults['pin_parasitics'][pkg_type][suffix] = val
            else:
                # General fields
                data[key] = val
        
        # Add global_defaults to data
        if global_defaults:
            data['global_defaults'] = global_defaults
        
        return data
    
    def reset(self):
        """Reset all data to defaults."""
        self._init_defaults()
        self._add_example_models_and_pins()
    
    def _add_example_models_and_pins(self):
        """Add example models and pins."""
        self.data["models"] = [m.copy() for m in EXAMPLE_MODELS]
        
        components = [{
            "component": self.data.get("component", ""),
            "manufacturer": self.data.get("manufacturer", ""),
            "spiceFile": self.data.get("spiceFile", ""),
            "pList": [p.copy() for p in EXAMPLE_PINS]
        }]
        self.data["components"] = components
        
        self._build_global_defaults_structure()
    
    def _build_global_defaults_structure(self):
        """Build the nested global_defaults structure."""
        def clean_value(val):
            """Convert empty strings, None, and NaN to None; keep valid numbers including 0."""
            import math
            if val == "" or val is None:
                return None
            # Handle NaN (both float nan and string representations)
            if isinstance(val, float) and math.isnan(val):
                return None
            if isinstance(val, str) and val.lower() in ('nan', '.nan', 'na', 'n/a'):
                return None
            return val
        
        def build_tmm_dict(typ_key, min_key, max_key):
            """Build typ/min/max dict, omitting if all values are empty."""
            typ = clean_value(self.data.get(typ_key))
            min_val = clean_value(self.data.get(min_key))
            max_val = clean_value(self.data.get(max_key))
            
            # If all values are None/empty, return None to omit the entire section
            if typ is None and min_val is None and max_val is None:
                return None
            
            # Otherwise return dict with cleaned values
            return {
                "typ": typ,
                "min": min_val,
                "max": max_val
            }
        
        gd = {
            "sim_time": clean_value(self.data.get("sim_time")),
            "r_load": clean_value(self.data.get("r_load")),
            "temp_range": build_tmm_dict("temp_typ", "temp_min", "temp_max"),
            "voltage_range": build_tmm_dict("voltage_typ", "voltage_min", "voltage_max"),
            "pullup_ref": build_tmm_dict("pullup_typ", "pullup_min", "pullup_max"),
            "pulldown_ref": build_tmm_dict("pulldown_typ", "pulldown_min", "pulldown_max"),
            "power_clamp_ref": build_tmm_dict("power_clamp_typ", "power_clamp_min", "power_clamp_max"),
            "gnd_clamp_ref": build_tmm_dict("gnd_clamp_typ", "gnd_clamp_min", "gnd_clamp_max"),
            "vil": build_tmm_dict("vil_typ", "vil_min", "vil_max"),
            "vih": build_tmm_dict("vih_typ", "vih_min", "vih_max"),
            "pin_parasitics": {
                "R_pkg": build_tmm_dict("r_pkg_typ", "r_pkg_min", "r_pkg_max"),
                "L_pkg": build_tmm_dict("l_pkg_typ", "l_pkg_min", "l_pkg_max"),
                "C_pkg": build_tmm_dict("c_pkg_typ", "c_pkg_min", "c_pkg_max"),
            }
        }
        
        # Remove None entries from top level (optional fields)
        gd = {k: v for k, v in gd.items() if v is not None}
        
        # Clean up pin_parasitics - remove None entries
        if "pin_parasitics" in gd:
            gd["pin_parasitics"] = {k: v for k, v in gd["pin_parasitics"].items() if v is not None}
            # If pin_parasitics is now empty, remove it entirely
            if not gd["pin_parasitics"]:
                del gd["pin_parasitics"]
        
        self.data["global_defaults"] = gd
    
    def load_from_dict(self, yaml_dict: Dict[str, Any]) -> None:
        """Load data from a dictionary (typically from YAML)."""
        if not isinstance(yaml_dict, dict):
            raise ValidationError("Invalid data format: expected dictionary")
        
        self.data = yaml_dict.copy()
    
    def load_from_file(self, filepath: str) -> None:
        """Load YAML file into model."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            if data is None:
                raise ValidationError("YAML file is empty")
            self.load_from_dict(data)
        except yaml.YAMLError as e:
            raise ValidationError(f"YAML parsing error: {e}")
        except IOError as e:
            raise ValidationError(f"Cannot read file: {e}")
    
    def save_to_file(self, filepath: str) -> None:
        """Save model data to YAML file."""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                yaml.dump(self.data, f, sort_keys=False, 
                         default_flow_style=False, indent=2, allow_unicode=True)
        except IOError as e:
            raise ValidationError(f"Cannot write file: {e}")
    
    def get_data(self) -> Dict[str, Any]:
        """Get a copy of the current data."""
        return self.data.copy()
    
    def set_field(self, key: str, value: Any) -> None:
        """Set a field value in the data."""
        self.data[key] = value
    
    def get_field(self, key: str, default: Any = None) -> Any:
        """Get a field value from the data."""
        return self.data.get(key, default)
    
    def update_models(self, models: list) -> None:
        """Update the models list."""
        self.data["models"] = models
    
    def update_pins(self, pins: list, component_idx: int = 0) -> None:
        """Update the pins for a component."""
        if "components" not in self.data:
            self.data["components"] = [{"pList": []}]
        if len(self.data["components"]) <= component_idx:
            self.data["components"].append({"pList": []})
        self.data["components"][component_idx]["pList"] = pins
    
    def get_models(self) -> list:
        """Get the models list."""
        return self.data.get("models", [])
    
    def get_pins(self, component_idx: int = 0) -> list:
        """Get the pins for a component."""
        components = self.data.get("components", [{}])
        if len(components) > component_idx:
            return components[component_idx].get("pList", [])
        return []
    
    def validate(self) -> list:
        """Validate all data. Returns list of validation errors (empty if valid)."""
        errors = []
        
        # Check required fields
        required_fields = ["component", "manufacturer", "file_name"]
        for field in required_fields:
            if not self.data.get(field):
                errors.append(f"Required field '{field}' is empty")
        
        # Validate numeric fields
        numeric_fields = {
            "sim_time": (0, float('inf')),
            "r_load": (0, float('inf')),
        }
        for field, (min_val, max_val) in numeric_fields.items():
            if field in self.data and self.data[field]:
                try:
                    val = float(self.data[field])
                    if val < min_val or val > max_val:
                        errors.append(f"Field '{field}' out of range: {val}")
                except (ValueError, TypeError):
                    errors.append(f"Field '{field}' is not numeric: {self.data[field]}")
        
        return errors
