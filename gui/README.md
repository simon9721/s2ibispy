# s2ibispy GUI Documentation

A modern graphical interface for IBIS model generation from SPICE netlists.

![GUI Overview](../resources/icons/s2ibispy.png)

---

## Overview

The s2ibispy GUI provides a unified interface combining file loading, YAML configuration editing, model/pin management, and simulation controls in one streamlined window.

**Key Features:**
- Load `.s2i` or `.yaml` configuration files
- Edit all IBIS parameters with proper widget types (dropdowns, checkboxes)
- Manage models and pins with inline editing
- Real-time simulation with progress bar and abort capability
- Integrated waveform plotting and correlation analysis
- Built-in ibischk validation with auto-detection

---

## Getting Started

### Launch the GUI

```powershell
python gui_main.py
```

The GUI will open with default values pre-populated in all fields.

### Basic Workflow

1. **Load a file**: Choose `.yaml` or `.s2i` from the file type dropdown
2. **Configure settings**: Edit general settings, global defaults, models, and pins
3. **Set paths**: Specify output directory and optional ibischk path
4. **Start conversion**: Click "Start Conversion" to generate IBIS model
5. **View results**: Check logs, plots, and generated files

---

## Main Entry Tab

The main entry tab combines all essential configuration in a single scrollable view.

### File Loading Section

**Input Type Selection:**
- **YAML**: Modern configuration format with full feature support
- **.s2i**: Legacy format (auto-converts to YAML internally)

**File Browser:**
- Click "Browse" to select your input file
- File path shown in entry field
- Recently loaded files preserved in session

### General Settings

**Field Types:**
- **IBIS Version**: Dropdown menu (4.0, 4.1, 4.2, 5.0, 5.1, 6.0, 6.1, 7.0)
- **File Rev**: Dropdown menu (0, 0.1, 0.2, 1.0, 1.1, 2.0)
- **File Name**: Text entry (required) - output .ibs filename
- **Date**: Auto-populated with current date
- **Copyright**: Your organization name
- **Source**: Origin of the data
- **Notes**: Description of the model (supports multi-line)
- **Disclaimer**: Legal text
- **Spice Type**: Text entry (hspice, spectre, eldo)

**Note**: Iterate and Cleanup settings are in the Simulation Options section (not duplicated here).

### Component Section

**Required Fields:**
- **Component Name**: Device part number (e.g., SN74LVC1G07)
- **Manufacturer**: Company name (e.g., Texas Instruments)
- **SPICE File**: Path to SPICE netlist with Browse button

### Global Defaults

Organized in logical groups for easy configuration. All fields support typ/min/max corner values.

**Simulation:**
- **Sim Time**: Simulation duration (e.g., 6e-9)
- **Rload**: Load resistance in Ω (typically 50)

**Temperature Range [°C]:**
- Typ/Min/Max values
- Note: For CMOS, min=highest temp (slow), max=lowest temp (fast)

**Voltage Range [V]:**
- Typ/Min/Max supply voltage values

**Pullup/Pulldown/Clamp References [V]:**
- Optional reference voltages for different driver types
- Leave blank if not applicable

**VIL/VIH [V] - Stimulus:**
- Low and high stimulus voltages for SPICE simulation
- These are input drive voltages, not logic thresholds
- Typ/Min/Max for each

**Pin Parasitics:**
- **R_pkg**: Package resistance (Ω)
- **L_pkg**: Package inductance (H)
- **C_pkg**: Package capacitance (F)
- Each with typ/min/max values

**Empty Fields:** Only non-empty fields are saved to YAML. Default values shown in UI won't be written unless you explicitly fill them.

### Simulation Options

**SPICE Type:** Dropdown (hspice, spectre, eldo)

**Checkboxes:**
- **Reuse existing SPICE data (--iterate)**: Skip re-running simulations if output files exist
- **Cleanup intermediate files**: Delete .spi, .tr0, .mt0 files after conversion
- **Verbose logging**: Enable detailed debug output

### Models Section

Treeview with columns: **Name | Type | Enable | Polarity | NoModel**

**Model Types:**
- Input, Output, I/O, 3-state
- Open_drain, Open_sink, Open_source
- I/O_Open_drain, I/O_Open_sink, I/O_Open_source
- Series, Series_switch, Terminator
- Input_ECL, Output_ECL, I/O_ECL

**Editing Models:**
1. **Double-click** any cell to edit inline
2. **Edit Model** button: Opens detailed dialog with:
   - Name (required)
   - Type (dropdown)
   - Enable pin name
   - Polarity (Non-Inverting/Inverting)
   - **NoModel checkbox**: Check to skip simulation for this model
   - Model files (typ/min/max) with Browse buttons

**NoModel Flag:**
- Marks models that should not be simulated
- Used for dummy/placeholder pins
- Alternative to using reserved names (DUMMY, NOMODEL, GND, POWER, NC)
- Shows "Yes" in NoModel column when set

**Buttons:**
- **Add Model**: Create new model entry
- **Edit Model**: Open detailed editor for selected model
- **Delete Selected**: Remove selected model(s)

### Pins Section

