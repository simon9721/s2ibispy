# Correlation Feature Roadmap

**Goal:** Transform s2ibispy correlation from "useful script" → **industry-standard IBIS validation suite**

---

## Phase 1 — Immediate Wins (1–4 weeks) ⚡

**Goal:** Make correlation configurable and production-ready with minimal effort

### 1.1 Configurable Transmission-Line Fixture
**Effort:** Low | **Impact:** 5/5 | **Status:** Not Started

**Current Issue:**
- Hard-coded `Z50_406.lc3` in `src/s2ibispy/correlation.py` (line 251)
- No user control over trace impedance/length/material

**Implementation:**
- Add `--fixture` CLI option accepting preset names or custom paths
- Add YAML config support: `correlation: { fixture: "ddr5", fixture_length: 1.2 }`
- Update `correlation.py` to resolve fixture from:
  1. CLI argument (highest priority)
  2. YAML config
  3. Package default (fallback)

**Deliverables:**
```bash
# Preset fixture
python -m s2ibispy input.yaml --correlate --fixture ddr5

# Custom fixture
python -m s2ibispy input.yaml --correlate --fixture path/to/trace.lc3
```

---

### 1.2 Bundle Standard Fixtures Library
**Effort:** Low | **Impact:** 5/5 | **Status:** Not Started

**Goal:** Provide 5+ production-grade fixtures covering common SI scenarios

**Fixture Library** (`src/s2ibispy/data/fixtures/`):

| Fixture Name | Impedance | Length | Material | Use Case |
|--------------|-----------|--------|----------|----------|
| `Z50_406mm_FR4.lc3` | 50 Ω | 406 mm | FR4 | Legacy DDR3/PCIe Gen3 |
| `Z85_100mm_lowloss.lc3` | 85 Ω | 100 mm | Low-loss | DDR5/LPDDR5 |
| `Z100_50mm_Megtron6.lc3` | 100 Ω | 50 mm | Megtron6 | PCIe Gen6/112G |
| `Z90_200mm_DDR4.lc3` | 90 Ω | 200 mm | FR4 | DDR4 UDIMM |
| `package_BGA_stub.rlgc` | 50 Ω | 5 mm | PKG | On-die → BGA ball |
| `ideal_50ohm_100ps.td` | 50 Ω | 100 ps | Ideal | Lossless reference |

**Packaging:**
- Update `pyproject.toml`:
  ```toml
  [tool.setuptools.package-data]
  s2ibispy = ["data/*.lc3", "data/fixtures/*.lc3", "data/fixtures/*.rlgc"]
  ```

---

### 1.3 Auto-Select Fixture (Smart Defaults)
**Effort:** Low | **Impact:** 4/5 | **Status:** Not Started

**Goal:** Automatically choose fixture based on model voltage/speed for zero-config correlation

**Heuristic Logic:**
```python
def auto_select_fixture(model: IbisModel) -> str:
    """Smart fixture selection based on model characteristics"""
    vdd = model.voltage_range.typ if model.voltage_range else 1.8
    edge_rate = estimate_edge_rate(model)  # from rising/falling waveforms
    
    if vdd < 1.2:
        return "Z85_100mm_lowloss"  # DDR5/LPDDR5
    elif edge_rate < 50e-12:  # < 50 ps
        return "Z100_50mm_Megtron6"  # High-speed serial
    elif vdd > 2.5:
        return "Z50_406mm_FR4"  # Legacy 3.3V LVCMOS
    else:
        return "Z90_200mm_DDR4"  # Modern DDR4/LPDDR4
```

**User Override:** CLI/YAML always takes precedence over auto-selection

---

### 1.4 Bonus: One-Line Wins (Do Today) 🚀
**Effort:** Trivial | **Impact:** 4/5

- ✅ Add `--quiet` and `--verbose` flags to CLI (5 min)
- ✅ Print correlation summary table to console on finish (10 min)
- ✅ Exit code 0 only if all metrics pass — CI-friendly (2 min)
- ✅ Add `--dry-run` flag to preview what would be simulated (5 min)

