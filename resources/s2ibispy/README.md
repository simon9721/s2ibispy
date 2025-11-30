# s2ibispy Documentation

This directory contains documentation specific to the s2ibispy Python implementation of the SPICE-to-IBIS converter.

## Files in This Directory

### FEATURE_COMPARISON.md
Comprehensive comparison between the original s2ibis3 (Java) and s2ibispy (Python) implementations. This document catalogs:
- Every command and feature from s2ibis3 documentation
- Support status in s2ibispy (✓ Supported / ⚠ Partial / ✗ Not Supported)
- YAML equivalents for each .s2i command
- Migration guide between formats
- Summary statistics and recommendations

**Use this document to:**
- Understand which s2ibis3 features are available in s2ibispy
- Find YAML configuration equivalents for .s2i commands
- Identify partially implemented features that need completion
- Plan migration from s2ibis3 to s2ibispy

## Quick Reference

### File Format Comparison

| Aspect | s2ibis3 (.s2i) | s2ibispy (YAML) |
|--------|----------------|-----------------|
| Format | Command-based text | YAML structured data |
| Case sensitivity | Case-insensitive | Case-sensitive keys |
| Line continuation | `+` character | YAML list syntax |
| Comments | `!` character | `#` character |
| Reserved words | `NA`, `NC` | `null`, `"NC"` |
| Multi-line text | Automatic | YAML `\|` or `>` |

### Support Summary

- **~85%** of s2ibis3 features fully supported
- **~11%** partially supported (mainly YAML schema gaps)
- **0%** completely unsupported
- **~4%** need verification

**All curve derivation algorithms from s2ibis3 are preserved:**
- Pullup/Pulldown curves with enable-based subtraction
- Power/Ground clamp curves for input models
- Ramp rate calculations (20%-80% measurement)
- Rising/Falling waveform generation with custom test fixtures

### Key Enhancements in s2ibispy

1. **Modern YAML format** - More readable and maintainable than .s2i command files
2. **IBIS v6.0 support** - Updated from v3.2 (year 2000) to v6.0+ (2020s)
3. **Full GUI** - Tkinter-based configuration interface with 6 tabs
4. **Python integration** - Native Python API, NumPy, Matplotlib, Pandas
5. **Enhanced logging** - Detailed progress: "Analyzing rising waveform data (2 waveforms)"
6. **Correlation testing** - Built-in SPICE vs IBIS comparison with visual plots
7. **Additional simulator** - Eldo support (HSpice, PSpice, Spice2, Spice3, Spectre, Eldo)
8. **Waveform editor** - GUI editor for rising/falling waveforms (Nov 2024)
9. **No Java required** - Pure Python, faster startup, smaller memory footprint
10. **Package distribution** - Install via `pip install s2ibispy`

See `FEATURE_COMPARISON.md` Section 8 for complete list of 50+ enhancements.

### Migration Path

**Legacy .s2i files:**
```bash
# Fully supported via legacy parser
python -m s2ibispy my_old_file.s2i
```

**New YAML projects:**
```bash
# Create YAML config and run
python -m s2ibispy my_config.yaml
```

**GUI mode:**
```bash
# Launch GUI for visual configuration
python gui_main.py
```

## Related Documentation

### Original s2ibis3 Documentation
See `resources/s2ibis3/` directory for the original Java tool documentation split into logical sections:
- `01_introduction.txt` - Overview and basic concepts
- `02_header_commands.txt` - Global header commands
- `03_component_description.txt` - Component specifications
- `04_pin_lists.txt` - Pin mapping and lists
- `05_model_specification.txt` - Model parameters
- `06_series_switch_models.txt` - Series switch specifics
- `curves.txt` - **How IBIS curves are derived from SPICE simulations**
- `READMEofs2ibis3.txt` - **Original installation and usage guide**
- `s2ibis3.txt` - Complete original documentation (unsplit)
- `README.txt` - Documentation structure guide

### Project Documentation
See `docs/` directory for implementation-specific documentation:
- `BEFORE_AFTER_COMPARISON.md` - Code refactoring history
- `CORRELATION_ROADMAP.md` - Correlation testing guide
- `REFACTORING_NOTES.md` - Technical refactoring notes
- `s2ibispy contributor guide.md` - Development guidelines
- `YAML_EDITOR_INTEGRATION.md` - YAML editor integration
- `YAML_EDITOR_REFERENCE.md` - YAML configuration reference

## Contributing

If you find missing features or discrepancies in the feature comparison:

1. Check `legacy/parser.py` for .s2i command support
2. Check `src/s2ibispy/schema.py` for YAML schema definitions
3. Check `src/s2ibispy/loader.py` for YAML loading logic
4. Update `FEATURE_COMPARISON.md` with your findings
5. Submit issues or pull requests for missing features

## Version History

- **v1.x** - Initial Python port with YAML support
- **Current** - Enhanced with GUI, correlation testing, comprehensive feature parity

---

*Last updated: 2024*
*For questions: See project README.md*
