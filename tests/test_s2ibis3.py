import logging
from typing import List
from legacy.parser import S2IParser
from s2iutil import S2IUtil
from models import IbisTOP, IbisGlobal, IbisComponent, IbisPin, IbisModel, IbisDiffPin, IbisSeriesPin, IbisSeriesSwitchGroup, IbisWaveTable, IbisTypMinMax, SeriesModel
from s2i_constants import ConstantStuff as CS

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def print_tmm(tmm: IbisTypMinMax, indent: int = 0) -> str:
    """Helper to format IbisTypMinMax values."""
    return f"{' ' * indent}typ={tmm.typ}, min={tmm.min}, max={tmm.max}"

def print_data_structures(ibis: IbisTOP, global_: IbisGlobal, models: List[IbisModel]) -> None:
    """Print the parsed and completed IBIS data structures."""
    print("\n=== IbisTOP ===")
    print(f"IBIS Version: {ibis.ibisVersion}")
    print(f"File Name: {ibis.thisFileName}")
    print(f"File Rev: {ibis.fileRev}")
    print(f"Date: {ibis.date}")
    print(f"Source: {ibis.source}")
    print(f"Notes: {ibis.notes}")
    print(f"Disclaimer: {ibis.disclaimer}")
    print(f"Copyright: {ibis.copyright}")
    print(f"Spice Type: {CS.SpiceType(ibis.spiceType).name}")
    print(f"Spice Command: {ibis.spiceCommand}")
    print(f"Iterate: {ibis.iterate}")
    print(f"Cleanup: {ibis.cleanup}")

    print("\n=== IbisGlobal ===")
    print(f"Comment Char: {global_.commentChar}")
    print(f"Temperature Range: {print_tmm(global_.tempRange)}")
    print(f"Voltage Range: {print_tmm(global_.voltageRange)}")
    print(f"Pullup Reference: {print_tmm(global_.pullupRef)}")
    print(f"Pulldown Reference: {print_tmm(global_.pulldownRef)}")
    print(f"Power Clamp Reference: {print_tmm(global_.powerClampRef)}")
    print(f"GND Clamp Reference: {print_tmm(global_.gndClampRef)}")
    print(f"C_comp: {print_tmm(global_.c_comp)}")
    print(f"Vil: {print_tmm(global_.vil)}")
    print(f"Vih: {print_tmm(global_.vih)}")
    print(f"Tr: {print_tmm(global_.tr)}")
    print(f"Tf: {print_tmm(global_.tf)}")
    print(f"Rload: {global_.Rload}")
    print(f"Sim Time: {global_.simTime}")
    print(f"Derate VI Pct: {global_.derateVIPct}")
    print(f"Derate Ramp Pct: {global_.derateRampPct}")
    print(f"Clamp Tolerance: {global_.clampTol}")
    print(f"Pin Parasitics:")
    print(f"  R_pkg: {print_tmm(global_.pinParasitics.R_pkg, 2)}")
    print(f"  L_pkg: {print_tmm(global_.pinParasitics.L_pkg, 2)}")
    print(f"  C_pkg: {print_tmm(global_.pinParasitics.C_pkg, 2)}")

    print("\n=== Components ===")
    for comp in ibis.cList:
        print(f"\nComponent: {comp.component}")
        print(f"  Manufacturer: {comp.manufacturer}")
        print(f"  Spice File: {comp.spiceFile}")
        print(f"  Series Spice File: {comp.seriesSpiceFile}")
        print(f"  Has Pin Mapping: {comp.hasPinMapping}")
        print(f"  Temperature Range: {print_tmm(comp.tempRange, 2)}")
        print(f"  Voltage Range: {print_tmm(comp.voltageRange, 2)}")
        print(f"  Pullup Reference: {print_tmm(comp.pullupRef, 2)}")
        print(f"  Pulldown Reference: {print_tmm(comp.pulldownRef, 2)}")
        print(f"  Power Clamp Reference: {print_tmm(comp.powerClampRef, 2)}")
        print(f"  GND Clamp Reference: {print_tmm(comp.gndClampRef, 2)}")
        print(f"  C_comp: {print_tmm(comp.c_comp, 2)}")
        print(f"  Vil: {print_tmm(comp.vil, 2)}")
        print(f"  Vih: {print_tmm(comp.vih, 2)}")
        print(f"  Tr: {print_tmm(comp.tr, 2)}")
        print(f"  Tf: {print_tmm(comp.tf, 2)}")
        print(f"  Rload: {comp.Rload}")
        print(f"  Sim Time: {comp.simTime}")
        print(f"  Derate VI Pct: {comp.derateVIPct}")
        print(f"  Derate Ramp Pct: {comp.derateRampPct}")
        print(f"  Clamp Tolerance: {comp.clampTol}")
        print(f"  Pin Parasitics:")
        print(f"    R_pkg: {print_tmm(comp.pinParasitics.R_pkg, 4)}")
        print(f"    L_pkg: {print_tmm(comp.pinParasitics.L_pkg, 4)}")
        print(f"    C_pkg: {print_tmm(comp.pinParasitics.C_pkg, 4)}")

        print(f"  Pins:")
        for pin in comp.pList:
            print(f"    Pin: {pin.pinName}")
            print(f"      Signal Name: {pin.signalName}")
            print(f"      Model Name: {pin.modelName}")
            print(f"      Spice Node: {pin.spiceNodeName}")
            print(f"      Input Pin: {pin.inputPin}")
            print(f"      Enable Pin: {pin.enablePin}")
            print(f"      Series Pin2: {pin.seriesPin2name}")
            print(f"      Pullup Ref: {pin.pullupRef}")
            print(f"      Pulldown Ref: {pin.pulldownRef}")
            print(f"      Power Clamp Ref: {pin.powerClampRef}")
            print(f"      GND Clamp Ref: {pin.gndClampRef}")
            print(f"      R_pin: {pin.R_pin}")
            print(f"      L_pin: {pin.L_pin}")
            print(f"      C_pin: {pin.C_pin}")
            print(f"      Model: {'Set' if pin.model else 'None'}")

        print(f"  Differential Pins:")
        for dp in comp.dpList:
            print(f"    Diff Pin: {dp.pinName}")
            print(f"      Inv Pin: {dp.invPin}")
            print(f"      Vdiff: {print_tmm(dp.vdiff, 6)}")
            print(f"      Tdelay: {print_tmm(dp.tdelay, 6)}")

        print(f"  Series Pins:")
        for sp in comp.spList:
            print(f"    Series Pin: {sp.pin1}")
            print(f"      Pin2: {sp.pin2}")
            print(f"      Model Name: {sp.modelName}")
            print(f"      Function Table Group: {sp.fnTableGp}")

        print(f"  Series Switch Groups:")
        for ssg in comp.ssgList:
            print(f"    Group: {ssg.pins}")

    print("\n=== Models ===")
    for model in models:
        print(f"\nModel: {model.modelName}")
        print(f"  Model Type: {CS.ModelType(model.modelType).name if isinstance(model.modelType, CS.ModelType) else model.modelType}")
        print(f"  Polarity: {model.polarity}")
        print(f"  Enable: {model.enable}")
        print(f"  Vinl: {model.Vinl}")
        print(f"  Vinh: {model.Vinh}")
        print(f"  Vmeas: {model.Vmeas}")
        print(f"  Cref: {model.Cref}")
        print(f"  Rref: {model.Rref}")
        print(f"  Vref: {model.Vref}")
        print(f"  Rload: {model.Rload}")
        print(f"  Sim Time: {model.simTime}")
        print(f"  Derate VI Pct: {model.derateVIPct}")
        print(f"  Derate Ramp Pct: {model.derateRampPct}")
        print(f"  Clamp Tolerance: {model.clampTol}")
        print(f"  Temperature Range: {print_tmm(model.tempRange, 2)}")
        print(f"  Voltage Range: {print_tmm(model.voltageRange, 2)}")
        print(f"  Pullup Reference: {print_tmm(model.pullupRef, 2)}")
        print(f"  Pulldown Reference: {print_tmm(model.pulldownRef, 2)}")
        print(f"  Power Clamp Reference: {print_tmm(model.powerClampRef, 2)}")
        print(f"  GND Clamp Reference: {print_tmm(model.gndClampRef, 2)}")
        print(f"  C_comp: {print_tmm(model.c_comp, 2)}")
        print(f"  Vil: {print_tmm(model.vil, 2)}")
        print(f"  Vih: {print_tmm(model.vih, 2)}")
        print(f"  Tr: {print_tmm(model.tr, 2)}")
        print(f"  Tf: {print_tmm(model.tf, 2)}")
        print(f"  Model File: {model.modelFile}")
        print(f"  Model File Min: {model.modelFileMin}")
        print(f"  Model File Max: {model.modelFileMax}")
        print(f"  Ext Spice Cmd File: {model.ext_spice_cmd_file}")
        print(f"  Has Been Analyzed: {model.hasBeenAnalyzed}")
        if model.ramp:
            print(f"  Ramp:")
            print(f"    dv_r: {print_tmm(model.ramp.dv_r, 4)}")
            print(f"    dt_r: {print_tmm(model.ramp.dt_r, 4)}")
            print(f"    dv_f: {print_tmm(model.ramp.dv_f, 4)}")
            print(f"    dt_f: {print_tmm(model.ramp.dt_f, 4)}")
            print(f"    Derate Ramp Pct: {model.ramp.derateRampPct}")
        if model.seriesModel:
            print(f"  Series Model:")
            print(f"    On State: {model.seriesModel.OnState}")
            print(f"    Off State: {model.seriesModel.OffState}")
            print(f"    RSeriesOff: {print_tmm(model.seriesModel.RSeriesOff, 4)}")
            print(f"    Vds List: {model.seriesModel.vdslist}")
        for i, wave in enumerate(model.risingWaveList):
            print(f"  Rising Waveform {i}:")
            print(f"    R_fixture: {wave.R_fixture}")
            print(f"    V_fixture: {wave.V_fixture}")
            print(f"    V_fixture_min: {wave.V_fixture_min}")
            print(f"    V_fixture_max: {wave.V_fixture_max}")
            print(f"    L_fixture: {wave.L_fixture}")
            print(f"    C_fixture: {wave.C_fixture}")
            print(f"    R_dut: {wave.R_dut}")
            print(f"    L_dut: {wave.L_dut}")
            print(f"    C_dut: {wave.C_dut}")
            print(f"    Size: {wave.size}")
        for i, wave in enumerate(model.fallingWaveList):
            print(f"  Falling Waveform {i}:")
            print(f"    R_fixture: {wave.R_fixture}")
            print(f"    V_fixture: {wave.V_fixture}")
            print(f"    V_fixture_min: {wave.V_fixture_min}")
            print(f"    V_fixture_max: {wave.V_fixture_max}")
            print(f"    L_fixture: {wave.L_fixture}")
            print(f"    C_fixture: {wave.C_fixture}")
            print(f"    R_dut: {wave.R_dut}")
            print(f"    L_dut: {wave.L_dut}")
            print(f"    C_dut: {wave.C_dut}")
            print(f"    Size: {wave.size}")

