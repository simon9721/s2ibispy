# tests/test_spice.py
import os
import math
import shutil
import pytest
import sys
sys.path.append("C:\\Users\\sh3qm\\PycharmProjects\\s2ibispy")

from s2ispice import S2ISpice
from s2i_constants import ConstantStuff as CS
from models import (
    IbisModel, IbisPin, IbisTypMinMax, IbisVItable, IbisVItableEntry,
    IbisWaveTable, IbisWaveTableEntry, IbisRamp
)

# ---------------------------
# small helpers / fixtures
# ---------------------------

@pytest.fixture
def tmpdir_chdir(tmp_path):
    """Run each test in an isolated temp directory (and chdir into it)."""
    old = os.getcwd()
    os.chdir(tmp_path)
    try:
        yield tmp_path
    finally:
        os.chdir(old)

def write_file(path: str, text: str):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w") as f:
        f.write(text)
    return path

def minimal_model(name="M"):
    # Minimal, sane defaults to keep S2ISpice happy
    m = IbisModel(
        modelName=name,
        simTime=2e-8,
        Rload=50.0,
        vil=IbisTypMinMax(typ=0.8, min=0.7, max=0.9),
        vih=IbisTypMinMax(typ=2.0, min=1.8, max=2.2),
        tr=IbisTypMinMax(typ=3e-11, min=3e-11, max=3e-11),
        tf=IbisTypMinMax(typ=3e-11, min=3e-11, max=3e-11),
        ramp=IbisRamp(derateRampPct=0.0),
        tempRange=IbisTypMinMax(typ=25.0, min=0.0, max=85.0),
    )
    return m

# ---------------------------
# 1) setup_spice_file_names
# ---------------------------

def test_setup_spice_file_names_zero_pad(tmpdir_chdir):
    s = S2ISpice(mList=[])
    spi, out, msg, st0, ic, ic0 = s.setup_spice_file_names("typPU", "PIN1", 7)
    assert spi.endswith("typPU07PIN1.spi")
    assert out.endswith("typPU07PIN1.out")
    assert msg.endswith("typPU07PIN1.msg")
    assert st0.endswith("typPU07PIN1.st0")
    assert ic.endswith("typPU07PIN1.ic")
    assert ic0.endswith("typPU07PIN1.ic0")

def test_setup_spice_file_names_no_index(tmpdir_chdir):
    s = S2ISpice(mList=[])
    spi, out, msg, *_ = s.setup_spice_file_names("typPD", "P2")
    assert spi.endswith("typPDP2.spi")
    assert out.endswith("typPDP2.out")
    assert msg.endswith("typPDP2.msg")

# ---------------------------
# 2) setup_spice_input_file
# ---------------------------

def test_setup_spice_input_file_builds_deck(tmpdir_chdir):
    s = S2ISpice(mList=[])
    dut = write_file("buffer.sp", "* DUT\nR1 a b 1k\n.END\n")
    model = write_file("model.lib", "*LIB*\n.param X=1\n")
    ext = write_file("ext.cmd", ".OPTION POST\n")
    ret = s.setup_spice_input_file(
        iterate=0,
        header_line="*Header\n",
        spice_file=dut,
        model_file=model,
        ext_spice_cmd_file=ext,
        load_buffer="VOUTS2I out 0 DC 0\n",
        input_buffer="VINS2I in 0 DC 1\n",
        power_buffer="VCC vcc 0 DC 3.3\n.TEMP 25\n",
        temperature_buffer="",
        analysis_buffer=".DC VOUTS2I -1 1 0.1\n",
        spice_in="deck.spi",
    )
    assert ret == 0
    text = open("deck.spi").read()
    assert "*Header" in text
    assert "R1 a b 1k" in text
    assert ".OPTION POST" in text
    assert "VOUTS2I out 0 DC 0" in text
    assert ".TEMP 25" in text
    assert ".DC VOUTS2I -1 1 0.1" in text
    assert text.strip().endswith(".END")

# ---------------------------
# 3) call_spice (no real tool)
# ---------------------------

