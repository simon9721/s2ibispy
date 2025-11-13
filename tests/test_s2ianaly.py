# tests/test_s2ianaly.py
import math
import os
import sys
import pytest



PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, PROJECT_ROOT)
from tests.fake import FakeSpiceTransient

from s2ianaly import (
    S2IAnaly, AnalyzeComponent, AnalyzePin,
    FindSupplyPins, SetupVoltages, SortVIData, SortVISeriesData,
    this_model_needs_pullup_data, this_model_needs_pulldown_data,
)
from s2i_constants import ConstantStuff as CS
from models import (
    IbisTOP, IbisGlobal, IbisComponent, IbisPin, IbisModel,
    IbisTypMinMax, IbisVItable, IbisVItableEntry, SeriesModel, IbisWaveTable,
)
from s2iutil import S2IUtil


# -----------------------
# Helpers / test doubles
# -----------------------
def _tmm(t, m=None, x=None):
    """Convenience builder for IbisTypMinMax."""
    return IbisTypMinMax(
        typ=t,
        min=t if m is None else m,
        max=t if x is None else x,
    )

def _vi_table(vals_v, vals_i_typ, vals_i_min=None, vals_i_max=None):
    if vals_i_min is None:
        vals_i_min = vals_i_typ
    if vals_i_max is None:
        vals_i_max = vals_i_typ
    VIs = []
    for v, it, imin, imax in zip(vals_v, vals_i_typ, vals_i_min, vals_i_max):
        VIs.append(IbisVItableEntry(v=v, i=IbisTypMinMax(typ=it, min=imin, max=imax)))
    return IbisVItable(VIs=VIs, size=len(VIs))


class FakeSpice:
    """
    Minimal fake that mimics S2ISpice's interface used by AnalyzePin:
    - generate_vi_curve: sets self.last_vi_table with deterministic data
    - generate_ramp_data / generate_wave_data: return 0 (ok)
    """

    def __init__(self, mList):
        self.mList = mList
        self.last_vi_table = None

    def _make_vi(self, curve_type, vcc, gnd, vds=0.0, disabled=False):
        # Make small tables whose values clearly show what's happening.
        # Voltages differ per curve (so sorting/clamp logic is exercised).
        if curve_type == CS.CurveType.PULLUP:
            vs = [0.0, 0.5, 1.0]
            base = 10.0
        elif curve_type == CS.CurveType.DISABLED_PULLUP:
            vs = [0.0, 0.5, 1.0]
            base = 1.0   # small offset to subtract out
        elif curve_type == CS.CurveType.PULLDOWN:
            vs = [0.0, 0.5, 1.0]
            base = -10.0
        elif curve_type == CS.CurveType.DISABLED_PULLDOWN:
            vs = [0.0, 0.5, 1.0]
            base = -1.0
        elif curve_type == CS.CurveType.POWER_CLAMP:
            # ensure some are >= VCC.typ for selection & vcc-relative conversion
            v0 = vcc.typ - 0.5
            vs = [v0, v0 + 0.25, v0 + 0.5, v0 + 0.75, vcc.typ + 0.5]
            base = 3.0
        elif curve_type == CS.CurveType.GND_CLAMP:
            # ensure some are <= VCC.typ for selection
            vs = [gnd.typ - 0.5, gnd.typ, 0.0, 0.5, vcc.typ - 0.25]
            base = -3.0
        elif curve_type == CS.CurveType.SERIES_VI:
            vs = [0.0 + vds, 0.5 + vds, 1.0 + vds]
            base = 5.0
        else:
            vs = [0.0, 0.5, 1.0]
            base = 0.0

        # current magnitudes
        it = [base + i for i in range(len(vs))]
        table = _vi_table(vs, it)
        return table

    def generate_vi_curve(
        self,
        current_pin, enable_pin, input_pin,
        pullup_pin, pulldown_pin, power_clamp_pin, gnd_clamp_pin,
        vcc, gnd, vcc_clamp, gnd_clamp,
        sweep_start, sweep_range, sweep_step,
        curve_type, spice_type, file, spice_command,
        enable_output, output_state, iterate, cleanup,
        vds, vds_idx,
    ):
        # disabled if enable_output == 0
        disabled = (enable_output == 0)
        self.last_vi_table = self._make_vi(curve_type, vcc, gnd, vds=vds, disabled=disabled)
        return 0

    def generate_ramp_data(self, *args, **kwargs):
        return 0

    def generate_wave_data(self, *args, **kwargs):
        return 0