Treeview with columns: **Pin | Signal | Model | Input Pin | Enable Pin**

**Editing Pins:**
1. **Double-click** any cell to edit inline
2. Right-click for context menu (if implemented)

**Pin Assignment:**
- **Pin**: Pin number or name
- **Signal**: Signal name in schematic
- **Model**: Must match a model name from Models section
- **Input Pin**: For outputs, specify which pin drives it
- **Enable Pin**: For tri-state models, specify enable pin

**Reserved Model Names:**
- **POWER**: Power supply pin (no simulation)
- **GND**: Ground pin (no simulation)
- **NC**: No connect pin (no simulation)
- **DUMMY/NOMODEL**: Placeholder pins (no simulation)

**Buttons:**
- **Add Pin**: Create new pin entry
- **Edit Pin**: Modify selected pin (future enhancement)
- **Delete Selected**: Remove selected pin(s)

---

## Output & Validation Section

**Output Directory:**
- Browse button to select output folder
- Default: `./out` in current directory
- Generated files: `.ibs`, `.sp` (correlation), `.ibischk_log.txt`

**ibischk Path:**
- Path to ibischk7.exe for validation
- **Auto-detection**: Checks `resources/ibischk/ibischk7.exe` on startup
- Optional: Leave blank to skip validation

---

## Simulation Controls

**Start Conversion Button:**
- Launches IBIS generation process
- Button changes to "Abort Simulation" during run
- Shows animated progress bar

**Progress Feedback:**
- Real-time log output in scrollable text area
- Color-coded messages:
  - INFO: Standard messages
  - WARNING: Non-critical issues (orange)
  - ERROR: Problems encountered (red)
  - SUCCESS: Completion messages (green)

**Abort Capability:**
- Click "Abort Simulation" to terminate running process
- Cleans up temporary files
- Safe to restart immediately

---

## Other Tabs

### Plots Tab
- Waveform visualization using matplotlib
- Automatic plot generation from simulation results
- Zoom, pan, save capabilities

### Correlation Tab
- SPICE vs IBIS comparison
- Overlay plots showing model accuracy
- Correlation deck generation and execution

### IBIS Viewer Tab
- Generated IBIS file preview
- Syntax highlighting
- Search functionality

---

## YAML Configuration Format

The GUI supports modern YAML configuration with nested structures.

### General Fields (Flat)
```yaml
ibis_version: '6.0'
file_name: my_model.ibs
file_rev: '1.0'
date: November 28, 2025
copyright: My Company
spice_type: hspice
iterate: '1'
cleanup: '0'
```

### Global Defaults (Nested)
```yaml
global_defaults:
  sim_time: 6e-9
  r_load: '50'
  
  temp_range:
    typ: '27'
    min: '100'
    max: '0'
  
  voltage_range:
    typ: '3.3'
    min: '3.0'
    max: '3.6'
  
  vil:
    typ: '0.8'
    min: '0'
    max: '0'
  
  vih:
    typ: '2.0'
    min: '3.0'
    max: '3.6'
  
  pin_parasitics:
    R_pkg:
      typ: '0.002'
      min: '0.001'
      max: '0.004'
    L_pkg:
      typ: 2e-10
      min: 1e-10
      max: 4e-10
    C_pkg:
      typ: 2e-12
      min: 1e-12
      max: 4e-12
```

### Models
```yaml
models:
- name: driver
  type: I/O
  enable: oe
  polarity: Non-Inverting
  modelFile: path/to/hspice.mod
  rising_waveforms:
  - R_fixture: 50
    V_fixture: 0
  - R_fixture: 50
    V_fixture: 3.3
  falling_waveforms:
  - R_fixture: 50
    V_fixture: 0
  - R_fixture: 50
    V_fixture: 3.3

- name: dummy
  type: Input
  nomodel: true
```

### Component and Pins
```yaml
components:
- component: MCM Driver 1
  manufacturer: MegaFLOPS Inc.
  spiceFile: /path/to/buffer.sp
  pList:
  - pinName: out
    signalName: out
    modelName: driver
    inputPin: in
    enablePin: oe
  - pinName: in
    signalName: in
    modelName: dummy
  - pinName: vdd
    signalName: vdd
    modelName: POWER
  - pinName: gnd
    signalName: gnd
    modelName: GND
```

---

## ibischk Integration

### Bundled Executable

s2ibispy includes ibischk7.exe integration:

**Location:** `resources/ibischk/ibischk7.exe`

**Auto-detection:**
- GUI checks this location on startup
- If found, path is automatically populated
- Log message: "Auto-detected ibischk7 → ibischk7.exe"

### Adding Your Own ibischk

1. Download ibischk from IBIS Open Forum: https://ibis.org/tools.htm
2. Place in `resources/ibischk/` directory (recommended)
3. Or use Browse button to select any location
4. Supported versions: ibischk7 (64-bit recommended)

### Validation Output

When ibischk path is set:
- Automatic validation after IBIS generation
- Text log: `output/model.ibischk_log.txt`
- JSON report: `output/model.json` (structured results)
- Error/warning counts in GUI log

---

## Widget Types Reference

The GUI uses appropriate widget types for different field categories:

