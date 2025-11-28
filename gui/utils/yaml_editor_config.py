# yaml_editor_config.py — Configuration and schema definitions
# All UI field definitions and defaults in one place for easy maintenance
#
# Field Format: (label, key, tooltip, required, widget_type, options)
#   - label: Display text for the field
#   - key: Data dictionary key
#   - tooltip: Help text (can be empty string or None)
#   - required: Boolean - True for required fields (marked with *)
#   - widget_type: "entry" (default), "dropdown", "checkbox"
#   - options: For dropdown - list of values; For checkbox - (checked_value, unchecked_value)

from datetime import datetime

# Widget type constants
WIDGET_ENTRY = "entry"
WIDGET_DROPDOWN = "dropdown"
WIDGET_CHECKBOX = "checkbox"
WIDGET_FILE_BROWSER = "file_browser"

# UI Schema — defines all form fields, grouping, and layout
UI_SCHEMA = {
    "general_settings": {
        "title": "General Settings",
        "fields": [
            ("IBIS Version", "ibis_version", "Select IBIS version", False, WIDGET_DROPDOWN, ["4.0", "4.1", "4.2", "5.0", "5.1", "6.0", "6.1", "7.0"]),
            ("File Name", "file_name", "Output .ibs file", True, WIDGET_ENTRY, None),
            ("File Rev", "file_rev", "File revision", False, WIDGET_DROPDOWN, ["0", "0.1", "0.2", "1.0", "1.1", "2.0"]),
            ("Date", "date", "Auto-filled", False, WIDGET_ENTRY, None),
            ("Copyright", "copyright", "Your lab/company", False, WIDGET_ENTRY, None),
            ("Source", "source", "Origin of the data", False, WIDGET_ENTRY, None),
            ("Notes", "notes", "Be honest about limitations", False, WIDGET_ENTRY, None),
            ("Disclaimer", "disclaimer", "Legal text", False, WIDGET_ENTRY, None),
            ("Spice Type", "spice_type", "hspice, spectre, ltspice...", False, WIDGET_ENTRY, None),
            ("Iterate", "iterate", "Enable iterative solving", False, WIDGET_CHECKBOX, ("1", "0")),
            ("Cleanup", "cleanup", "Delete intermediate SPICE files", False, WIDGET_CHECKBOX, ("1", "0"))
        ],
        "cols": 3  # 3 columns layout
    },
    
    "component": {
        "title": "Component",
        "fields": [
            ("Component Name", "component", "e.g. SN74LVC1G07", True, WIDGET_ENTRY, None),
            ("Manufacturer", "manufacturer", "e.g. Texas Instruments", True, WIDGET_ENTRY, None),
            ("SPICE File", "spiceFile", "Path to SPICE netlist", True, WIDGET_FILE_BROWSER, None)
        ],
        "cols": 1
    },
    
    # NOTE: VIL/VIH here are STIMULUS voltages for SPICE simulation (driving inputs).
    # VINL/VINH (input threshold voltages) are per-model parameters, not in global_defaults.
    # See s2ibis3.txt for details on the distinction.
    "global_defaults": {
        "title": "Global Defaults",
        "groups": [
            ("Simulation", [
                ("Sim Time (s)", "sim_time", "e.g. 6e-9", True),
                ("Rload (Ω)", "r_load", "Usually 50", True)
            ]),
            ("Temperature Range [°C] *", [
                ("Typ", "temp_typ", None, True),
                ("Min", "temp_min", None, True),
                ("Max", "temp_max", None, True)
            ]),
            ("Voltage Range [V] *", [
                ("Typ", "voltage_typ", None, True),
                ("Min", "voltage_min", None, True),
                ("Max", "voltage_max", None, True)
            ]),
            ("Pullup Ref [V]", [
                ("Typ", "pullup_typ", None, False),
                ("Min", "pullup_min", None, False),
                ("Max", "pullup_max", None, False)
            ]),
            ("Pulldown Ref [V]", [
                ("Typ", "pulldown_typ", None, False),
                ("Min", "pulldown_min", None, False),
                ("Max", "pulldown_max", None, False)
            ]),
            ("Power Clamp Ref [V]", [
                ("Typ", "power_clamp_typ", None, False),
                ("Min", "power_clamp_min", None, False),
                ("Max", "power_clamp_max", None, False)
            ]),
            ("GND Clamp Ref [V]", [
                ("Typ", "gnd_clamp_typ", None, False),
                ("Min", "gnd_clamp_min", None, False),
                ("Max", "gnd_clamp_max", None, False)
            ]),
            ("VIL [V] - Stimulus", [
                ("Typ", "vil_typ", "Low stimulus voltage (not threshold)", False),
                ("Min", "vil_min", None, False),
                ("Max", "vil_max", None, False)
            ]),
            ("VIH [V] - Stimulus", [
                ("Typ", "vih_typ", "High stimulus voltage (not threshold)", False),
                ("Min", "vih_min", None, False),
                ("Max", "vih_max", None, False)
            ]),
            ("Pin Parasitics", [
                ("R_pkg typ (Ω)", "r_pkg_typ", None, False),
                ("min", "r_pkg_min", None, False),
                ("max", "r_pkg_max", None, False),
                ("L_pkg typ (H)", "l_pkg_typ", None, False),
                ("min", "l_pkg_min", None, False),
                ("max", "l_pkg_max", None, False),
                ("C_pkg typ (F)", "c_pkg_typ", None, False),
                ("min", "c_pkg_min", None, False),
                ("max", "c_pkg_max", None, False),
            ]),
        ]
    },
    
    "models": {
        "title": "Models",
        "columns": ("Name", "Type", "Enable", "Polarity", "NoModel"),
        "height": 8
    },
    
    "pins": {
        "title": "Pins",
        "columns": ("Pin", "Signal", "Model", "Input Pin", "Enable Pin"),
        "height": 12
    }
}

