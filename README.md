# s2ibispy — A Modern Python Implementation of s2ibis3

[Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue)

[License: MIT](https://img.shields.io/badge/license-MIT-green)

[Work in Progress](https://img.shields.io/badge/status-work%20in%20progress-orange)


![S2IBISpy](resources/s2ibispy.png)


`s2ibis3` was developed by North Carolina State University and has been a widely used reference tool for generating IBIS models from SPICE netlists. Written in Java, it has not received updates in many years.

**s2ibispy** is a new, independent implementation in modern Python. The goal is to provide a clean, maintainable, and extensible codebase while maintaining compatibility with existing `.s2i` configuration files and producing functionally equivalent IBIS output.

This project is **under active development** and requires extensive real-world validation.

---

### Features (Current)

- Full `.s2i` file parsing with `[Include]` support and line continuations
- Hierarchical default propagation (global to component to model)
- SPICE deck generation for HSPICE, Spectre, and Eldo
- VI curve, ramp, and waveform extraction
- Accurate IBIS file output (formatting and section order compatible with original)
- Built-in correlation deck generation (SPICE vs IBIS overlay)
- Optional ibischk validation and JSON report
- GUI version available (`gui_main.py`)

---

### Installation (Development)

```bash
git clone <https://github.com/yourname/s2ibispy.git>
cd s2ibispy
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\\Scripts\\activate   # Windows
pip install -e .
```

**Requirements**: Python 3.9+, jinja2

---

### Command Line Usage

```bash
s2ibispy input.s2i [options]`
```

### Required

- input.s2i — Path to your s2ibis3-style configuration file

### Options

| Option | Description | Default |
| --- | --- | --- |
| -o, --outdir DIR | Output directory | ./out |
| --spice-type | Simulator: hspice, spectre, or eldo | hspice |
| --spice-cmd CMD | Custom simulator command line | (auto) |
| --iterate 0/1 | Reuse existing simulation outputs | 0 |
| --cleanup 0/1 | Delete intermediate .spi, .out, .msg files | 0 |
| --ibischk PATH | Run ibischk and generate reports | (disabled) |
| --correlate | Generate and run correlation deck | (disabled) |
| -v, --verbose | Enable debug logging | (disabled) |

### Example

```bash
s2ibispy my_buffer.s2i -o results --spice-type spectre --correlate --ibischk ./ibischk8`
```

**Output includes**:

- results/my_buffer.ibs
- results/compare_*.sp (correlation decks)
- results/*.ibischk_log.txt, *.json (if --ibischk used)

---

### GUI Version

A graphical interface is available:

```bash
python gui_main.py`
```

**Features**:

- Drag-and-drop .s2i file loading
- Real-time log output
- Waveform plotting (via matplotlib)
- One-click correlation deck generation
- Built on Tkinter (no extra dependencies)

---

### Architecture

| Module | Responsibility |
| --- | --- |
| main.py | CLI entry point and pipeline orchestration |
| parser.py | Parses .s2i files with full syntax support |
| models.py | Dataclasses for all IBIS structures (typ/min/max aware) |
| s2i_constants.py | Constants and enums matching original behavior |
| s2iutil.py | Default propagation and pin to model linking |
| s2ianaly.py | Determines which simulations to run |
| s2ispice.py | Generates and runs SPICE decks, parses output |
| s2ioutput.py | Writes final .ibs file |
| correlation.py | Generates self-validating SPICE+IBIS testbench |

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