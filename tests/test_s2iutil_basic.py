import math
import os
import sys
PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, PROJECT_ROOT)
from models import (
    IbisTOP, IbisGlobal, IbisComponent, IbisPin, IbisModel,
    IbisTypMinMax, IbisWaveTable, SeriesModel
)
from s2i_constants import ConstantStuff as CS
from s2iutil import S2IUtil

def assert_nan(x):
    assert isinstance(x, float) and math.isnan(x)

def main():
    # --- Build globals ---
    g = IbisGlobal(
        tempRange=IbisTypMinMax(27, 100, 0),
        voltageRange=IbisTypMinMax(3.3, 3.0, 3.6),
        pullupRef=IbisTypMinMax(3.3, 3.0, 3.6),
        pulldownRef=IbisTypMinMax(0.0, 0.0, 0.0),
        powerClampRef=IbisTypMinMax(3.3, 3.0, 3.6),
        gndClampRef=IbisTypMinMax(0.0, 0.0, 0.0),
        vil=IbisTypMinMax(0.0, 0.0, 0.0),
        vih=IbisTypMinMax(2.0, 1.8, 2.2),
        tr=IbisTypMinMax(1e-9, 1e-9, 1e-9),
        tf=IbisTypMinMax(1e-9, 1e-9, 1e-9),
        c_comp=IbisTypMinMax(5e-12, 5e-12, 5e-12),
        Rload=500.0,
        simTime=3e-9,
        derateVIPct=15.0,
        derateRampPct=10.0,
    )

    # --- Build models list ---
    # m1: mostly empty → should get globals copied
    m1 = IbisModel(modelName="DRV", modelType=CS.ModelType.OUTPUT)
    # m2: pre-filled values must NOT be overwritten
    m2 = IbisModel(
        modelName="custom",
        modelType=CS.ModelType.OUTPUT,
        voltageRange=IbisTypMinMax(1.8, 1.62, 1.98),
        vil=IbisTypMinMax(0.3, 0.25, 0.35),
        vih=IbisTypMinMax(1.2, 1.1, 1.3),
        Rload=123.0,
        simTime=7e-9,
        c_comp=IbisTypMinMax(1e-12, 1e-12, 1e-12),
        derateVIPct=5.0,
    )
    # Give m2 a waveform so Rload should NOT be overwritten
    m2.risingWaveList.append(IbisWaveTable(R_fixture=50, V_fixture=0))

    # m3: series model present → should inherit seriesSpiceFile to ext_spice_cmd_file
    m3 = IbisModel(modelName="SER", modelType=CS.ModelType.SERIES, seriesModel=SeriesModel())

    mlist = [m1, m2, m3]

    # --- Build component+pins ---
    comp = IbisComponent(
        component="U1",
        manufacturer="ACME",
        spiceFile="comp_top.sp",
        seriesSpiceFile="series_top.inc",
    )
    comp.pList = [
        IbisPin(pinName="OUT", signalName="OUT", modelName="drv"),      # case-insensitive
        IbisPin(pinName="IN", signalName="IN", modelName="dummy"),      # no model in list
        IbisPin(pinName="GND", signalName="GND", modelName="GND"),      # special → skip link
        IbisPin(pinName="VDD", signalName="VDD", modelName="POWER"),    # special → skip link
        IbisPin(pinName="SER1", signalName="SER1", modelName="SER"),
        IbisPin(pinName="OUT2", signalName="OUT2", modelName="custom"),
    ]
    top = IbisTOP(ibisVersion="3.2", thisFileName="x.ibs", cList=[comp])

    # --- Run util ---
    util = S2IUtil(mlist)
    util.complete_data_structures(top, g)

    # --- Assertions ---

    # m1 should be filled from globals
    assert m1.voltageRange.typ == 3.3
    assert m1.vil.typ == 0.0
    assert m1.vih.typ == 2.0
    assert m1.tr.typ == 1e-9 and m1.tf.typ == 1e-9
    assert m1.Rload == 500.0           # no waveforms → copied
    assert m1.simTime == 3e-9          # copied
    assert m1.c_comp.typ == 5e-12
    assert m1.derateVIPct == 15.0
    assert m1.ramp is not None and m1.ramp.derateRampPct == 10.0
    # From component defaults
    assert m1.spice_file == "comp_top.sp"

    # m2 should preserve its own values
    assert m2.voltageRange.typ == 1.8
    assert m2.vil.typ == 0.3 and m2.vih.typ == 1.2
    assert m2.Rload == 123.0           # model-defined, and has waveforms → do NOT copy global
    assert m2.simTime == 7e-9
    assert m2.c_comp.typ == 1e-12
    assert m2.derateVIPct == 5.0
    # spice_file should copy since model had none
    assert m2.spice_file == "comp_top.sp"

    # m3 series: should obtain seriesSpiceFile in ext_spice_cmd_file
    assert m3.spice_file == "comp_top.sp"
    assert m3.seriesModel is not None
    assert m3.ext_spice_cmd_file == "series_top.inc"

    # Pin→model links
    pin_out = comp.pList[0]
    assert pin_out.model is m1                       # "drv"→"DRV"
    pin_in = comp.pList[1]
    assert pin_in.model is None                      # "dummy" not in model list
    pin_gnd = comp.pList[2]
    assert pin_gnd.model is None                     # special
    pin_vdd = comp.pList[3]
    assert pin_vdd.model is None                     # special
    pin_ser = comp.pList[4]
    assert pin_ser.model is m3

    # Helper lookups
    assert util.get_matching_pin("out", comp.pList) is pin_out
    assert util.get_matching_pin("nope", comp.pList) is None
    assert util.get_matching_model("DRV", mlist) is m1
    assert util.get_matching_model("GND", mlist) is None  # special is skipped

    print("=== S2IUtil tests passed ===")

if __name__ == "__main__":
    main()
