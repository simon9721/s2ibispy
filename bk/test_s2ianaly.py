import subprocess
import sys
sys.path.append("/")
import pytest
import math
import os
from unittest.mock import patch, mock_open
from s2ianaly import AnalyzeComponent, SetupVoltages, FindSupplyPins, SortVIData, SortVISeriesData
from s2ispice import S2ISpice
from s2iutil import S2IUtil
from parser import S2IParser
from models import (
    IbisTOP, IbisGlobal, IbisComponent, IbisPin, IbisModel, IbisTypMinMax,
    IbisPinParasitics, IbisVItable, IbisVItableEntry, IbisWaveTable, IbisWaveTableEntry, IbisRamp
)
from s2i_constants import ConstantStuff as CS

@pytest.fixture
def analy_setup(tmp_path):
    """Create a test setup for AnalyzeComponent using buffer.s2i."""
    parser = S2IParser()
    s2i_file = tmp_path / "buffer.s2i"
    s2i_file.write_text("""
[IBIS Ver] 3.2
[File rev] 0
[date] April 1, 2004
[source] From MegaFLOPS Inc. layout and silicon models.
[notes] I really wouldn't try to use this driver.  It's really bad.
[disclaimer] This file is only for demonstration purposes.
[Copyright] Copyright 2004 MegaFLOPS Inc.
[cleanup]
[Spice type] hspice
[temperature range] 27 100 0
[voltage range] 3.3 3 3.6
[sim time] 3ns
[vil] 0 0 0
[vih] 3.3 3 3.6
[rload] 500
[R_pkg] 2.0m 1.0m 4.0m
[L_pkg] 0.2nH 0.1nH 0.4nH
[C_pkg] 2pF 1pF 4pF
[Component] MCM Driver 1
[manufacturer] MegaFLOPS Inc.
[Spice file] buffer.sp
[Pin]
out out out driver
-> in
in in in dummy
gnd gnd gnd GND
vdd vdd vdd POWER
[Model] driver
[Model type] output
[Polarity] Non-inverting
[Model file] hspice.mod hspice.mod hspice.mod
[c_comp] 20pf
[Rising waveform] 500 0 NA NA NA NA NA NA NA
[Falling waveform] 500 3.3 NA NA NA NA NA NA NA
[Model] dummy
[nomodel]
""")
    ibis, global_, mList = parser.parse(str(s2i_file))
    s2iutil = S2IUtil(mList=mList)
    s2ispice = S2ISpice(mList=mList, spice_type=CS.SpiceType.HSPICE)
    analy = AnalyzeComponent(s2ispice, s2iutil)
    return analy, ibis, global_, mList

@pytest.fixture
def mock_spice_files(tmp_path):
    """Create mock SPICE output files for testing."""
    mock_dir = tmp_path / "mock_spice"
    mock_dir.mkdir()
    # Mock VI data for pullup and pulldown (typ, min, max)
    for corner in ['', 'n', 'x']:
        for prefix in ['put', 'pdt']:
            with open(mock_dir / f"{prefix}out.out", "w") as f:
                f.write(
                    "****** mos model parameters\n"
                    "****** dc transfer curves tnom= 25.000 temp= 27.000 ******\n"
                    "x\n volt current\n vouts2i\n"
                    "0.0000e+00 0.0000e+00\n"
                    f"{'-1.0000e+00 -1.0000e-02' if prefix == 'pdt' else '1.0000e+00 1.0000e-02'}\n"
                    f"{'-2.0000e+00 -2.0000e-02' if prefix == 'pdt' else '2.0000e+00 2.0000e-02'}\n"
                    f"{'-3.3000e+00 -3.3000e-02' if prefix == 'pdt' else '3.3000e+00 3.3000e-02'}\n"
                )
    # Mock ramp and waveform data for rising and falling (typ, min, max)
    for corner in ['', 'n', 'x']:
        for prefix in ['rut', 'rdt']:
            with open(mock_dir / f"{prefix}{corner}out.out", "w") as f:
                f.write(
                    "****** transient analysis tnom= 25.000 temp= 27.000 ******\n"
                    "x\n time voltage\n out\n"
                    "0.0000e+00 0.0000e+00\n"
                    "1.0000e-09 6.6000e-01\n"
                    "2.0000e-09 2.6400e+00\n"
                    "3.0000e-09 3.3000e+00\n"
                )
            with open(mock_dir / f"{prefix}{corner}out0.out", "w") as f:
                f.write(
                    "****** transient analysis tnom= 25.000 temp= 27.000 ******\n"
                    "x\n time voltage\n out\n"
                    "0.0000e+00 0.0000e+00\n"
                    "5.0000e-10 3.3000e-01\n"
                    "1.0000e-09 6.6000e-01\n"
                    "1.5000e-09 1.3200e+00\n"
                    "2.0000e-09 2.6400e+00\n"
                    "3.0000e-09 3.3000e+00\n"
                )
    return mock_dir

