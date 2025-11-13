import pytest
import math
from models import (
    IbisTypMinMax, SeriesModel, IbisPin, IbisModel, IbisRamp, IbisVItableEntry,
    IbisVItable, IbisWaveTableEntry, IbisWaveTable, IbisComponent, IbisDiffPin,
    IbisSeriesPin, IbisSeriesSwitchGroup, IbisGlobal, IbisPinParasitics, IbisTOP
)
from s2i_constants import ConstantStuff as CS

def test_ibis_typ_min_max():
    """Test IbisTypMinMax initialization and defaults."""
    tmm = IbisTypMinMax()
    assert math.isnan(tmm.typ), "typ should be nan by default"
    assert math.isnan(tmm.min), "min should be nan by default"
    assert math.isnan(tmm.max), "max should be nan by default"
    tmm = IbisTypMinMax(1.0, 0.9, 1.1)
    assert tmm.typ == 1.0, "Incorrect typ value"
    assert tmm.min == 0.9, "Incorrect min value"
    assert tmm.max == 1.1, "Incorrect max value"

def test_series_model():
    """Test SeriesModel initialization and post_init."""
    sm = SeriesModel()
    assert sm.OnState is False, "OnState should be False"
    assert sm.OffState is True, "OffState should be True"
    assert sm.RSeriesOff.typ == CS.R_SERIES_DEFAULT, "Incorrect RSeriesOff typ"
    assert sm.vdslist == [], "vdslist should be empty list"
    sm = SeriesModel(OnState=True, vdslist=[1.0, 2.0])
    assert sm.OnState is True, "OnState should be True"
    assert sm.vdslist == [1.0, 2.0], "Incorrect vdslist"

def test_ibis_pin():
    """Test IbisPin initialization."""
    model = IbisModel(modelName="test", modelType=str(CS.ModelType.IO))
    pin = IbisPin(pinName="P1", signalName="SIG1", modelName="test", model=model, enablePin="EN", inputPin="IN")
    assert pin.pinName == "P1", "Incorrect pinName"
    assert pin.signalName == "SIG1", "Incorrect signalName"
    assert pin.modelName == "test", "Incorrect modelName"
    assert pin.model == model, "Incorrect model"
    assert pin.enablePin == "EN", "Incorrect enablePin"
    assert pin.inputPin == "IN", "Incorrect inputPin"
    assert pin.spiceNodeName == "", "Incorrect spiceNodeName"
    assert pin.seriesPin2name == "", "Incorrect seriesPin2name"

def test_ibis_model():
    """Test IbisModel initialization and post_init."""
    model = IbisModel(modelName="test", modelType=str(CS.ModelType.IO))
    assert model.modelName == "test", "Incorrect modelName"
    assert model.modelType == str(CS.ModelType.IO), "Incorrect modelType"
    assert model.risingWaveList == [], "risingWaveList should be empty"
    assert model.fallingWaveList == [], "fallingWaveList should be empty"
    assert model.seriesVITables == [], "seriesVITables should be empty"
    assert math.isnan(model.tempRange.typ), "tempRange should be nan"  # Fixed nan comparison
    assert model.derateVIPct == 0.0, "derateVIPct should be 0.0"
    assert model.hasBeenAnalyzed == 0, "hasBeenAnalyzed should be 0"

def test_ibis_ramp():
    """Test IbisRamp initialization."""
    ramp = IbisRamp(dv_r=IbisTypMinMax(1.0), dt_r=IbisTypMinMax(2.0), dv_f=IbisTypMinMax(3.0), dt_f=IbisTypMinMax(4.0), derateRampPct=10.0)
    assert ramp.dv_r.typ == 1.0, "Incorrect dv_r typ"
    assert ramp.dt_r.typ == 2.0, "Incorrect dt_r typ"
    assert ramp.dv_f.typ == 3.0, "Incorrect dv_f typ"
    assert ramp.dt_f.typ == 4.0, "Incorrect dt_f typ"
    assert ramp.derateRampPct == 10.0, "Incorrect derateRampPct"

def test_ibis_vi_table_entry():
    """Test IbisVItableEntry initialization."""
    entry = IbisVItableEntry(v=1.5, i=IbisTypMinMax(0.1, 0.09, 0.11))
    assert entry.v == 1.5, "Incorrect voltage"
    assert entry.i.typ == 0.1, "Incorrect typ current"
    assert entry.i.min == 0.09, "Incorrect min current"
    assert entry.i.max == 0.11, "Incorrect max current"

def test_ibis_vi_table():
    """Test IbisVItable initialization."""
    entry = IbisVItableEntry(v=1.5, i=IbisTypMinMax(0.1))
    table = IbisVItable(VIs=[entry], size=1)
    assert len(table.VIs) == 1, "Incorrect VIs length"
    assert table.VIs[0].v == 1.5, "Incorrect voltage"
    assert table.size == 1, "Incorrect table size"