**Console Output Example:**
```
╔══════════════════════════════════════════════════════════════╗
║              CORRELATION SUMMARY                             ║
╠══════════════════════════════════════════════════════════════╣
║ Model: SN74LVC1G07_OUTPUT                                    ║
║ Fixture: Z85_100mm_lowloss (auto-selected)                   ║
║ Test: switching (3-buffer chain)                             ║
╠══════════════════════════════════════════════════════════════╣
║ Metric              | SPICE    | IBIS     | Delta  | PASS   ║
╠══════════════════════════════════════════════════════════════╣
║ Rise Time (20-80%)  | 487 ps   | 502 ps   | +3.1%  | ✓      ║
║ Fall Time (80-20%)  | 411 ps   | 398 ps   | -3.2%  | ✓      ║
║ Overshoot           | 87 mV    | 105 mV   | +20%   | ✗      ║
║ Undershoot          | -42 mV   | -39 mV   | -7.1%  | ✓      ║
║ Delay (50%)         | 2.13 ns  | 2.11 ns  | -0.9%  | ✓      ║
╠══════════════════════════════════════════════════════════════╣
║ Overall: 4/5 metrics passed                                  ║
╚══════════════════════════════════════════════════════════════╝

Exit code: 1 (failed)
```

---

## Phase 2 — Professional-Grade Correlation Suite (1–3 months) 🏆

**Goal:** Multi-test validation with automated pass/fail and reporting

### 2.1 Multiple Test Types
**Effort:** Medium | **Impact:** 5/5 | **Status:** Not Started

**Test Suite** (Jinja2 templates in `src/s2ibispy/templates/tests/`):

| Test Name | Description | Template | Priority |
|-----------|-------------|----------|----------|
| `switching` | 3-buffer chain (current) | `switching.sp.j2` | ✅ Done |
| `highz_leakage` | Tri-state DC sweep -200mV → VDD+200mV | `highz_leakage.sp.j2` | High |
| `smart_stimulus` | PRBS7/31, DDR5 training, PCIe TS1/TS2 | `smart_stimulus.sp.j2` | High |
| `crosstalk` | Coupled 3-line trace (aggressor + 2 victims) | `crosstalk.sp.j2` | Medium |
| `ccomp_sweep` | Composite current ±30% variation | `ccomp_sweep.sp.j2` | Medium |
| `return_loss` | TDR pulse + S11 extraction (FFT) | `return_loss.sp.j2` | Low |

**CLI Usage:**
```bash
# Single test
python -m s2ibispy input.yaml --correlate --test switching

# Multiple tests
python -m s2ibispy input.yaml --correlate --test switching,crosstalk,highz

# All tests
python -m s2ibispy input.yaml --correlate --test all
```

**Implementation Order:**
1. `highz_leakage` (easy, high value for tri-state validation)
2. `smart_stimulus` (moderate, critical for DDR/PCIe)
3. `crosstalk` (medium, needs W-element HSPICE support)
4. Defer `return_loss` to Phase 3 (requires FFT + S-parameter expertise)

---

### 2.2 Automatic Waveform Analysis + Pass/Fail
**Effort:** Medium | **Impact:** 5/5 | **Status:** Not Started

**Metrics to Extract:**
- **Timing:** Rise/fall time (10-90%, 20-80%), propagation delay
- **Voltage:** Overshoot, undershoot, peak-to-peak ripple
- **Eye Diagram:** Eye height, eye width, jitter RMS (for multi-bit patterns)
- **Power:** Average/peak supply current, ground bounce
- **RMS Error:** Waveform correlation coefficient vs. SPICE

**Tolerance Defaults:**
```yaml
correlation:
  tolerances:
    edge_rate: 8%      # ±8% for rise/fall
    overshoot: 120mV   # absolute mV
    delay: 5%          # ±5% for propagation
    rms_error: 10%     # waveform correlation
```