def test_setup_voltages():
    """Test SetupVoltages.setup_voltages for buffer.s2i driver model."""
    model = IbisModel(
        modelName="driver",
        modelType=str(CS.ModelType.OUTPUT),
        voltageRange=IbisTypMinMax(3.3, 3.0, 3.6),
        pullupRef=IbisTypMinMax(3.3, 3.0, 3.6),
        pulldownRef=IbisTypMinMax(0.0, 0.0, 0.0),
        powerClampRef=IbisTypMinMax(3.3, 3.0, 3.6),
        gndClampRef=IbisTypMinMax(0.0, 0.0, 0.0),
        Rload=500.0,
        simTime=3e-9
    )
    setup_v = SetupVoltages()
    setup_v.setup_voltages(CS.CurveType.PULLUP, model)
    assert math.isclose(setup_v.vcc.typ, 3.3, rel_tol=1e-5), "Incorrect vcc for PULLUP"
    assert math.isclose(setup_v.gnd.typ, 0.0, rel_tol=1e-5), "Incorrect gnd for PULLUP"
    assert math.isclose(setup_v.sweep_start.typ, -3.3, rel_tol=1e-5), "Incorrect sweep_start for PULLUP"
    assert math.isclose(setup_v.sweep_range, 6.6, rel_tol=1e-5), "Incorrect sweep_range for PULLUP"
    setup_v.setup_voltages(CS.CurveType.GND_CLAMP, model)
    assert math.isclose(setup_v.vcc.typ, 3.3, rel_tol=1e-5), "Incorrect vcc for GND_CLAMP"
    assert math.isclose(setup_v.gnd.typ, 0.0, rel_tol=1e-5), "Incorrect gnd for GND_CLAMP"
    assert math.isclose(setup_v.sweep_start.typ, -3.3, rel_tol=1e-5), "Incorrect sweep_start for GND_CLAMP"
    assert math.isclose(setup_v.sweep_range, 6.6, rel_tol=1e-5), "Incorrect sweep_range for GND_CLAMP"

def test_find_supply_pins(analy_setup):
    """Test FindSupplyPins.find_pins for buffer.s2i."""
    analy, ibis, _, _ = analy_setup
    component = ibis.cList[0]
    assert component.pList, "No pins parsed for component"
    pin_out = next(pin for pin in component.pList if pin.pinName == "out")
    pins = FindSupplyPins().find_pins(pin_out, component.pList, False)
    assert pins is not None, "Failed to find supply pins"
    assert pins["pullupPin"].pinName == "vdd", "Incorrect pullupPin"
    assert pins["pulldownPin"].pinName == "gnd", "Incorrect pulldownPin"
    assert pins["powerClampPin"].pinName == "vdd", "Incorrect powerClampPin"
    assert pins["gndClampPin"].pinName == "gnd", "Incorrect gndClampPin"