# Default values for all fields
DEFAULTS = {
    # General settings
    "ibis_version": "5.1",
    "file_name": "my_model.ibs",
    "file_rev": "0.1",
    "date": lambda: datetime.now().strftime("%B %d, %Y"),
    "copyright": "© 2025 Your Lab",
    "spice_type": "hspice",
    "iterate": "1",
    "cleanup": "0",
    
    # Multiline
    "source": "Netlist generated by Grok",
    "notes": "I really wouldn't try to use this driver. It's really bad.",
    "disclaimer": "This file is only for demonstration purposes.",
    
    # Component
    "component": "FastBuffer",
    "manufacturer": "YourCompany",
    "spiceFile": "",
    
    # Global defaults (aligned with s2i_constants.py)
    "sim_time": "10e-9",  # SIM_TIME_DEFAULT
    "r_load": "50",       # RLOAD_DEFAULT
    "temp_typ": "27",     # TEMP_TYP_DEFAULT
    "temp_min": "100",    # TEMP_MIN_DEFAULT (intentionally high for corner case)
    "temp_max": "0",      # TEMP_MAX_DEFAULT (intentionally low for corner case)
    "voltage_typ": "5.0", # VOLTAGE_RANGE_TYP_DEFAULT
    "voltage_min": "4.5", # VOLTAGE_RANGE_MIN_DEFAULT
    "voltage_max": "5.5", # VOLTAGE_RANGE_MAX_DEFAULT
    "pullup_typ": "3.3",
    "pullup_min": None,
    "pullup_max": None,
    "pulldown_typ": "0",
    "pulldown_min": None,
    "pulldown_max": None,
    "power_clamp_typ": "3.3",
    "power_clamp_min": None,
    "power_clamp_max": None,
    "gnd_clamp_typ": "0",
    "gnd_clamp_min": None,
    "gnd_clamp_max": None,
    "vil_typ": "0.8",
    "vil_min": None,
    "vil_max": None,
    "vih_typ": "2.0",
    "vih_min": None,
    "vih_max": None,
    "r_pkg_typ": "0.2",
    "r_pkg_min": "0.1",
    "r_pkg_max": "0.4",
    "l_pkg_typ": "5e-9",
    "l_pkg_min": "3e-9",
    "l_pkg_max": "8e-9",
    "c_pkg_typ": "1e-12",
    "c_pkg_min": "0.5e-12",
    "c_pkg_max": "2e-12",
}

# Example data for new files
EXAMPLE_MODELS = [
    {"name": "buffer", "type": "I/O", "enable": "oe", "polarity": "Non-Inverting"}
]

EXAMPLE_PINS = [
    {"pinName": "1", "signalName": "pad", "modelName": "buffer", "inputPin": "in", "enablePin": "oe"},
    {"pinName": "2", "signalName": "vdd", "modelName": "POWER", "inputPin": "", "enablePin": ""},
    {"pinName": "3", "signalName": "vss", "modelName": "GND", "inputPin": "", "enablePin": ""},
]

# UI Styling constants
COLORS = {
    "tooltip_bg": "#ffffe0",
    "tooltip_fg": "#000000",
    "log_bg": "#0d1117",
    "log_fg_info": "#d4d4d4",
    "log_fg_success": "#00ff41",
    "log_fg_warning": "#ffaa00",
    "log_fg_error": "#ff5555",
}

FONTS = {
    "title_large": ("Helvetica", 18, "bold"),
    "title_medium": ("Helvetica", 16, "bold"),
    "title_small": ("Helvetica", 12, "bold"),
    "tooltip": ("Segoe UI", 9),
    "monospace": ("Consolas", 10),
}

# Editor configuration
EDITOR_CONFIG = {
    "window_width": 1560,
    "window_height": 1000,
    "min_width": 1200,
    "min_height": 800,
    "auto_backup_interval": 30000,  # 30 seconds in ms
    "log_height": 10,
}