**Implementation:**
- Use `numpy` for waveform processing
- Use `scipy.signal` for edge detection, FFT
- Store results in `correlation_results.json`

---

### 2.3 HTML/PDF Report Generation
**Effort:** Medium | **Impact:** 5/5 | **Status:** Not Started

**Report Contents:**
- Executive summary (pass/fail by test)
- Per-test overlaid plots (SPICE vs. IBIS)
- Metric tables with delta/tolerance
- Fixture/model/configuration details
- Timestamp + git commit SHA (if available)

**Tech Stack:**
- Jinja2 template → `report_template.html.j2`
- Matplotlib plots embedded as base64 images
- Optional: `weasyprint` for PDF export

**Output:**
```bash
python -m s2ibispy input.yaml --correlate --report html
# Generates: output/correlation_report_2025-11-29.html
```

---

### 2.4 Multi-Corner Support
**Effort:** Medium | **Impact:** 5/5 | **Status:** Not Started

**Goal:** Run typ/fast/slow corners automatically and compare

**CLI:**
```bash
python -m s2ibispy input.yaml --correlate --corners typ,fast,slow
```

**Implementation:**
- Run N simulations with different temp/voltage
- Generate comparison table showing worst-case corner per metric
- Flag if any corner fails tolerance

---

## Phase 3 — Production & CI/CD Ready (3–6 months) 🏭

### 3.1 Regression Dashboard & History
**Effort:** Medium | **Impact:** 4/5 | **Status:** Not Started

**Goal:** Track correlation results over time for regression analysis

**Storage:** SQLite database (`correlation_history.db`) with schema:
```sql
CREATE TABLE runs (
    run_id INTEGER PRIMARY KEY,
    timestamp TEXT,
    model_name TEXT,
    fixture TEXT,
    test_type TEXT,
    pass_count INTEGER,
    fail_count INTEGER,
    git_commit TEXT
);

CREATE TABLE metrics (
    metric_id INTEGER PRIMARY KEY,
    run_id INTEGER,
    metric_name TEXT,
    spice_value REAL,
    ibis_value REAL,
    delta_pct REAL,
    passed INTEGER,
    FOREIGN KEY(run_id) REFERENCES runs(run_id)
);
```

**CLI:**
```bash
# List history
python -m s2ibispy --corr-history

# Compare runs
python -m s2ibispy --corr-diff run123 run124

# Trend analysis
python -m s2ibispy --corr-trend SN74LVC1G07 --last 30d
```

---

### 3.2 Golden Reference Mode
**Effort:** Low | **Impact:** 5/5 | **Status:** Not Started

**Goal:** Lock known-good results and compare future runs

**Workflow:**
```bash
# Create golden reference
python -m s2ibispy input.yaml --correlate --save-golden ./golden_2025-11-29/

# Validate against golden
python -m s2ibispy input.yaml --correlate --golden-dir ./golden_2025-11-29/
```

**Golden Directory Contents:**
- `results.json` (all metrics)
- `waveforms/` (`.tr0` files)
- `config.yaml` (fixture, test settings)
- `metadata.txt` (timestamp, git SHA, IBIS version)

**Comparison:**
- Flag regressions exceeding tolerance vs. golden
- Generate delta report

---

### 3.3 Support Modern IBIS Features
**Effort:** High | **Impact:** 5/5 | **Status:** Not Started

**Features to Add:**
- IBIS 6.1+ **Composite Current** waveforms
- IBIS 7.0+ **[Driver Schedule]** multi-stage buffers
- **Touchstone models** (S-parameter package)
- Integration with **ibischk7** (validate before correlate)

**Note:** IBIS-AMI executable model flow deferred to Phase 4 or separate project (high complexity)

---

## Phase 4 — Polish & Nice-to-Haves (Future) 🎨

