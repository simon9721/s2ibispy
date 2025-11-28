# s2ibispy contributor guide

# pys2ibis — Contributor Guide

How to Add New Features (Even If You’re New to Python)

This guide is written for **everyone** — from first-time contributors to experienced developers.

You do **not** need to be an expert in Python or IBIS to follow it.

The goal is simple:

**Add a new IBIS keyword (like a table or model type) and make sure it works perfectly.**

We will explain **every step**, **why** it is needed, and **where** to make changes.

---

### The Big Picture — 6 Easy Steps

Every new feature goes through these 6 steps (always in this order):

| Step | File Name | What You Do Here | Why It Matters |
| --- | --- | --- | --- |
| 1 | `s2i_constants.py` | Give your new table a name and file prefixes | So the program knows what to call the files |
| 2 | `models.py` | Create two boxes to store the data | One for raw data, one for final clean data |
| 3 | `schema.py` | (Optional) Let users turn the feature on/off in YAML | So people can control it |
| 4 | `s2ianaly.py` | Tell the program: “Hey, run this simulation!” | This is the “start button” |
| 5 | `s2ispice.py` | Write the correct SPICE circuit | The most important part — this makes the data real |
| 6 | `s2ioutput.py` | Print the table into the final .ibs file | So it appears in the IBIS model |

If you skip any step → the feature will **not work**.

---

### Step-by-Step Example: Adding [ISSO_PU] and [ISSO_PD] Tables

We will use real code from the project so you can copy-paste.

### Step 1: `s2i_constants.py` — Give It a Name

Open the file and find where other tables are listed.

**Add these lines:**

```python
class CurveType(IntEnum):
    # ... existing ones ...
    ISSO_PULLUP   = 60
    ISSO_PULLDOWN = 61

```

Then add file name prefixes (so SPICE files have nice names):

```python
# Typical corner
spice_file_typ_prefix.update({
    CurveType.ISSO_PULLUP:   "isso_put",
    CurveType.ISSO_PULLDOWN: "isso_pdt",
})

# Min corner
spice_file_min_prefix.update({
    CurveType.ISSO_PULLUP:   "isso_pun",
    CurveType.ISSO_PULLDOWN: "isso_pdn",
})

# Max corner
spice_file_max_prefix.update({
    CurveType.ISSO_PULLUP:   "isso_pux",
    CurveType.ISSO_PULLDOWN: "isso_pdx",
})

```

Done. The program now knows these tables exist.

---

### Step 2: `models.py` — Create Storage Boxes

Every table needs **two** places:

- `Data` → raw numbers from SPICE (messy)
- plain name → clean, final version (used in .ibs file)

**Add these lines in `IbisModel` class:**

```python
# Raw data (straight from SPICE)
isso_pullupData:   Optional[IbisVItable] = None
isso_pulldownData: Optional[IbisVItable] = None

# Final clean tables (ready for IBIS file)
isso_pullup:   Optional[IbisVItable] = None
isso_pulldown: Optional[IbisVItable] = None

```

This is how **all** tables work in pys2ibis.

---

### Step 3: `schema.py` — Let Users Turn It On (Optional but Recommended)

Add a switch so users can enable it:

```python
class ModelConfig(BaseModel):
    # ... other settings ...
    enable_isso_tables: bool = False   # Set to True to get [ISSO_PU]/[ISSO_PD]

```

Now users can write in YAML:

```yaml
enable_isso_tables: true

```

---

### Step 4: `s2ianaly.py` — Press the “Start” Button

This file decides **when** to run simulations.

**Add this function:**

```python
def needs_isso_tables(model: IbisModel, ibis_version: str) -> bool:
    # Only for IBIS 5.0 and newer
    if "5." not in ibis_version and "6." not in ibis_version and "7." not in ibis_version:
        return False
    # Only for output buffers
    return "Output" in model.modelType or "I/O" in model.modelType

```

