# yaml_editor_model.py — Business logic layer (no GUI dependencies)
# Handles data validation, serialization, and YAML I/O

import yaml
from pathlib import Path
from typing import Dict, Any, Optional, Callable
from yaml_editor_config import DEFAULTS, EXAMPLE_MODELS, EXAMPLE_PINS


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
        for key, value in DEFAULTS.items():
            # Handle callable defaults (e.g., datetime.now())
            data[key] = value() if callable(value) else value
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
        gd = {
            "sim_time": self.data.get("sim_time"),
            "r_load": self.data.get("r_load"),
            "temp_range": {
                "typ": self.data.get("temp_typ"),
                "min": self.data.get("temp_min"),
                "max": self.data.get("temp_max")
            },
            "voltage_range": {
                "typ": self.data.get("voltage_typ"),
                "min": self.data.get("voltage_min"),
                "max": self.data.get("voltage_max")
            },
            "pullup_ref": {
                "typ": self.data.get("pullup_typ"),
                "min": self.data.get("pullup_min"),
                "max": self.data.get("pullup_max")
            },
            "pulldown_ref": {
                "typ": self.data.get("pulldown_typ"),
                "min": self.data.get("pulldown_min"),
                "max": self.data.get("pulldown_max")
            },
            "power_clamp_ref": {
                "typ": self.data.get("power_clamp_typ"),
                "min": self.data.get("power_clamp_min"),
                "max": self.data.get("power_clamp_max")
            },
            "gnd_clamp_ref": {
                "typ": self.data.get("gnd_clamp_typ"),
                "min": self.data.get("gnd_clamp_min"),
                "max": self.data.get("gnd_clamp_max")
            },
            "vil": {
                "typ": self.data.get("vil_typ"),
                "min": self.data.get("vil_min"),
                "max": self.data.get("vil_max")
            },
            "vih": {
                "typ": self.data.get("vih_typ"),
                "min": self.data.get("vih_min"),
                "max": self.data.get("vih_max")
            },
            "pin_parasitics": {
                "R_pkg": {
                    "typ": self.data.get("r_pkg_typ"),
                    "min": self.data.get("r_pkg_min"),
                    "max": self.data.get("r_pkg_max")
                },
                "L_pkg": {
                    "typ": self.data.get("l_pkg_typ"),
                    "min": self.data.get("l_pkg_min"),
                    "max": self.data.get("l_pkg_max")
                },
                "C_pkg": {
                    "typ": self.data.get("c_pkg_typ"),
                    "min": self.data.get("c_pkg_min"),
                    "max": self.data.get("c_pkg_max")
                },
            }
        }
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
