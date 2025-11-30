# s2ibispy — A Modern Python Implementation of s2ibis3

[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/downloads/)

[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

[![Work in Progress](https://img.shields.io/badge/status-work%20in%20progress-orange)](#status)


![S2IBISpy](resources//icons/s2ibispy.png)


`s2ibis3` was developed by North Carolina State University and has been a widely used reference tool for generating IBIS models from SPICE netlists. Written in Java, it has not received updates in many years.

**s2ibispy** is a new, independent implementation in modern Python. The goal is to provide a clean, maintainable, and extensible codebase while maintaining compatibility with existing `.s2i` configuration files and producing functionally equivalent IBIS output.

This project is **under active development** and requires extensive real-world validation.

---

### Quickstart (Windows PowerShell)

```powershell
# 1) Clone and enter the repo
git clone https://github.com/simon9721/s2ibispy.git
cd s2ibispy

# 2) Create and activate a virtual environment
python -m venv .venv
.venv\Scripts\activate

# 3) Install in editable mode (recommended for dev)
python -m pip install -U pip
pip install -e .

# 4) Run the tool (module form)
python -m s2ibispy tests/real_test.yaml --outdir tests/1127test --iterate 0 --cleanup 0

# Optional: include ibischk and correlation once paths are set
# python -m s2ibispy tests/real_test.yaml --outdir tests/1127test \
#   --iterate 0 --cleanup 0 --ibischk "C:\Path\to\ibischk7_64.exe" --correlate

# Alternative (backward compatible):
python main.py tests/real_test.yaml --outdir tests/1127test --iterate 0 --cleanup 0
```

Linux/macOS users: use the same steps but activate with `source .venv/bin/activate` and invoke `python -m s2ibispy ...` similarly.

---

### Templates and Data

- Packaged: The Jinja2 correlation template (`templates/compare_correlation.sp.j2`) and the example RLGC file (`Z50_406.lc3`) are bundled inside the package (`src/s2ibispy/templates/`, `src/s2ibispy/data/`).
- Loading: The tool loads packaged templates by default; if a `templates/` folder exists in the working directory, it will be used as a fallback/override.
- Override: Advanced users can pass an internal `template_dir` via the programmatic API; a CLI switch can be added if needed.

---

### Features (Current)

**Core Functionality:**
- Full `.s2i` file parsing with `[Include]` support and line continuations
- Modern YAML configuration format (recommended) with nested structure support
- Hierarchical default propagation (global → component → model)
- SPICE deck generation for HSPICE, Spectre, and Eldo
- VI curve, ramp, and waveform extraction
- Accurate IBIS file output (formatting and section order compatible with original)
- Built-in correlation deck generation (SPICE vs IBIS overlay)
- Optional ibischk validation and JSON report

**GUI Features:**
- Unified interface with dropdown/checkbox widgets for proper field types
- Support for both `.yaml` and `.s2i` input formats
- Inline model and pin editing with NoModel flag support
- Global defaults configuration with grouped settings
- Real-time simulation with progress feedback and abort capability
- Integrated plotting and correlation analysis
- Bundled ibischk7.exe with auto-detection

See [gui/README.md](gui/README.md) for complete GUI documentation.

---

### Installation (Development)

Use an editable install so the `src/` package is importable and `python -m s2ibispy` works.

Linux/macOS (bash):
```bash
git clone https://github.com/simon9721/s2ibispy.git
cd s2ibispy
python -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
pip install -e .
```

Windows (PowerShell):
```powershell
git clone https://github.com/simon9721/s2ibispy.git
cd s2ibispy
python -m venv .venv
.venv\Scripts\activate
python -m pip install -U pip
pip install -e .
```

**Requirements**: Python 3.9+, jinja2

---

### Command Line Usage

Recommended (YAML-first, after editable install):
```bash
python -m s2ibispy input.yaml [options]
```

Legacy `.s2i` configs are still supported (auto-converted internally):
```bash
python -m s2ibispy input.s2i [options]
```

Also supported (backward compatible script entry):
```bash
python main.py input.yaml [options]
```

Tip (without install): temporarily add the package to `PYTHONPATH`.
- Linux/macOS: `export PYTHONPATH=src`
- Windows PowerShell: `$env:PYTHONPATH = "src"`

### Required

- `input.yaml` — Path to modern YAML configuration
- or `input.s2i` — Legacy s2ibis3-style configuration (supported)

### Options

| Option | Description | Default |
| --- | --- | --- |
| -o, --outdir DIR | Output directory | ./out |
| --spice-type | Simulator: hspice, spectre, or eldo | hspice |
| --spice-cmd CMD | Custom simulator command line | (auto) |
| --iterate 0/1 | Reuse existing simulation outputs | 0 |
| --cleanup 0/1 | Delete intermediate .spi, .tr0, .mt0 files | 0 |
| --ibischk PATH | Run ibischk and generate reports | (disabled) |
| --correlate | Generate and run correlation deck | (disabled) |
| -v, --verbose | Enable debug logging | (disabled) |

**Note:** The GUI provides a more user-friendly way to configure these options with proper field types and validation.

### Examples

YAML input (recommended):
```bash
python -m s2ibispy tests/real_test.yaml --outdir tests/output --spice-type hspice --iterate 1 --cleanup 0 --verbose
```

Legacy `.s2i` input (still supported):
```bash
python -m s2ibispy tests/buffer.s2i --outdir tests/output --spice-type hspice --iterate 1 --cleanup 0 --verbose
```

---

### Migration from `.s2i` to YAML

- You can run existing `.s2i` files directly: `python -m s2ibispy input.s2i ...`.
- Recommended: convert to YAML for clearer structure and future features.
- GUI helps convert: load `.s2i` in the Main tab; it auto-populates the YAML model. Save via "Save YAML".
- Benefits of YAML:
	- Nested `global_defaults`, `models`, `pins`
	- Typ/Min/Max values grouped logically
	- Easier diffing/version control

**Output includes**:

- results/my_buffer.ibs
- results/compare_*.sp (correlation decks)
- results/*.ibischk_log.txt, *.json (if --ibischk used)

---

### GUI Version

A modern graphical interface is available with unified configuration, real-time simulation, and integrated analysis tools:

```bash
python gui_main.py
```

**Key Features**:

- Unified main entry tab combining file loading, YAML editing, and simulation controls
- Support for both `.yaml` (recommended) and `.s2i` (legacy) input formats
- Inline model and pin editing with proper widget types (dropdowns, checkboxes)
- Real-time simulation with progress bar and abort capability
- Integrated waveform plotting and correlation analysis
- Auto-detection of bundled ibischk7.exe for validation
- Built on Tkinter with matplotlib integration

**See detailed GUI documentation:** [gui/README.md](gui/README.md)

---

### Architecture

Core code now lives in a proper package at `src/s2ibispy/`.

| Module (package) | Responsibility |
| --- | --- |
| `s2ibispy/cli.py` | CLI entry point (`python -m s2ibispy`) |
| `s2ibispy/models.py` | Dataclasses for all IBIS structures |
| `s2ibispy/s2i_constants.py` | Constants and enums (polarity, types, sentinels) |
| `s2ibispy/schema.py` | YAML schema for modern configs |
| `s2ibispy/loader.py` | Loads YAML into IBIS model objects |
| `s2ibispy/s2ianaly.py` | Simulation plan and analysis orchestration |
| `s2ibispy/s2ispice.py` | Generates/runs SPICE, parses results |
| `s2ibispy/s2ioutput.py` | Writes the final `.ibs` (full original, patched) |
| `s2ibispy/correlation.py` | SPICE↔IBIS correlation deck generation |
| `s2ibispy/legacy/parser.py` | Legacy `.s2i` file parser (moved from root) |
| `s2ibispy/legacy/` | Legacy modules (s2iutil.py, etc.) |

#### GUI Architecture

GUI code is organized under `gui/`:
- `gui/app.py` - Main application window
- `gui/tabs/` - Tab implementations (main_entry, plots, correlation, etc.)
- `gui/utils/` - Utilities (yaml_editor_model.py, yaml_editor_config.py, s2i_to_yaml.py, parse_netlist.py)

See [gui/README.md](gui/README.md) for detailed GUI documentation.

#### Source of Truth
- Core functionality: `src/s2ibispy/`
- GUI code: `gui/`
- Legacy code: `legacy/` (backward compatibility)
- Compatibility shims: Root level (`main.py`, `gui_main.py`)

---

### Status & Roadmap

| Feature | Status | Notes |
| --- | --- | --- |
| Core IBIS 3.2 generation | Functional | Needs broader validation |
| Multi-simulator support | Implemented | HSPICE primary, Spectre/Eldo syntax |
| Correlation deck | Functional | Auto subcircuit wrapping |
| GUI | Available | Basic plotting and control |
| IBIS 5.0+ features | Partial | [Pin Mapping], [Diff Pin] supported |
| Composite Current (IBIS 6.1+) | Not started | Planned |
| Full test suite | In development | Real-world cases needed |

This tool is **not yet production-ready**. Contributions, bug reports, and test cases are very welcome.

---

### License

MIT License — free for commercial and academic use.

---

Thank you for your interest in s2ibispy.
This is a community-driven effort to modernize a critical but aging tool. Your feedback and testing are essential.