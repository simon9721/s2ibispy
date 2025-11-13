import pytest
import os
import tempfile
import math
from parser import S2IParser
from models import IbisTOP, IbisGlobal, IbisComponent, IbisPin, IbisModel, IbisTypMinMax, IbisPinParasitics, IbisDiffPin, IbisSeriesPin, IbisSeriesSwitchGroup, SeriesModel
from s2i_constants import ConstantStuff as CS

@pytest.fixture
def parser():
    """Create a new S2IParser instance."""
    return S2IParser()

@pytest.fixture
def temp_s2i_file(tmp_path):
    """Create a temporary .s2i file for testing."""
    file_path = tmp_path / "test.s2i"
    file_path.write_text("""
[IBIS Ver] 3.2
[File Name] test.ibs
[File Rev] 1.0
[Date] Fri Oct 17 2025
[Source] Test source
[Notes] Test notes
[Copyright] Test copyright
[Spice Type] hspice
[Temperature Range] 25.0 0.0 70.0
[Voltage Range] 3.3 3.0 3.6
[Pullup Reference] 3.3
[Pulldown Reference] 0.0
[Power Clamp Reference] 3.3
[GND Clamp Reference] 0.0
[Vil] 0.8
[Vih] 2.0
[Rload] 50.0
[Sim Time] 1n
[Derate VI] 10.0
[Derate Ramp] 5.0
[Component] test_comp
[Manufacturer] test_mfg
[Spice File] test.sp
[Pin]
1 SIG1 NC test_model
-> IN1 EN1
2 SIG2 NC POWER
3 SIG3 NC GND
[Diff Pin]
2 0.2 1n
[Series Pin Mapping]
1 2 series_model
[Model] test_model
[Model Type] io
[Polarity] non-inverting
[Enable] active-high
[Model File] model.sp
[Spice File] model.sp
[Rising Waveform] 50.0 3.3
[Falling Waveform] 50.0 0.0
[Series MOSFET]
[Vds] 1.0
[On]
[Model] series_model
[Model Type] series
[Off]
[R Series] 1M
    """)
    yield str(file_path)

def test_parse_basic_info(parser, temp_s2i_file):
    """Test parsing of basic IBIS file information."""
    ibis, global_, mList = parser.parse(temp_s2i_file)
    assert ibis.ibisVersion == "3.2", "Incorrect IBIS version"
    assert ibis.thisFileName == "test.ibs", "Incorrect file name"
    assert ibis.fileRev == "1.0", "Incorrect file revision"
    assert ibis.source == "Test source", "Incorrect source"
    assert ibis.notes == "Test notes", "Incorrect notes"
    assert ibis.copyright == "Test copyright", "Incorrect copyright"
    assert ibis.spiceType == CS.SpiceType.HSPICE, "Incorrect spice type"
    assert global_.tempRange.typ == 25.0, "Incorrect tempRange typ"
    assert global_.voltageRange.typ == 3.3, "Incorrect voltageRange typ"
    assert global_.pullupRef.typ == 3.3, "Incorrect pullupRef typ"
    assert global_.pulldownRef.typ == 0.0, "Incorrect pulldownRef typ"
    assert global_.vil.typ == 0.8, "Incorrect vil typ"
    assert global_.vih.typ == 2.0, "Incorrect vih typ"
    assert global_.Rload == 50.0, "Incorrect Rload"
    assert global_.simTime == 1e-9, "Incorrect simTime"
    assert global_.derateVIPct == 10.0, "Incorrect derateVIPct"
    assert global_.derateRampPct == 5.0, "Incorrect derateRampPct"