Then in `analyze_pin()` function, after the normal tables, add:

```python
if needs_isso_tables(current_pin.model, ibis.ibisVersion):
    logging.info("Generating [ISSO_PU] and [ISSO_PD] tables")

    # Run the two simulations
    rc, raw_pu = run_vi_curve(CS.CurveType.ISSO_PULLUP,   1, CS.OUTPUT_RISING,  spice_file)
    rc, raw_pd = run_vi_curve(CS.CurveType.ISSO_PULLDOWN, 1, CS.OUTPUT_FALLING, spice_file)

    current_pin.model.isso_pullupData   = raw_pu
    current_pin.model.isso_pulldownData = raw_pd

```

---

### Step 5: `s2ispice.py` — The Most Important Part (SPICE Circuit)

This is where the real data comes from.

**Replace the old `load_buffer` logic** with this correct version:

```python
        # Special case: [ISSO_PU] and [ISSO_PD]
        if curve_type in (CS.CurveType.ISSO_PULLUP, CS.CurveType.ISSO_PULLDOWN):
            dummy = "DUMMY_ISSO"
            vcc_typ_val = abs(vcc.typ) if not math.isnan(vcc.typ) else 3.3

            if curve_type == CS.CurveType.ISSO_PULLDOWN:
                # Output tied to VCC, sweep pulldown reference
                load_buffer = f"VOUTS2I {current_pin.pinName} vdd DC 0\\n"
                isso_sources = f"VTABLE_ISSO 0 {dummy} DC 0\\n"
                isso_sources += f"VCC_ISSO vdd {dummy} DC {vcc_typ_val}\\n"
                isso_sources += f"VGND_ISSO vss 0 DC 0\\n"
                start_sweep = -vcc_typ_val
                end_sweep   = +vcc_typ_val
            else:
                # Output tied to GND, sweep pullup reference
                load_buffer = f"VOUTS2I {current_pin.pinName} 0 DC 0\\n"
                isso_sources = f"VTABLE_ISSO vdd {dummy} DC 0\\n"
                isso_sources += f"VCC_ISSO {dummy} 0 DC {vcc_typ_val}\\n"
                isso_sources += f"VGND_ISSO vss 0 DC 0\\n"
                start_sweep = +vcc_typ_val
                end_sweep   = -vcc_typ_val

            # Use our custom sources only
            power_buffer = isso_sources
            analysis_buffer = f".DC VTABLE_ISSO {start_sweep:.6g} {end_sweep:.6g} 0.066\\n"
            analysis_buffer += ".PRINT DC I(VOUTS2I)\\n"

```

This generates **exactly** the same SPICE deck as commercial tools.

---

### Step 6: `s2ioutput.py` — Show It in the IBIS File

In the `_print_model()` function, after the clamp tables, add:

```python
        self._print_vi_table(f, "[ISSO_PU]", model.isso_pullup)
        self._print_vi_table(f, "[ISSO_PD]", model.isso_pulldown)

```

Done! The tables will now appear in your .ibs file.

---

### Final Checklist (Copy-Paste This)

Before you send your code:

- [ ]  Added to `CurveType` and all 3 prefix lists
- [ ]  Added `Data` and final fields in `models.py`
- [ ]  Added a way to turn it on (in `schema.py` or code)
- [ ]  Added simulation call in `s2ianaly.py`
- [ ]  Wrote correct SPICE circuit in `s2ispice.py`
- [ ]  Cleaned raw data in `SortVIData.sort_vi_data()`
- [ ]  Printed the table in `s2ioutput.py`
- [ ]  Tested with real SPICE and ibischk7

---

### You Can Do This

Even if you’ve never touched Python before, you can add new IBIS features by following these 6 steps.

Every change is small.

Every file has a clear job.

You are not alone — the code is designed to help you.

Welcome to the team.

Your contribution keeps IBIS modeling **free and open** for everyone.

Thank you for making the future better.