def test_call_spice_renames_lis_and_succeeds(tmpdir_chdir, monkeypatch):
    s = S2ISpice(mList=[], hspice_path="hspice")
    # make dummy input file so command looks plausible
    write_file("deck.spi", "*dummy*\n")

    # simulate a run that produces only a .lis but returns success
    def fake_run(cmd, shell, capture_output, text, timeout):
        # command includes "-o deck.out"
        open("deck.lis", "w").write("volt current\n0 0\n")
        class R:
            returncode = 0
            stderr = ""
            stdout = ""
        return R()
    monkeypatch.setattr("subprocess.run", fake_run)

    ret = s.call_spice(
        iterate=0, spice_command="", spice_in="deck.spi",
        spice_out="deck.out", spice_msg="deck.msg"
    )
    assert ret == 0
    assert os.path.exists("deck.out")     # renamed from deck.lis
    assert os.path.exists("deck.msg")     # captured logs

# ---------------------------
# 4) get_spice_vi_data
# ---------------------------

def test_get_spice_vi_data_parses_typ(tmpdir_chdir):
    s = S2ISpice(mList=[])
    out = write_file("vi.out", "hdr\nvolt current\n-1 -0.1\n0 0\n1 0.1\n")
    table = IbisVItable(
        VIs=[IbisVItableEntry(0.0, IbisTypMinMax(0,0,0)) for _ in range(8)],
        size=0
    )
    ret = s.get_spice_vi_data(table, 8, out, "typ")
    assert ret == 0
    assert table.size == 3
    # current is negated in parser
    assert table.VIs[0].v == -1.0 and table.VIs[0].i.typ == 0.1
    assert table.VIs[2].v == 1.0 and table.VIs[2].i.typ == -0.1

# ---------------------------
# 5) get_spice_ramp_data
# ---------------------------

def test_get_spice_ramp_data_rising_20_80(tmpdir_chdir):
    s = S2ISpice(mList=[])
    out = write_file(
        "ramp.out",
        "hdr\ntime voltage\n0 0\n1e-9 0.66\n2e-9 1.32\n4e-9 2.64\n6e-9 3.3\n"
    )
    m = minimal_model("M")

    ret = s.get_spice_ramp_data(m, CS.CurveType.RISING_RAMP, out, "typ")
    assert ret == 0

    # IBIS/Java definition uses 20–80% of the swing:
    # dv = v80 - v20 = 0.6 * 3.3 = 1.98
    assert m.ramp.dv_r.typ == pytest.approx(0.6 * 3.3, rel=1e-6)

    # For the linear data above: t20 = 1.2e-9, t80 = 4.8e-9 -> dt = 3.6e-9
    # For the linear data above: t20 = 1.0e-9, t80 = 4.0e-9 -> dt = 3.0e-9
    assert m.ramp.dt_r.typ == pytest.approx(3.0e-9, rel=1e-6)


# ---------------------------
# 6) get_spice_wave_data
# ---------------------------

def test_get_spice_wave_data_bins(tmpdir_chdir):
    s = S2ISpice(mList=[])
    out = write_file(
        "wave.out",
        "hdr\ntime voltage\n0 0\n0.5e-8 1.0\n1e-8 2.0\n2e-8 3.3\n"
    )
    w = IbisWaveTable(waveData=[], size=0)
    ret = s.get_spice_wave_data(sim_time=2e-8, spice_out=out, command="typ", wave_p=w)
    assert ret == 0
    assert w.size == CS.WAVE_POINTS_DEFAULT
    assert w.waveData[0].t == 0.0
    assert w.waveData[-1].t == pytest.approx(2e-8)
    # should have non-zero typ voltages after the first few bins
    assert any(entry.v.typ > 0 for entry in w.waveData[1:])

# ---------------------------
# 7) generate_vi_curve (thin e2e)
# ---------------------------

