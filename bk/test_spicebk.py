# tests/test_spice.py
import pytest
import sys
import os
import math
sys.path.insert(0, "C:\\Users\\sh3qm\\PycharmProjects\\s2ibispy")
from parser import S2IParser
from s2iutil import S2IUtil
from s2ispice import S2ISpice, SpiceVT, BinParams
from s2i_constants import ConstantStuff as CS
from models import IbisTypMinMax, IbisPin, IbisModel, IbisVItable, IbisWaveTable, IbisVItableEntry, IbisWaveTableEntry, IbisComponent, IbisGlobal

PROJECT_ROOT = "C:\\Users\\sh3qm\\PycharmProjects\\s2ibispy"

@pytest.fixture
def setup_spice():
    parser = S2IParser()
    ibis, global_ = parser.parse(os.path.join(PROJECT_ROOT, "tests", "buffer.s2i"))
    util = S2IUtil(parser.mList)
    util.complete_data_structures(ibis, global_)
    spice = S2ISpice(parser.mList, hspice_path="C:\\synopsys\\Hspice_T-2022.06\\WIN64\\hspice.com")
    return ibis, global_, spice

def test_generate_vi_curve(setup_spice):
    ibis, global_, spice = setup_spice
    pin = next(p for c in ibis.cList for p in c.pList if p.modelName == "driver")
    input_pin = next(p for c in ibis.cList for p in c.pList if p.modelName == "dummy")
    power_pin = next(p for c in ibis.cList for p in c.pList if p.modelName == "POWER")
    gnd_pin = next(p for c in ibis.cList for p in c.pList if p.modelName == "GND")
    result = spice.generate_vi_curve(pin, None, input_pin, power_pin, gnd_pin, None, None,
        global_.voltageRange, IbisTypMinMax(0.0, 0.0, 0.0), global_.voltageRange,
        IbisTypMinMax(0.0, 0.0, 0.0), IbisTypMinMax(-3.3, -3.0, -3.6), 6.6, 0.09999999999999999,
        CS.CurveType.PULLUP, "", 1, 1, 0, 0, 0.0, 0)
    assert result == 0
    assert os.path.exists("putout.spi")
    assert pin.model.pullupData.size > 0

def test_generate_ramp_data(setup_spice):
    ibis, global_, spice = setup_spice
    pin = next(p for c in ibis.cList for p in c.pList if p.modelName == "driver")
    input_pin = next(p for c in ibis.cList for p in c.pList if p.modelName == "dummy")
    power_pin = next(p for c in ibis.cList for p in c.pList if p.modelName == "POWER")
    gnd_pin = next(p for c in ibis.cList for p in c.pList if p.modelName == "GND")
    result = spice.generate_ramp_data(pin, None, input_pin, power_pin, gnd_pin, None, None,
        global_.voltageRange, IbisTypMinMax(0.0, 0.0, 0.0), global_.voltageRange,
        IbisTypMinMax(0.0, 0.0, 0.0), CS.CurveType.RISING_RAMP, "", 0, 1)
    assert result == 0
    assert os.path.exists("rutout.spi")
    assert not math.isnan(pin.model.ramp.dv_r.typ)
    assert not math.isnan(pin.model.ramp.dt_r.typ)

def test_generate_wave_data(setup_spice):
    ibis, global_, spice = setup_spice
    pin = next(p for c in ibis.cList for p in c.pList if p.modelName == "driver")
    input_pin = next(p for c in ibis.cList for p in c.pList if p.modelName == "dummy")
    power_pin = next(p for c in ibis.cList for p in c.pList if p.modelName == "POWER")
    gnd_pin = next(p for c in ibis.cList for p in c.pList if p.modelName == "GND")
    result = spice.generate_wave_data(pin, None, input_pin, power_pin, gnd_pin, None, None,
        global_.voltageRange, IbisTypMinMax(0.0, 0.0, 0.0), global_.voltageRange,
        IbisTypMinMax(0.0, 0.0, 0.0), CS.CurveType.RISING_WAVE, "", 0, 1, 0)
    assert result == 0
    assert len(pin.model.risingWaveList) > 0
    assert pin.model.risingWaveList[0].size == CS.WAVE_POINTS_DEFAULT

def test_parallel_simulations(setup_spice):
    ibis, global_, spice = setup_spice
    pin = next(p for c in ibis.cList for p in c.pList if p.modelName == "driver")
    args_list = [
        (spice.setup_spice_input_file, (0, "*Test", pin.model.spice_file, pin.model.modelFile, "",
            "VOUTS2I out 0 DC 0\n", "VINS2I in 0 DC 2.0\n",
            "VCCS2I vdd 0 DC 3.3\nVGNDS2I gnd 0 DC 0\n.TEMP 27.0\n", "",
            ".DC VOUTS2I -3.3 6.6 0.1\n.PRINT DC I(VOUTS2I)\n", "test.spi")),
        (spice.call_spice, (0, "", "test.spi", "test.out", "test.msg"))
    ]
    results = spice.run_simulations(args_list)
    assert all(r == 0 for r in results)