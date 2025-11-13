import pytest
import math
from s2iutil import S2IUtil
from models import (
    IbisTOP, IbisGlobal, IbisComponent, IbisPin, IbisModel, IbisTypMinMax,
    IbisPinParasitics, IbisDiffPin
)
from s2i_constants import ConstantStuff as CS

@pytest.fixture
def util_setup():
    """Create a test setup with models, components, and global parameters."""
    model = IbisModel(
        modelName="test_model",
        modelType=str(CS.ModelType.IO),
        vil=IbisTypMinMax(CS.USE_NA),
        vih=IbisTypMinMax(CS.USE_NA),
        Rload=0.0,
        simTime=0.0
    )
    pin1 = IbisPin(pinName="P1", signalName="SIG1", modelName="test_model", model=None)
    pin2 = IbisPin(pinName="P2", signalName="SIG2", modelName="POWER", model=None)
    comp = IbisComponent(
        component="test_comp",
        manufacturer="test_mfg",
        pList=[pin1, pin2],
        dpList=[IbisDiffPin(invPin="P2", vdiff=IbisTypMinMax(0.2), tdelay=IbisTypMinMax(1e-9))],
        spiceFile="test.sp"
    )
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
        derateVIPct=10.0,
        derateRampPct=5.0
    )
    ibis = IbisTOP(
        ibisVersion="3.2",
        thisFileName="test.ibs",
        fileRev="0",
        date="Fri Oct 17 2025",
        source="test",
        notes="",
        disclaimer="",
        copyright="",
        cList=[comp]
    )
    util = S2IUtil(mList=[model])
    return util, ibis, global_, model, comp, pin1

def test_copy_global_data_to_models(util_setup):
    """Test copy_global_data_to_models functionality."""
    util, _, global_, model, _, _ = util_setup
    util.copy_global_data_to_models(global_)
    assert model.tempRange.typ == 25.0, "tempRange not copied"
    assert model.voltageRange.typ == 3.3, "voltageRange not copied"
    assert model.pullupRef.typ == 3.3, "pullupRef not copied"
    assert model.pulldownRef.typ == 0.0, "pulldownRef not copied"
    assert model.powerClampRef.typ == 3.3, "powerClampRef not copied"
    assert model.gndClampRef.typ == 0.0, "gndClampRef not copied"
    assert model.vil.typ == 0.8, "vil not copied"
    assert model.vih.typ == 2.0, "vih not copied"
    assert model.Rload == 50.0, "Rload not copied"
    assert model.simTime == 1e-9, "simTime not copied"
    assert model.ramp.derateRampPct == 5.0, "derateRampPct not copied"
    assert model.derateVIPct == 10.0, "derateVIPct not copied"

def test_copy_global_data_to_models_with_existing_values(util_setup):
    """Test copy_global_data_to_models skips existing values."""
    util, _, global_, model, _, _ = util_setup
    model.vil = IbisTypMinMax(0.7)
    model.Rload = 100.0
    model.derateVIPct = 15.0
    util.copy_global_data_to_models(global_)
    assert model.vil.typ == 0.7, "vil should not be overwritten"
    assert model.Rload == 100.0, "Rload should not be overwritten"
    assert model.derateVIPct == 15.0, "derateVIPct should not be overwritten"

def test_link_pins_to_models(util_setup):
    """Test link_pins_to_models functionality."""
    util, ibis, _, model, comp, pin = util_setup
    util.link_pins_to_models(ibis)
    assert pin.model == model, "Pin not linked to model"
    assert model.spice_file == "test.sp", "spice_file not propagated"

def test_link_pins_to_models_invalid_pin(util_setup):
    """Test link_pins_to_models with invalid modelName."""
    util, ibis, _, _, comp, _ = util_setup
    comp.pList[0].modelName = "invalid_model"
    util.link_pins_to_models(ibis)
    assert comp.pList[0].model is None, "Pin should not link to invalid model"

def test_get_matching_pin(util_setup):
    """Test get_matching_pin functionality."""
    util, _, _, _, comp, pin = util_setup
    found_pin = util.get_matching_pin("P1", comp.pList)
    assert found_pin == pin, "Incorrect pin returned"
    assert util.get_matching_pin("P2", comp.pList) is not None, "P2 should exist"
    assert util.get_matching_pin("invalid", comp.pList) is None, "Non-existent pin should return None"
    assert util.get_matching_pin("", comp.pList) is None, "Empty pin name should return None"

def test_get_matching_model(util_setup):
    """Test get_matching_model functionality."""
    util, _, _, model, _, _ = util_setup
    found_model = util.get_matching_model("test_model", util.mList)
    assert found_model == model, "Incorrect model returned"
    assert util.get_matching_model("GND", util.mList) is None, "GND should return None"
    assert util.get_matching_model("invalid_model", util.mList) is None, "Non-existent model should return None"
    assert util.get_matching_model("", util.mList) is None, "Empty model name should return None"

def test_complete_data_structures(util_setup):
    """Test complete_data_structures functionality."""
    util, ibis, global_, model, comp, pin = util_setup
    util.complete_data_structures(ibis, global_)
    assert model.tempRange.typ == 25.0, "tempRange not copied"
    assert pin.model == model, "Pin not linked to model"
    assert model.spice_file == "test.sp", "spice_file not propagated"

def test_complete_data_structures_diff_pin_validation_error(util_setup):
    """Test complete_data_structures raises error for invalid diff pin."""
    util, ibis, global_, _, comp, _ = util_setup
    comp.dpList[0].invPin = "invalid_pin"
    with pytest.raises(ValueError, match="Validation failed: Differential pin pair invalid_pin not found"):
        util.complete_data_structures(ibis, global_)
