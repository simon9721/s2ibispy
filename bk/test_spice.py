import pytest
import sys
import os
import math
import glob

# Resolve repo root relative to this file (portable)
HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(HERE, os.pardir))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from parser import S2IParser
from s2iutil import S2IUtil
from s2ispice import S2ISpice
from s2i_constants import ConstantStuff as CS
from models import IbisTypMinMax

@pytest.fixture
def setup_spice(tmp_path):
    """
    Build parser/util/spice, run from a temp work dir so artifacts are isolated.
    """
    # Work under tmp so generated .spi/.out land in a predictable place
    cwd = os.getcwd()
    os.chdir(tmp_path)

    parser = S2IParser()
    # sample file lives in tests/
    s2i_path = os.path.join(PROJECT_ROOT, "tests", "buffer.s2i")
    ibis, global_, m_list = parser.parse(s2i_path)

    util = S2IUtil(parser.mList)  # same list as m_list
    util.complete_data_structures(ibis, global_)

    # Use your default HSPICE path if available; otherwise the class will fall back to mock files
    spice = S2ISpice(parser.mList, hspice_path=os.environ.get("HSPICE_PATH", "hspice"))

    try:
        yield ibis, global_, spice, tmp_path
    finally:
        os.chdir(cwd)

def _assert_any_exists(patterns):
    """
    Pass a list of filename patterns; assert at least one exists.
    Useful when code may or may not suffix indices.
    """
    for pat in patterns:
        matches = glob.glob(pat)
        if matches:
            return
    raise AssertionError(f"None of the expected files found: {patterns}")

def _get_pin(ibis, model_name):
    return next(p for c in ibis.cList for p in c.pList if p.modelName == model_name)

def test_generate_vi_curve(setup_spice):
    ibis, global_, spice, tmp_path = setup_spice

    pin = _get_pin(ibis, "driver")
    input_pin = _get_pin(ibis, "dummy")
    power_pin = _get_pin(ibis, "POWER")
    gnd_pin = _get_pin(ibis, "GND")

    result = spice.generate_vi_curve(
        pin, None, input_pin, power_pin, gnd_pin, None, None,
        global_.voltageRange, IbisTypMinMax(0.0, 0.0, 0.0), global_.voltageRange,
        IbisTypMinMax(0.0, 0.0, 0.0), IbisTypMinMax(-3.3, -3.0, -3.6),
        6.6, 0.1, CS.CurveType.PULLUP, "", 1, 1, 0, 0, 0.0, 0
    )
    assert result == 0

    # Accept either unsuffixed or suffixed filenames
    _assert_any_exists([
        os.path.join(tmp_path, "putout.spi"),
        os.path.join(tmp_path, "put00out.spi"),
        os.path.join(tmp_path, "put0out.spi"),
    ])

    assert pin.model.pullupData is not None
    assert pin.model.pullupData.size > 0

def test_generate_ramp_data(setup_spice):
    ibis, global_, spice, tmp_path = setup_spice

    pin = _get_pin(ibis, "driver")
    input_pin = _get_pin(ibis, "dummy")
    power_pin = _get_pin(ibis, "POWER")
    gnd_pin = _get_pin(ibis, "GND")

    result = spice.generate_ramp_data(
        pin, None, input_pin, power_pin, gnd_pin, None, None,
        global_.voltageRange, IbisTypMinMax(0.0, 0.0, 0.0), global_.voltageRange,
        IbisTypMinMax(0.0, 0.0, 0.0), CS.CurveType.RISING_RAMP, "", 0, 1
    )
    assert result == 0

    _assert_any_exists([
        os.path.join(tmp_path, "rutout.spi"),
        os.path.join(tmp_path, "rut00out.spi"),
        os.path.join(tmp_path, "rut0out.spi"),
    ])

    assert not math.isnan(pin.model.ramp.dv_r.typ)
    assert not math.isnan(pin.model.ramp.dt_r.typ)

def test_generate_wave_data(setup_spice):
    ibis, global_, spice, tmp_path = setup_spice

    pin = _get_pin(ibis, "driver")
    input_pin = _get_pin(ibis, "dummy")
    power_pin = _get_pin(ibis, "POWER")
    gnd_pin = _get_pin(ibis, "GND")

    result = spice.generate_wave_data(
        pin, None, input_pin, power_pin, gnd_pin, None, None,
        global_.voltageRange, IbisTypMinMax(0.0, 0.0, 0.0), global_.voltageRange,
        IbisTypMinMax(0.0, 0.0, 0.0), CS.CurveType.RISING_WAVE, "", 0, 1, 0
    )
    assert result == 0

    assert len(pin.model.risingWaveList) > 0
    assert pin.model.risingWaveList[0].size == CS.WAVE_POINTS_DEFAULT

def test_sequential_simulations(setup_spice):
    """
    Run two simple steps sequentially using run_simulations(). If your S2ISpice
    gets updated to suffix indices, this still passes.
    """
    ibis, global_, spice, tmp_path = setup_spice
    pin = _get_pin(ibis, "driver")

    # First, set up a tiny DC deck
    args_list = [
        (
            spice.setup_spice_input_file,
            (
                0, "*Test\n", pin.model.spice_file or "buffer.sp",
                pin.model.modelFile, "",
                "VOUTS2I out 0 DC 0\n", "VINS2I in 0 DC 2.0\n",
                "VCCS2I vdd 0 DC 3.3\nVGNDS2I gnd 0 DC 0\n.TEMP 27.0\n",
                "",
                ".DC VOUTS2I -3.3 6.6 0.1\n.PRINT DC I(VOUTS2I)\n",
                "test.spi",
            ),
        ),
        (spice.call_spice, (0, "", "test.spi", "test.out", "test.msg")),
    ]
    results = spice.run_simulations(args_list)
    assert all(r == 0 for r in results)

    assert os.path.exists(os.path.join(tmp_path, "test.spi"))
    # Either a real out or a copied mock should exist after call_spice
    assert os.path.exists(os.path.join(tmp_path, "test.out")) or os.path.exists(os.path.join(tmp_path, "test.lis"))