def test_sort_vi_data():
    """Test SortVIData.sort_vi_data for buffer.s2i driver model."""
    model = IbisModel(
        modelName="driver",
        modelType=str(CS.ModelType.OUTPUT),
        voltageRange=IbisTypMinMax(3.3, 3.0, 3.6),
        derateVIPct=10.0
    )
    vi_data = IbisVItable(
        VIs=[
            IbisVItableEntry(v=0.0, i=IbisTypMinMax(0.0, 0.0, 0.0)),
            IbisVItableEntry(v=1.0, i=IbisTypMinMax(0.01, 0.009, 0.011)),
            IbisVItableEntry(v=2.0, i=IbisTypMinMax(0.02, 0.018, 0.022))
        ],
        size=3
    )
    sort_vi = SortVIData()
    result = sort_vi.sort_vi_data(model, vi_data, None, None, None)
    assert result == 0, "sort_vi_data failed"
    assert model.pullupData is not None, "pullupData not set"
    assert len(model.pullupData.VIs) == 3, "Incorrect pullupData size"
    assert math.isclose(model.pullupData.VIs[0].v, 1.3, rel_tol=1e-5), "Incorrect voltage transformation"
    assert math.isclose(model.pullupData.VIs[0].i.typ, 0.02, rel_tol=1e-5), "Incorrect typical current"
    assert math.isclose(model.pullupData.VIs[0].i.min, 0.018 * 0.9, rel_tol=1e-5), "Incorrect min current with derating"

