# Why YAML for s2ibispy (and the limits of .s2i)

s2ibispy supports both the legacy s2ibis3-style `.s2i` files and a modern YAML format. This document explains why YAML is the primary format going forward, and where `.s2i` shows its age for today’s workflows.

---

## Summary

- YAML is structured, typed, and tool‑friendly; `.s2i` is a flat, ad‑hoc config language.
- YAML enables reliable validation, modern editors/linters, and predictable diffs.
- `.s2i` works for simple cases but becomes fragile with real‑world complexity (includes, overrides, units, multi-line semantics).

---

## Side‑by‑Side Glance

Legacy `.s2i` (excerpt from `tests/buffer.s2i`):

```text
[IBIS Ver]        3.2
[File rev]        0
[Spice type]      hspice
[temperature range] 27 100 0
[voltage range]   3.3 3 3.6
[sim time]        3ns
[Pin]
out out out driver 
-> in 
...
[Model]  driver
[Model type] output
[Polarity] Non-inverting
[Model file] hspice.mod hspice.mod hspice.mod
[Rising waveform] 500 0 NA NA NA NA NA NA NA
[Falling waveform] 500 3.3 NA NA NA NA NA NA NA
```

Modern YAML (excerpt from `tests/simple.yaml`):

```yaml
file_name: simple_test.ibs
file_rev: "0.1"

global_defaults:
  voltage_range: { typ: 3.3, min: 3.0, max: 3.6 }
  c_comp: { typ: 1.0e-12, min: 0.8e-12, max: 1.2e-12 }

models:
  - name: BUF1
    type: I/O
    c_comp:
      typ: 1.5e-12
      min: 1.2e-12
      max: 1.8e-12

components:
  - component: TEST_CHIP
    manufacturer: Test Inc.
    pList:
      - pinName: "1"
        signalName: DQ0
        modelName: BUF1
```

---

## Why YAML

- Schema & validation: YAML maps cleanly to a schema (see `src/s2ibispy/schema.py`), enabling early error detection (missing fields, wrong types, invalid choices).
- Explicit structure: Nested groups for `global_defaults`, `models`, `components`, and pin lists prevent accidental cross‑contamination of settings.
- Data types: Numbers, strings, booleans, and lists are unambiguous; units can be parsed reliably (`1e-12` vs `1.0p` heuristics).
- Tooling: Excellent ecosystem—IDEs, linters, formatters, and pre‑commit hooks keep configs consistent.
- Merge & diff: Hierarchical keys yield readable diffs in PRs; partial overrides are localized.
- Extensibility: Adding new fields (e.g., correlation options, simulator switches) is straightforward without inventing new bracketed keywords.

---

## Where `.s2i` Falls Short

- Flat, keyword‑driven grammar:
  - Repeated keywords and positional fields (e.g., `[Rising waveform] 500 0 ...`) are easy to mis‑order and hard to validate.
  - No native typing—values become ambiguous (literal `0`, `0V`, `0.0`, or `NA`).
- Line continuation & sections:
  - Special syntaxes like the `Pin` section (`->` continuation lines) are brittle.
  - Multi‑line text blocks (e.g., `notes`, `disclaimer`) lack clear delimiters and are truncated in legacy tools.
- Includes & overrides:
  - `[Include]` and split configs increase fragility and resolution order confusion.
  - No namespaced scoping—global values can be unintentionally overridden.
- Unit ambiguity:
  - Mix of `ns`, `m`, `pF`, or plain numbers depends on context; parsers must guess.
- Limited editor support:
  - No language server or schema—typos in keywords go unnoticed until runtime.
- Poor diffability:
  - Reordering blocks or adding a field can cause noisy, unhelpful diffs.

---

## Practical Wins with YAML in this Repo

- Clear defaults and overrides: `global_defaults` for `voltage_range`, `temp_range`, `pin_parasitics`, etc., apply broadly while remaining explicit.
- Models are first‑class: `models[]` carry per‑model parameters, waveforms, and flags (e.g., `nomodel`) without positional guessing.
- Components & pins are structured: `components[].pList[]` mirrors IBIS intent directly; additional per‑pin metadata can be added safely.
- Correlation options: YAML is ready for feature growth (e.g., correlation templates, deck toggles) without grammar changes.

---

## Migration Guidance

You can run `.s2i` as‑is, but we recommend migrating to YAML:

- CLI (both supported):

```powershell
# YAML (recommended)
python -m s2ibispy tests/real_test.yaml --outdir tests/output --iterate 1 --cleanup 0

# Legacy .s2i
python -m s2ibispy tests/buffer.s2i --outdir tests/output --iterate 1 --cleanup 0
```

- GUI assisted conversion:
  - Open the GUI (`python gui_main.py` or the packaged `.exe`).
  - Load an `.s2i` in the Main tab; the YAML model is auto‑populated.
  - Review, then “Save YAML”.

- Programmatic conversion:
  - Utilities under `gui/utils/s2i_to_yaml.py` are available for scripted flows.

---

## Known Behavior Differences (Heads‑up)

- Units: YAML examples prefer scientific notation (`6e-9`) for clarity; `.s2i` may use `3ns` or `2pF`. s2ibispy normalizes inputs where possible.
- Paths: YAML fields like `spiceFile` and `modelFile*` are explicit; `.s2i` may rely on working‑dir assumptions.
- Defaults: YAML’s `global_defaults` are applied deterministically; `.s2i` global scope and later overrides can be confusing in large files.

---

## Screenshot Placeholders

> Replace the placeholders below with real screenshots when available.

- ![GUI: Load .s2i and review YAML](../resources/screenshots/PLACEHOLDER_load_s2i_to_yaml.png)
- ![Editor: YAML schema validation highlighting](../resources/screenshots/PLACEHOLDER_yaml_schema_validation.png)
- ![Diff: Clean YAML change showing localized edits](../resources/screenshots/PLACEHOLDER_yaml_diff_example.png)

---

## Appendix: Real Examples in this Repo

- `.s2i`: `tests/buffer.s2i`, `tests/ex2.s2i`, `tests/ex3.s2i`, `tests/ex4.s2i`
- YAML: `tests/simple.yaml`, `tests/real_test.yaml`, `tests/test_load.yaml`, `tests/buffer.yaml`

These samples reflect the patterns discussed above and are good starting points for migration.