def test_generate_vi_curve_typ_min_max(tmpdir_chdir, monkeypatch):
    m = minimal_model("M")
    pin = IbisPin(pinName="OUT", spiceNodeName="OUT", model=m)
    s = S2ISpice(mList=[m])

    # precompute the expected "typ" filenames to know what to write in fake run
    typ_prefix = CS.spice_file_typ_prefix.get(CS.CurveType.PULLUP, "")
    spi, out, msg, *_ = s.setup_spice_file_names(typ_prefix, pin.pinName, 0)

    # fake runner that writes a valid ".out" (for each corner)
    def fake_run(cmd, shell, capture_output, text, timeout):
        # inspect cmd if you want, but simplest is: write the file we know from the first corner
        # The function will be called 3 times (typ/min/max), each with different out names;
        # to be robust, detect "-o <outfile>" and write there.
        target = None
        parts = str(cmd).split()
        if "-o" in parts:
            target = parts[parts.index("-o") + 1]
        else:
            # fallback to 'out' from typ precompute
            target = out
        # Ensure directory exists
        os.makedirs(os.path.dirname(target) or ".", exist_ok=True)
        with open(target, "w") as f:
            f.write("volt current\n-1 -0.1\n0 0\n1 0.1\n")
        class R:
            returncode = 0
            stderr = ""
            stdout = ""
        return R()

    monkeypatch.setattr("subprocess.run", fake_run)

    zero = IbisTypMinMax(0.0, 0.0, 0.0)
    sweep_start = IbisTypMinMax(typ=-1.0, min=-1.0, max=-1.0)

    ret = s.generate_vi_curve(
        current_pin=pin, enable_pin=None, input_pin=None,
        power_pin=None, gnd_pin=None, power_clamp_pin=None, gnd_clamp_pin=None,
        vcc=zero, gnd=zero, vcc_clamp=zero, gnd_clamp=zero,
        sweep_start=sweep_start, sweep_range=2.0, sweep_step=1.0,
        curve_type=CS.CurveType.PULLUP, spice_type=CS.SpiceType.HSPICE,
        spice_file="buffer.sp", spice_command="",
        enable_output=1, output_high=1, iterate=0, cleanup=0, vds=0.0, index=0
    )
    assert ret == 0
    assert m.pullupData is not None
    assert m.pullupData.size >= 1
    # Spot-check the first parsed row for typ
    assert m.pullupData.VIs[0].i.typ != 0 or m.pullupData.VIs[1].i.typ != 0

# ---------------------------
# 8) retry loop behavior
# ---------------------------

def test_generate_vi_retry_on_abort_and_nonconv(tmpdir_chdir, monkeypatch):
    m = minimal_model("M2")
    pin = IbisPin(pinName="OUT", spiceNodeName="OUT", model=m)
    s = S2ISpice(mList=[m])

    # capture sequence: first two runs -> aborted + nonconv; third run -> good .out
    state = {"i": 0}

    def fake_run(cmd, shell, capture_output, text, timeout):
        parts = str(cmd).split()
        target = parts[parts.index("-o") + 1] if "-o" in parts else "typPU00OUT.out"
        msg = target.replace(".out", ".msg")
        if state["i"] < 2:
            write_file(msg, "simulation aborted\n")
            write_file(target, "non convergence observed\n")
        else:
            write_file(target, "volt current\n0 0\n")
        state["i"] += 1
        class R:
            returncode = 0
            stderr = ""
            stdout = ""
        return R()

    monkeypatch.setattr("subprocess.run", fake_run)

    zero = IbisTypMinMax(0.0, 0.0, 0.0)
    sweep_start = IbisTypMinMax(typ=-1.0, min=-1.0, max=-1.0)

    ret = s.generate_vi_curve(
        current_pin=pin, enable_pin=None, input_pin=None,
        power_pin=None, gnd_pin=None, power_clamp_pin=None, gnd_clamp_pin=None,
        vcc=zero, gnd=zero, vcc_clamp=zero, gnd_clamp=zero,
        sweep_start=sweep_start, sweep_range=2.0, sweep_step=1.0,
        curve_type=CS.CurveType.PULLUP, spice_type=CS.SpiceType.HSPICE,
        spice_file="buffer.sp", spice_command="",
        enable_output=1, output_high=1, iterate=0, cleanup=0, vds=0.0, index=0
    )
    assert ret == 0
    assert m.pullupData is not None