| Widget Type | Fields | Behavior |
|-------------|--------|----------|
| **Dropdown** | IBIS Version, File Rev, SPICE Type, Model Type, Polarity | Select from predefined options |
| **Checkbox** | Iterate, Cleanup, Verbose, NoModel | Boolean on/off |
| **Text Entry** | File Name, Copyright, Component, Manufacturer | Free-form text |
| **File Browser** | Input File, SPICE File, Model Files, Output Dir, ibischk | Browse button + text entry |
| **Treeview** | Models, Pins | Tabular editing with double-click |

**Data Binding:**
- Dropdowns use StringVar for value storage
- Checkboxes use BooleanVar internally, saved as strings ("0"/"1")
- Text entries support validation (future enhancement)

---

## Tips & Tricks

### Keyboard Shortcuts
- **Double-click**: Edit treeview cells inline
- **Tab**: Navigate between fields
- **Enter**: Accept inline edits

### Data Management
- **Save Often**: Use File > Save to write YAML frequently
- **Blank Fields**: Empty fields won't be saved to YAML (keeps files clean)
- **Preserved Fields**: Model files, waveforms, and other complex data are preserved even if not shown in treeview

### Model Names
- Use descriptive names (e.g., `io_buffer`, `output_driver`)
- Reserved names skip simulation: POWER, GND, NC, DUMMY, NOMODEL
- Case-insensitive matching for reserved names

### SPICE File Paths
- Use absolute paths for reliability
- GUI automatically resolves relative paths when loading
- Browse button helps avoid typos

### Debugging
- Enable "Verbose logging" for detailed output
- Check log area for warnings about missing files
- Use ibischk to catch IBIS format issues

---

## Architecture Notes

### File Organization

```
gui/
├── __init__.py
├── app.py              # Main application class
├── tabs/               # Tab implementations
│   ├── __init__.py
│   ├── main_entry_tab.py    # Unified configuration tab
│   ├── correlation_tab.py   # Correlation analysis
│   ├── ibis_viewer_tab.py   # IBIS file viewer
│   ├── plots_tab.py         # Waveform plots
│   └── __pycache__/
├── utils/              # GUI utilities
│   ├── __init__.py
│   ├── matplotlib_fix.py    # Plot backend setup
│   ├── session.py           # Session management
│   ├── splash.py            # Splash screen
│   ├── tr0_reader.py        # SPICE output parser
│   ├── yaml_editor_config.py   # UI schema definitions
│   ├── yaml_editor_model.py    # YAML data model
│   ├── s2i_to_yaml.py          # .s2i converter
│   ├── parse_netlist.py        # SPICE netlist parser
│   └── __pycache__/
└── README.md           # This file
```

### Data Flow

1. **Load File** → Parser (`.s2i` or YAML) → YamlModel
2. **YamlModel** ↔ **UI Widgets** (bidirectional binding)
3. **Start Conversion** → Collect data → CLI entry point
4. **CLI** → Core analysis → IBIS generation
5. **Results** → GUI tabs (plots, viewer, correlation)

### Widget Registry

The GUI maintains two widget registries:
- `self.entries{}`: General settings and component fields
- `self.global_entries{}`: Global defaults fields

Dropdown/checkbox widgets store:
- `entries[key]`: The widget itself
- `entries[f"{key}_var"]`: The StringVar/BooleanVar

---

## Troubleshooting

### Common Issues

**Problem:** "Python was not found"
- **Solution:** Ensure Python is in PATH or use full path: `C:\Path\to\python.exe gui_main.py`

**Problem:** Dropdown values not saving
- **Solution:** This was a known issue, now fixed. Update to latest version.

**Problem:** Global defaults not showing
- **Solution:** Ensure YAML has nested structure (see format above). Fixed in recent update.

**Problem:** ibischk not found
- **Solution:** Place `ibischk7.exe` in `resources/ibischk/` or use Browse button

**Problem:** Model shows "I/O" type incorrectly
- **Solution:** Check .s2i file has `[Model type]` line. NoModel models default to I/O (harmless).

**Problem:** Simulation hangs
- **Solution:** Click "Abort Simulation" button. Check SPICE file syntax.

### Reporting Issues

When reporting bugs, please include:
1. GUI version (check main README.md)
2. Python version: `python --version`
3. Input file (.s2i or .yaml)
4. Log output (copy from log area)
5. Expected vs actual behavior

GitHub Issues: https://github.com/simon9721/s2ibispy/issues

---

## Future Enhancements

Planned improvements:
- [ ] Undo/redo for model and pin edits
- [ ] Drag-and-drop file loading
- [ ] Pin mapping visualization
- [ ] Real-time field validation
- [ ] Recent files menu
- [ ] Export to different IBIS versions
- [ ] Batch processing multiple models
- [ ] Integrated SPICE netlist editor

---

## Contributing

GUI contributions welcome! Areas of interest:
- Improved plotting capabilities
- Better treeview editing (context menus, copy/paste)
- Field validation and tooltips
- Dark mode theme
- Keyboard shortcuts
- Accessibility improvements

See main `README.md` for contribution guidelines.

---

**Last Updated:** November 28, 2025