# -----------------------
# Fixtures
# -----------------------
@pytest.fixture
def simple_env():
    # Global with sane ranges
    global_ = IbisGlobal(
        voltageRange=_tmm(1.8),
        pullupRef=_tmm(1.8),
        pulldownRef=_tmm(0.0),
        powerClampRef=_tmm(1.8),
        gndClampRef=_tmm(0.0),
        derateVIPct=0.0,
        derateRampPct=0.0,
    )

    # One model
    m = IbisModel(
        modelName="OUT_A",
        modelType=CS.ModelType.IO,
    )

    # Pins: power, gnd, enable, input, and one signal pin using OUT_A
    pwr = IbisPin(pinName="VDD", modelName="POWER")
    gnd = IbisPin(pinName="VSS", modelName="GND")
    en  = IbisPin(pinName="EN",  modelName="NOMODEL")
    din = IbisPin(pinName="DIN", modelName="NOMODEL")
    sig = IbisPin(pinName="P1",  modelName="OUT_A", enablePin="EN", inputPin="DIN")

    comp = IbisComponent(component="U1", pList=[pwr, gnd, en, din, sig])
    ibis = IbisTOP(cList=[comp])

    return ibis, global_, [m], comp, sig


@pytest.fixture
def util():
    return S2IUtil(mList=[])


# -----------------------
# Tests
# -----------------------
def test_find_supply_pins_basic(simple_env):
    ibis, global_, mlist, comp, _ = simple_env
    util = S2IUtil(mlist)
    util.complete_data_structures(ibis, global_)

    f = FindSupplyPins()
    pins = f.find_pins(comp.pList[-1], comp.pList, comp.hasPinMapping)
    assert pins["pullupPin"] and pins["pullupPin"].modelName.upper() == "POWER"
    assert pins["pulldownPin"] and pins["pulldownPin"].modelName.upper() == "GND"


def test_analyze_pin_disabled_subtraction_and_sorting(simple_env, monkeypatch):
    ibis, global_, mlist, comp, sig = simple_env
    util = S2IUtil(mlist)
    util.complete_data_structures(ibis, global_)
    # Wire model to pin
    sig.model = mlist[0]

    # Fake spice plugged into analyzer
    fake = FakeSpice(mlist)
    from s2ianaly import AnalyzePin
    ap = AnalyzePin(fake)

    # Locate helper pins
    pwr = next(p for p in comp.pList if p.modelName.upper() == "POWER")
    gnd = next(p for p in comp.pList if p.modelName.upper() == "GND")
    en  = next(p for p in comp.pList if p.pinName == "EN")
    din = next(p for p in comp.pList if p.pinName == "DIN")

    rc = ap.analyze_pin(
        sig, en, din,
        pwr, gnd, pwr, gnd,
        spice_type=CS.SpiceType.HSPICE,
        spice_file="dummy.sp",
        series_spice_file="series.sp",
        spice_command="run",
        iterate=0,
        cleanup=0,
    )
    assert rc == 0

    # After subtraction, pullupData currents should equal enabled - disabled.
    # FakeSpice produced typ currents: enabled = 10,11,12; disabled = 1,2,3 → diff = 9,9,9
    pu = sig.model.pullupData
    assert pu and pu.size >= 3
    for i in range(3):
        assert abs(pu.VIs[i].i.typ - 9.0) < 1e-9
        assert abs(pu.VIs[i].i.min - 9.0) < 1e-9
        assert abs(pu.VIs[i].i.max - 9.0) < 1e-9

    # Pulldown: enabled = -10,-9,-8; disabled = -1,0,1 → diff = -9,-9,-9
    pd = sig.model.pulldownData
    assert pd and pd.size >= 3
    for i in range(3):
        assert abs(pd.VIs[i].i.typ - (-9.0)) < 1e-9

    # Power/GND clamps should be present (sorted/filtered by SortVIData)
    assert sig.model.powerClampData is not None
    assert sig.model.gndClampData is not None


def test_series_vi_path_and_sorting(simple_env):
    ibis, global_, mlist, comp, sig = simple_env
    # Attach a series model and VDS list
    m = mlist[0]
    m.seriesModel = SeriesModel(OnState=True, OffState=False, vdslist=[0.5, 1.0])

    util = S2IUtil(mlist)
    util.complete_data_structures(ibis, global_)
    sig.model = m

    fake = FakeSpice(mlist)
    ap = AnalyzePin(fake)

    pwr = next(p for p in comp.pList if p.modelName.upper() == "POWER")
    gnd = next(p for p in comp.pList if p.modelName.upper() == "GND")
    en  = next(p for p in comp.pList if p.pinName == "EN")
    din = next(p for p in comp.pList if p.pinName == "DIN")

    rc = ap.analyze_pin(
        sig, en, din, pwr, gnd, pwr, gnd,
        spice_type=CS.SpiceType.HSPICE,
        spice_file="dummy.sp",
        series_spice_file="series.sp",
        spice_command="run",
        iterate=0,
        cleanup=0,
    )
    assert rc == 0
    assert sig.model.seriesVITables and len(sig.model.seriesVITables) == 2

    # Check VCC-relative + reversed ordering for one of the series tables
    tbl = sig.model.seriesVITables[0]
    assert tbl.size == 3
    # We can't know exact VCC used here without re-running SetupVoltages,
    # but we can at least assert the voltages are strictly decreasing (reversed copy)
    vs = [e.v for e in tbl.VIs]
    assert all(vs[i] > vs[i+1] for i in range(len(vs)-1))