def test_parse_component_and_pins(parser, temp_s2i_file):
    """Test parsing of component and pin data."""
    ibis, _, _ = parser.parse(temp_s2i_file)
    assert len(ibis.cList) == 1, "Incorrect component count"
    comp = ibis.cList[0]
    assert comp.component == "test_comp", "Incorrect component name"
    assert comp.manufacturer == "test_mfg", "Incorrect manufacturer"
    assert comp.spiceFile == "test.sp", "Incorrect spice file"
    assert len(comp.pList) == 3, "Incorrect pin count"
    pin1 = comp.pList[0]
    assert pin1.pinName == "1", "Incorrect pin name"
    assert pin1.signalName == "SIG1", "Incorrect signal name"
    assert pin1.modelName == "test_model", "Incorrect model name"
    assert pin1.inputPin == "IN1", "Incorrect input pin"
    assert pin1.enablePin == "EN1", "Incorrect enable pin"
    pin2 = comp.pList[1]
    assert pin2.pinName == "2", "Incorrect pin name"
    assert pin2.signalName == "SIG2", "Incorrect signal name"
    assert pin2.modelName == "POWER", "Incorrect model name"
    pin3 = comp.pList[2]
    assert pin3.pinName == "3", "Incorrect pin name"
    assert pin3.signalName == "SIG3", "Incorrect signal name"
    assert pin3.modelName == "GND", "Incorrect model name"
    assert len(comp.dpList) == 1, "Incorrect diff pin count"
    assert comp.dpList[0].invPin == "2", "Incorrect diff pin invPin"
    assert len(comp.spList) == 1, "Incorrect series pin count"
    assert comp.spList[0].pin1 == "1", "Incorrect series pin1"
    assert comp.spList[0].pin2 == "2", "Incorrect series pin2"

def test_parse_models(parser, temp_s2i_file):
    """Test parsing of model and series model data."""
    _, _, mList = parser.parse(temp_s2i_file)
    assert len(mList) == 2, "Incorrect model count"
    model = mList[0]
    assert model.modelName == "test_model", "Incorrect model name"
    assert model.modelType == str(CS.ModelType.IO), "Incorrect model type"
    assert model.polarity == "non-inverting", "Incorrect polarity"
    assert model.enable == "active-high", "Incorrect enable"
    assert model.spice_file == "model.sp", "Incorrect spice file"
    assert len(model.risingWaveList) == 1, "Incorrect rising waveform count"
    assert model.risingWaveList[0].R_fixture == 50.0, "Incorrect R_fixture"
    assert model.risingWaveList[0].V_fixture == 3.3, "Incorrect V_fixture"
    series_model = mList[1]
    assert series_model.modelName == "series_model", "Incorrect series model name"
    assert series_model.modelType == str(CS.ModelType.SERIES), "Incorrect series model type"
    assert series_model.seriesModel.OnState is True, "Incorrect series OnState"
    assert series_model.seriesModel.vdslist == [1.0], "Incorrect vdslist"
    assert series_model.seriesModel.RSeriesOff.typ == 1e6, "Incorrect RSeriesOff"

def test_parse_invalid_file(parser):
    """Test parsing of non-existent file."""
    with pytest.raises(FileNotFoundError, match="No such file or directory: 'invalid.s2i'"):
        parser.parse("invalid.s2i")

def test_parse_invalid_pin_data(tmp_path):
    """Test parsing with invalid pin data."""
    file_path = tmp_path / "invalid.s2i"
    file_path.write_text("""
[Component] test_comp
[Pin]
1 SIG1 NC  # Invalid: missing modelName
    """)
    parser = S2IParser()
    ibis, _, _ = parser.parse(str(file_path))
    assert len(ibis.cList) == 1, "Should parse component"
    assert len(ibis.cList[0].pList) == 0, "Should skip invalid pin"

def test_parse_empty_file(tmp_path):
    """Test parsing of empty file."""
    file_path = tmp_path / "empty.s2i"
    file_path.write_text("")
    parser = S2IParser()
    ibis, global_, mList = parser.parse(str(file_path))
    assert len(ibis.cList) == 0, "cList should be empty"
    assert len(mList) == 0, "mList should be empty"
    assert math.isnan(global_.tempRange.typ), "tempRange should be nan"