@patch('os.path.exists', return_value=True)
@patch('shutil.copy', return_value=None)
@patch('s2ispice.subprocess.run')
@patch('builtins.open', new_callable=mock_open)
def test_analyze_pin(mock_open, mock_subprocess, mock_copy, mock_exists, analy_setup, mock_spice_files):
    """Test AnalyzePin.analyze_pin with mock SPICE outputs for buffer.s2i."""
    analy, ibis, global_, mList = analy_setup
    component = ibis.cList[0]
    assert component.pList, "No pins parsed for component"
    pin_out = next(pin for pin in component.pList if pin.pinName == "out")
    pin_in = next(pin for pin in component.pList if pin.pinName == "in")
    pin_vdd = next(pin for pin in component.pList if pin.pinName == "vdd")
    pin_gnd = next(pin for pin in component.pList if pin.pinName == "gnd")
    mock_subprocess.return_value = subprocess.CompletedProcess(
        args=['hspice'], returncode=0, stdout='', stderr=''
    )
    # Mock file operations for all corners (typ, min, max) and curves
    file_data = {
        'putout.out': (
            "****** mos model parameters\n"
            "****** dc transfer curves tnom= 25.000 temp= 27.000 ******\n"
            "x\n volt current\n vouts2i\n"
            "0.0000e+00 0.0000e+00\n"
            "1.0000e+00 1.0000e-02\n"
            "2.0000e+00 2.0000e-02\n"
            "3.3000e+00 3.3000e-02\n"
        ),
        'punout.out': (
            "****** mos model parameters\n"
            "****** dc transfer curves tnom= 25.000 temp= 27.000 ******\n"
            "x\n volt current\n vouts2i\n"
            "0.0000e+00 0.0000e+00\n"
            "1.0000e+00 1.0000e-02\n"
            "2.0000e+00 2.0000e-02\n"
            "3.3000e+00 3.3000e-02\n"
        ),
        'puxout.out': (
            "****** mos model parameters\n"
            "****** dc transfer curves tnom= 25.000 temp= 27.000 ******\n"
            "x\n volt current\n vouts2i\n"
            "0.0000e+00 0.0000e+00\n"
            "1.0000e+00 1.0000e-02\n"
            "2.0000e+00 2.0000e-02\n"
            "3.3000e+00 3.3000e-02\n"
        ),
        'pdtout.out': (
            "****** mos model parameters\n"
            "****** dc transfer curves tnom= 25.000 temp= 27.000 ******\n"
            "x\n volt current\n vouts2i\n"
            "0.0000e+00 0.0000e+00\n"
            "-1.0000e+00 -1.0000e-02\n"
            "-2.0000e+00 -2.0000e-02\n"
            "-3.3000e+00 -3.3000e-02\n"
        ),
        'pdnout.out': (
            "****** mos model parameters\n"
            "****** dc transfer curves tnom= 25.000 temp= 27.000 ******\n"
            "x\n volt current\n vouts2i\n"
            "0.0000e+00 0.0000e+00\n"
            "-1.0000e+00 -1.0000e-02\n"
            "-2.0000e+00 -2.0000e-02\n"
            "-3.3000e+00 -3.3000e-02\n"
        ),
        'pdxout.out': (
            "****** mos model parameters\n"
            "****** dc transfer curves tnom= 25.000 temp= 27.000 ******\n"
            "x\n volt current\n vouts2i\n"
            "0.0000e+00 0.0000e+00\n"
            "-1.0000e+00 -1.0000e-02\n"
            "-2.0000e+00 -2.0000e-02\n"
            "-3.3000e+00 -3.3000e-02\n"
        ),
        'rutout.out': (
            "****** transient analysis tnom= 25.000 temp= 27.000 ******\n"
            "x\n time voltage\n out\n"
            "0.0000e+00 0.0000e+00\n"
            "1.0000e-09 6.6000e-01\n"
            "2.0000e-09 2.6400e+00\n"
            "3.0000e-09 3.3000e+00\n"
        ),
        'runout.out': (
            "****** transient analysis tnom= 25.000 temp= 27.000 ******\n"
            "x\n time voltage\n out\n"
            "0.0000e+00 0.0000e+00\n"
            "1.0000e-09 6.6000e-01\n"
            "2.0000e-09 2.6400e+00\n"
            "3.0000e-09 3.3000e+00\n"
        ),
        'ruxout.out': (
            "****** transient analysis tnom= 25.000 temp= 27.000 ******\n"
            "x\n time voltage\n out\n"
            "0.0000e+00 0.0000e+00\n"
            "1.0000e-09 6.6000e-01\n"
            "2.0000e-09 2.6400e+00\n"
            "3.0000e-09 3.3000e+00\n"
        ),
        'rdtout.out': (
            "****** transient analysis tnom= 25.000 temp= 27.000 ******\n"
            "x\n time voltage\n out\n"
            "0.0000e+00 0.0000e+00\n"
            "1.0000e-09 6.6000e-01\n"
            "2.0000e-09 2.6400e+00\n"
            "3.0000e-09 3.3000e+00\n"
        ),
        'rdnout.out': (
            "****** transient analysis tnom= 25.000 temp= 27.000 ******\n"
            "x\n time voltage\n out\n"
            "0.0000e+00 0.0000e+00\n"
            "1.0000e-09 6.6000e-01\n"
            "2.0000e-09 2.6400e+00\n"
            "3.0000e-09 3.3000e+00\n"
        ),
        'rdxout.out': (
            "****** transient analysis tnom= 25.000 temp= 27.000 ******\n"
            "x\n time voltage\n out\n"
            "0.0000e+00 0.0000e+00\n"
            "1.0000e-09 6.6000e-01\n"
            "2.0000e-09 2.6400e+00\n"
            "3.0000e-09 3.3000e+00\n"
        ),
        'rutout0.out': (
            "****** transient analysis tnom= 25.000 temp= 27.000 ******\n"
            "x\n time voltage\n out\n"
            "0.0000e+00 0.0000e+00\n"
            "5.0000e-10 3.3000e-01\n"
            "1.0000e-09 6.6000e-01\n"
            "1.5000e-09 1.3200e+00\n"
            "2.0000e-09 2.6400e+00\n"
            "3.0000e-09 3.3000e+00\n"
        ),
        'runout0.out': (
            "****** transient analysis tnom= 25.000 temp= 27.000 ******\n"
            "x\n time voltage\n out\n"
            "0.0000e+00 0.0000e+00\n"
            "5.0000e-10 3.3000e-01\n"
            "1.0000e-09 6.6000e-01\n"
            "1.5000e-09 1.3200e+00\n"
            "2.0000e-09 2.6400e+00\n"
            "3.0000e-09 3.3000e+00\n"
        ),
        'ruxout0.out': (
            "****** transient analysis tnom= 25.000 temp= 27.000 ******\n"
            "x\n time voltage\n out\n"
            "0.0000e+00 0.0000e+00\n"
            "5.0000e-10 3.3000e-01\n"
            "1.0000e-09 6.6000e-01\n"
            "1.5000e-09 1.3200e+00\n"
            "2.0000e-09 2.6400e+00\n"
            "3.0000e-09 3.3000e+00\n"
        ),
        'rdtout0.out': (
            "****** transient analysis tnom= 25.000 temp= 27.000 ******\n"
            "x\n time voltage\n out\n"
            "0.0000e+00 0.0000e+00\n"
            "5.0000e-10 3.3000e-01\n"
            "1.0000e-09 6.6000e-01\n"
            "1.5000e-09 1.3200e+00\n"
            "2.0000e-09 2.6400e+00\n"
            "3.0000e-09 3.3000e+00\n"
        ),
        'rdnout0.out': (
            "****** transient analysis tnom= 25.000 temp= 27.000 ******\n"
            "x\n time voltage\n out\n"
            "0.0000e+00 0.0000e+00\n"
            "5.0000e-10 3.3000e-01\n"
            "1.0000e-09 6.6000e-01\n"
            "1.5000e-09 1.3200e+00\n"
            "2.0000e-09 2.6400e+00\n"
            "3.0000e-09 3.3000e+00\n"
        ),
        'rdxout0.out': (
            "****** transient analysis tnom= 25.000 temp= 27.000 ******\n"
            "x\n time voltage\n out\n"
            "0.0000e+00 0.0000e+00\n"
            "5.0000e-10 3.3000e-01\n"
            "1.0000e-09 6.6000e-01\n"
            "1.5000e-09 1.3200e+00\n"
            "2.0000e-09 2.6400e+00\n"
            "3.0000e-09 3.3000e+00\n"
        )
    }
    def mock_open_file(*args, **kwargs):
        filename = args[0] if args else kwargs.get('file', '')
        base_name = os.path.basename(filename)
        if base_name in file_data:
            mock = mock_open(read_data=file_data[base_name])()
            mock.read.return_value = file_data[base_name]
            return mock
        return mock_open()()
    mock_open.side_effect = mock_open_file
    # Log mock data for debugging
    for filename in file_data:
        print(f"Mock data for {filename}:\n{file_data[filename]}")
    analy.s2ispice.mock_dir = str(mock_spice_files)
    result = analy.analyze_component(ibis, global_, CS.SpiceType.HSPICE, 0, 1, "")
    assert result <= 6, "analyze_component failed with unexpected error count"
    model = pin_out.model
    assert model.pullupData is not None, "pullupData not generated"
    assert model.pullupData.size == 4, "Incorrect pullupData size"
    assert model.pulldownData is not None, "pulldownData not generated"
    assert model.pulldownData.size == 4, "Incorrect pulldownData size"
    assert model.ramp is not None, "ramp not generated"
    assert math.isclose(model.ramp.dv_r.typ, 3.3, rel_tol=1e-5), "Incorrect rising ramp dv"
    assert math.isclose(model.ramp.dt_r.typ, 2e-9, rel_tol=1e-5), "Incorrect rising ramp dt"
    assert len(model.risingWaveList) >= 1, "Incorrect rising waveform count"
    assert model.risingWaveList[0].size == 6, "Incorrect rising waveform size"