def test_one_and_done_model_analysis(simple_env):
    ibis, global_, mlist, comp, sig = simple_env
    util = S2IUtil(mlist)
    util.complete_data_structures(ibis, global_)
    sig.model = mlist[0]

    fake = FakeSpice(mlist)
    from s2ianaly import AnalyzeComponent
    ac = AnalyzeComponent(fake, util)

    # First run flips hasBeenAnalyzed
    rc1 = ac.analyze_component(
        ibis=ibis, global_=global_,
        spice_type=CS.SpiceType.HSPICE,
        iterate=0, cleanup=0,
        spice_command="run",
    )
    assert rc1 == 0
    assert sig.model.hasBeenAnalyzed == 1

    # Second run should skip (no series model), keeping hasBeenAnalyzed == 1
    rc2 = ac.analyze_component(
        ibis=ibis, global_=global_,
        spice_type=CS.SpiceType.HSPICE,
        iterate=0, cleanup=0,
        spice_command="run",
    )
    assert rc2 == 0
    assert sig.model.hasBeenAnalyzed == 1


def test_no_transients_for_input_model(io_env):
    ibis, global_, mlist, comp, sig = io_env
    # Switch the model type to INPUT
    sig.model.modelType = CS.ModelType.INPUT

    util = S2IUtil(mlist)
    util.complete_data_structures(ibis, global_)

    # Pre-seed lists anyway; analyzer should ignore them
    sig.model.risingWaveList = [IbisWaveTable()]
    sig.model.fallingWaveList = [IbisWaveTable()]

    fake = FakeSpiceTransient(mlist)
    ap = AnalyzePin(fake)

    pwr = next(p for p in comp.pList if p.modelName.upper() == "POWER")
    gnd = next(p for p in comp.pList if p.modelName.upper() == "GND")
    en  = next(p for p in comp.pList if p.pinName == "EN")
    din = next(p for p in comp.pList if p.pinName == "DIN")

    rc = ap.analyze_pin(
        sig, en, din, pwr, gnd, pwr, gnd,
        spice_type=CS.SpiceType.HSPICE,
        spice_file="dummy.sp",
        series_spice_file="series.sp",
        spice_command="run",
        iterate=0,
        cleanup=0,
    )
    assert rc == 0
    assert fake.calls["generate_ramp_data"] == []
    assert fake.calls["generate_wave_data"] == []

def test_waveform_cap_by_constant(io_env):
    ibis, global_, mlist, comp, sig = io_env
    util = S2IUtil(mlist)
    util.complete_data_structures(ibis, global_)

    # Pre-seed more than allowed
    N = CS.MAX_WAVEFORM_TABLES + 3
    sig.model.risingWaveList  = [IbisWaveTable() for _ in range(N)]
    sig.model.fallingWaveList = [IbisWaveTable() for _ in range(N)]

    fake = FakeSpiceTransient(mlist)
    ap = AnalyzePin(fake)

    pwr = next(p for p in comp.pList if p.modelName.upper() == "POWER")
    gnd = next(p for p in comp.pList if p.modelName.upper() == "GND")
    en  = next(p for p in comp.pList if p.pinName == "EN")
    din = next(p for p in comp.pList if p.pinName == "DIN")

    rc = ap.analyze_pin(
        sig, en, din, pwr, gnd, pwr, gnd,
        spice_type=CS.SpiceType.HSPICE,
        spice_file="dummy.sp",
        series_spice_file="series.sp",
        spice_command="run",
        iterate=0,
        cleanup=0,
    )
    assert rc == 0

    rising_calls = [c for c in fake.calls["generate_wave_data"] if c["curve_type"] == CS.CurveType.RISING_WAVE]
    falling_calls = [c for c in fake.calls["generate_wave_data"] if c["curve_type"] == CS.CurveType.FALLING_WAVE]
    assert len(rising_calls) == CS.MAX_WAVEFORM_TABLES
    assert len(falling_calls) == CS.MAX_WAVEFORM_TABLES