def test_ibis_wave_table_entry():
    """Test IbisWaveTableEntry initialization."""
    entry = IbisWaveTableEntry(t=1e-9, v=IbisTypMinMax(1.0, 0.9, 1.1))
    assert entry.t == 1e-9, "Incorrect time"
    assert entry.v.typ == 1.0, "Incorrect typ voltage"
    assert entry.v.min == 0.9, "Incorrect min voltage"
    assert entry.v.max == 1.1, "Incorrect max voltage"

def test_ibis_wave_table():
    """Test IbisWaveTable initialization."""
    entry = IbisWaveTableEntry(t=1e-9, v=IbisTypMinMax(1.0))
    table = IbisWaveTable(waveData=[entry], size=1, R_fixture=50.0, V_fixture=3.3)
    assert len(table.waveData) == 1, "Incorrect waveData length"
    assert table.waveData[0].t == 1e-9, "Incorrect time"
    assert table.size == 1, "Incorrect table size"
    assert table.R_fixture == 50.0, "Incorrect R_fixture"
    assert table.V_fixture == 3.3, "Incorrect V_fixture"
    assert math.isnan(table.V_fixture_min), "V_fixture_min should be nan"

def test_ibis_component():
    """Test IbisComponent initialization."""
    pin = IbisPin(pinName="P1", signalName="SIG1", modelName="test", model=None)
    comp = IbisComponent(component="test_comp", manufacturer="test_mfg", pList=[pin], spiceFile="test.sp")
    assert comp.component == "test_comp", "Incorrect component name"
    assert comp.manufacturer == "test_mfg", "Incorrect manufacturer"
    assert len(comp.pList) == 1, "Incorrect pList length"
    assert comp.spiceFile == "test.sp", "Incorrect spiceFile"
    assert comp.seriesSpiceFile == "", "Incorrect seriesSpiceFile"
    assert comp.hasPinMapping is False, "Incorrect hasPinMapping"

def test_ibis_diff_pin():
    """Test IbisDiffPin initialization."""
    dp = IbisDiffPin(invPin="P2", vdiff=IbisTypMinMax(0.2), tdelay=IbisTypMinMax(1e-9))
    assert dp.invPin == "P2", "Incorrect invPin"
    assert dp.vdiff.typ == 0.2, "Incorrect vdiff typ"
    assert dp.tdelay.typ == 1e-9, "Incorrect tdelay typ"

def test_ibis_series_pin():
    """Test IbisSeriesPin initialization."""
    sp = IbisSeriesPin(pin1="P1", pin2="P2", modelName="series_model")
    assert sp.pin1 == "P1", "Incorrect pin1"
    assert sp.pin2 == "P2", "Incorrect pin2"
    assert sp.modelName == "series_model", "Incorrect modelName"

def test_ibis_series_switch_group():
    """Test IbisSeriesSwitchGroup initialization."""
    ssg = IbisSeriesSwitchGroup(pins=["P1", "P2"])
    assert ssg.pins == ["P1", "P2"], "Incorrect pins list"

def test_ibis_global():
    """Test IbisGlobal initialization and post_init."""
    global_ = IbisGlobal(
        tempRange=IbisTypMinMax(25.0),
        voltageRange=IbisTypMinMax(3.3),
        pullupRef=IbisTypMinMax(3.3),
        pulldownRef=IbisTypMinMax(0.0),
        powerClampRef=IbisTypMinMax(3.3),
        gndClampRef=IbisTypMinMax(0.0),
        vil=IbisTypMinMax(0.8),
        vih=IbisTypMinMax(2.0),
        Rload=50.0,
        simTime=1e-9,
        pinParasitics=IbisPinParasitics(IbisTypMinMax(), IbisTypMinMax(), IbisTypMinMax()),
        derateVIPct=10.0
    )
    assert global_.tempRange.typ == 25.0, "Incorrect tempRange typ"
    assert global_.voltageRange.typ == 3.3, "Incorrect voltageRange typ"
    assert global_.Rload == 50.0, "Incorrect Rload"
    assert global_.simTime == 1e-9, "Incorrect simTime"
    assert global_.derateVIPct == 10.0, "Incorrect derateVIPct"
    assert math.isnan(global_.tr.typ), "tr should be nan"  # Fixed nan comparison
    assert global_.commentChar == "|", "Incorrect commentChar"

def test_ibis_top():
    """Test IbisTOP initialization."""
    comp = IbisComponent(component="test_comp", manufacturer="test_mfg", pList=[])
    top = IbisTOP(
        ibisVersion="3.2",
        thisFileName="test.ibs",
        fileRev="0",
        date="Fri Oct 17 2025",
        source="test",
        notes="",
        disclaimer="",
        copyright="",
        cList=[comp],
        spiceType=CS.SpiceType.HSPICE
    )
    assert top.ibisVersion == "3.2", "Incorrect ibisVersion"
    assert top.thisFileName == "test.ibs", "Incorrect thisFileName"
    assert top.spiceType == CS.SpiceType.HSPICE, "Incorrect spiceType"
    assert len(top.cList) == 1, "Incorrect cList length"
    assert top.iterate == 0, "Incorrect iterate"
    assert top.cleanup == 0, "Incorrect cleanup"