### 4.1 Advanced Features
- **Batch processing:** Run 50 models overnight with `--batch models/*.yaml`
- **Custom tolerance settings:** CLI overrides per metric
- **Plot-only mode:** `--plot-only spice.tr0 ibis.tr0` for debugging
- **JSON output:** Machine-readable results for programmatic parsing
- **Spectre/Eldo support:** Not just HSPICE (moderate effort)
- **Coupled T-line fixture:** True far-end crosstalk (`.cpl` file format)

### 4.2 Deployment & CI/CD
- **Docker image:** Pre-configured with HSPICE license stub
- **GitHub Actions workflow:** Template for nightly validation
- **PyPI package:** `pip install s2ibispy[correlation]` with all fixtures

### 4.3 GUI Integration
- Add **Correlation** section to main GUI tab:
  - Fixture selector dropdown (preset + custom)
  - Test type checkboxes (switching, crosstalk, etc.)
  - Pass/fail badge (green ✓ / red ✗)
  - "Re-run Last Correlation" button
  - Live progress: "Running test 2/5..."

---

## Testing Strategy

**Unit Tests** (`tests/correlation/`):
- Known-good IBIS models (sample1.ibs, sn74lvc2t45.ibs)
- Expected waveforms (`.tr0.golden`)
- Pytest suite that runs mini-correlations

**Example Test:**
```python
def test_correlation_switching():
    result = run_correlation("tests/correlation/sample1.yaml", 
                            fixture="ideal_50ohm", 
                            test="switching")
    assert result.pass_rate >= 0.95  # 95% metrics pass
    assert result.overshoot < 150e-3  # 150 mV
```

---

## Success Metrics

**Phase 1 Complete When:**
- ✅ 5+ bundled fixtures available
- ✅ `--fixture` CLI option works with presets + custom paths
- ✅ Auto-selection heuristic selects correct fixture 90% of time
- ✅ Console summary prints pass/fail

**Phase 2 Complete When:**
- ✅ 3+ test types implemented (switching, highz, smart_stimulus)
- ✅ HTML report generates with overlaid plots
- ✅ Multi-corner support runs typ/fast/slow
- ✅ Pass/fail logic validates 95%+ of real-world models

**Phase 3 Complete When:**
- ✅ Regression database tracks 100+ runs
- ✅ Golden reference mode detects regressions
- ✅ IBIS 6.1+ features supported

---

## Priority Summary

| Feature | Phase | Effort | Impact | Priority |
|---------|-------|--------|--------|----------|
| Configurable fixture | 1 | Low | 5/5 | 🔥 Do First |
| Bundle fixtures | 1 | Low | 5/5 | 🔥 Do First |
| Console summary | 1 | Trivial | 4/5 | 🔥 Do First |
| highz_leakage test | 2 | Low | 5/5 | ⚡ High |
| smart_stimulus test | 2 | Med | 5/5 | ⚡ High |
| HTML report | 2 | Med | 5/5 | ⚡ High |
| Multi-corner | 2 | Med | 5/5 | ⚡ High |
| crosstalk test | 2 | Med | 4/5 | ✓ Medium |
| Regression DB | 3 | Med | 4/5 | ✓ Medium |
| Golden reference | 3 | Low | 5/5 | ✓ Medium |
| return_loss test | 3 | High | 3/5 | ⏸ Low |
| IBIS-AMI flow | 4 | High | 3/5 | ⏸ Defer |

---

## Next Steps

1. **Start Phase 1.1:** Implement `--fixture` CLI option
2. **Gather fixtures:** Create/source the 5 standard traces
3. **Test with real models:** Validate against DDR5/PCIe Gen6 IBIS files
4. **Ship Phase 1 ASAP:** Get user feedback before Phase 2

---

**End Goal:** By completing Phase 1 + Phase 2, s2ibispy becomes **the de facto open-source IBIS validator** — cited at IBIS Summits, used by 112G/UCIe/DDR6 teams, and trusted for production sign-off.