def main():
    # Path to the .s2i file (replace with your actual file path)
    s2i_file = "buffer.s2i"

    # Create sample .s2i file if it doesn't exist
    sample_s2i = """
| 
| ex1 -   An example of how to create a model for a simple output-only
|         buffer. This example uses the [NoModel] switch to create a
|         "dummy" input pin that has no model in the IBIS file.
| 

|
| Specify the IBIS version and file revision number.
|
[IBIS Ver]		3.2
[File rev] 		0

|
| Add some comments to identify the file.
|
[date]  April 1, 2004
|[file name] test.ibs
[source] From MegaFLOPS Inc. layout and silicon models.
[notes] I really wouldn't try to use this driver.  It's really bad.
[disclaimer] This file is only for demonstration purposes. It describes
a really crummy driver.

You can put blank lines in any of these sections. (But s2ibis3 won't
print them.)

Of course, as noted in the documentation, any text in these sections is
truncated at 1KB.

[Copyright] Copyright 2004 MegaFLOPS Inc.
[cleanup]
|
| Give the spice type.  Allowable values are hspice, pspice, spice2,
| spice3 spectre and eldo.
|
[Spice type]		hspice
|[Spice type]		spectre
|
| Now specify some global parameters. These parameters will apply to
| _all_ the models in this file.
|
| Note on the [Temperature range] keyword: Since this is a CMOS circuit,
| the min column contains the highest temperature, since this temperature
| causes or amplifies the "min" (slow, weak) behavior, while the max
| column contains the lowest temperature, since this temperature causes or
| amplifies the "max" (fast, strong) behavior.  If this were a bipolar
| circuit, these temperature values would be reversed.
|
[temperature range] 27 100 0
[voltage range] 3.3 3 3.6
[sim time] 3ns
[vil] 0 0 0
|[Tf]			21.0m	11.0m	41.0m
[vih] 3.3 3 3.6
[rload] 500

| 
| Specify the default pin parasitics
| 
[R_pkg]			2.0m	1.0m	4.0m
[L_pkg]			0.2nH	0.1nH	0.4nH
[C_pkg]			2pF     1pF     4pF

|
| Component Description
|
[Component] MCM Driver 1
[manufacturer] MegaFLOPS Inc.

|
| Specify the SPICE file where the circuit is located.
|
[Spice file]    buffer.sp


|
| Now specify the pin list.  Since we're just creating an IBIS file for
| the driver, we'll use a very short pin list.
|
| The pin list formats can be found in doc/s2ibis2.txt.  Briefly, the
| first line of each pin is of the form
|
|  pin_name  spice_node  signal_name  model_name
|
| If a pin description has more than one line (e.g. the first pin in the
| pin list below), the second line is of the form
|
| -> input_pin  enable_pin
|
| Note that the second line must begin with the symbol "->".
|
| Therefore, a "translation" of the pin list below would read:
|
|   - The first pin is pin number "out". It corresponds to node "out" in
|     the given SPICE file. The signal carried on this pin is named
|     "out". This pin is represented by the model "driver"; it is driven
|     by pin number "in" and has no enable.
|   - The second pin is pin number "in", which corresponds to node "in"
|     in the SPICE file; its signal is named "in". The model for this
|     pin is "dummy".
|   - The third pin is pin number "gnd", which corresponds to node "gnd"
|     in the SPICE file; it carries the "gnd" signal. The model for this
|     pin is "GND", which is an s2ibis2 reserved word that denotes a
|     ground supply pin.
|   - The fourth pin is pin number "vdd", which corresponds to node "vdd"
|     in the SPICE file; it carries the "vdd" signal. The model for this
|     pin is "POWER", which is an s2ibis2 reserved word that denotes a
|     power supply pin.
|
[Pin]
out out out driver 
-> in 
in in in dummy
gnd gnd gnd GND
vdd vdd vdd POWER

|[series pin mapping]
|out in SwitchModelTest 

| Now we give the particulars of the model "driver".  It is of type
| "Output" (allowable types may be found in doc/s2ibis2.txt) and is
| non-inverting. We want to use models from the file "spectre.mod" for
| typ, min and max simulations, and we want to include both a rising and
| falling waveform in our IBIS model. Both the rising and falling
| wveforms have a 500 ohm load; the rising waveform has the load
| grounded, while the falling waveform has the load connected to 3.3V.
| Neither waveform includes any other text fixture or package parasitics.
|
[Model] driver
[Model type] output
[Polarity] Non-inverting
|[Model file] spectre.mod spectre.mod spectre.mod
[Model file] hspice.mod hspice.mod hspice.mod
|[c_comp] 20pf
[Rising waveform] 500 0 NA NA NA NA NA NA NA
[Rising waveform] 1500 0 NA NA NA NA NA NA NA
|[Rising waveform] 2500 0 NA NA NA NA NA NA NA
[Falling waveform] 500 3.3 NA NA NA NA NA NA NA
[Falling waveform] 3500 3.3 NA NA NA NA NA NA NA

|
| Now specify stuff for the model "dummy". Since we only wanted to model
| the driver, we use the [NoModel] switch to tell s2ibis2 not to create
| this model. 
|
[Model] 	dummy
[nomodel]

"""
    try:
        with open(s2i_file, 'w') as f:
            f.write(sample_s2i)
        logging.info(f"Created sample {s2i_file}")
    except Exception as e:
        logging.error(f"Failed to create sample {s2i_file}: {e}")
        return

    # Parse the .s2i file
    parser = S2IParser()
    try:
        ibis, global_, models = parser.parse(s2i_file)
        logging.info("Parsing completed successfully")
    except Exception as e:
        logging.error(f"Parsing failed: {e}")
        return

    # Complete the data structures
    util = S2IUtil(models)
    try:
        util.complete_data_structures(ibis, global_)
        logging.info("Data structure completion successful")
    except Exception as e:
        logging.error(f"Data completion failed: {e}")
        return

    # Print the results
    print_data_structures(ibis, global_, models)

if __name__ == "__main__":
    main()
