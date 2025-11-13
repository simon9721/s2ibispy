# test_parser_basic.py
import os
import sys
import tempfile
from datetime import datetime
PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, PROJECT_ROOT)
# Import your code
from parser import S2IParser

SAMPLE_S2I = r"""|
| ex1 -   An example of how to create a model for a simple output-only
|         buffer. This example uses the [NoModel] switch to create a
|         "dummy" input pin that has no model in the IBIS file.
| 

|
| Specify the IBIS version and file revision number.
|
[IBIS Ver]        3.2
[File rev]        0

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
[Spice type]        hspice
|[Spice type]        spectre
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
|[Tf]            21.0m  11.0m  41.0m
[vih] 3.3 3 3.6
[rload] 500

| 
| Specify the default pin parasitics
| 
[R_pkg]            2.0m  1.0m  4.0m
[L_pkg]            0.2nH 0.1nH 0.4nH
[C_pkg]            2pF   1pF   4pF

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
[Pin]
out out out driver 
-> in 
in in in dummy
gnd gnd gnd GND
vdd vdd vdd POWER

| Now we give the particulars of the model "driver".
[Model] driver
[Model type] output
[Polarity] Non-inverting
[Model file] hspice.mod hspice.mod hspice.mod
[Rising waveform] 500 0 NA NA NA NA NA NA NA
[Rising waveform] 1500 0 NA NA NA NA NA NA NA
[Falling waveform] 500 3.3 NA NA NA NA NA NA NA
[Falling waveform] 3500 3.3 NA NA NA NA NA NA NA

| The dummy input uses [NoModel]
[Model]     dummy
[nomodel]
"""

def main():
    # Write the sample to a temp file
    with tempfile.TemporaryDirectory() as td:
        s2i_path = os.path.join(td, "example.s2i")
        with open(s2i_path, "w", newline="\n") as f:
            f.write(SAMPLE_S2I)

        # Parse
        parser = S2IParser()
        ibis, global_, mlist = parser.parse(s2i_path)

        # --- Assertions (raise AssertionError if anything regresses) ---
        assert ibis.ibisVersion == "3.2"
        assert len(ibis.cList) == 1
        comp = ibis.cList[0]
        assert comp.component == "MCM Driver 1"
        assert comp.spiceFile == "buffer.sp"

        # Pins
        assert len(comp.pList) == 4
        pins = {p.pinName: p for p in comp.pList}
        assert pins["out"].modelName.lower() == "driver"
        assert pins["out"].inputPin == "in"
        assert pins["in"].modelName.lower() == "dummy"
        assert pins["gnd"].modelName == "GND"
        assert pins["vdd"].modelName == "POWER"

        # Globals parsed with SI+unit
        # [L_pkg] 0.2nH -> 2.0e-10 H
        L_typ = global_.pinParasitics.L_pkg.typ
        C_typ = global_.pinParasitics.C_pkg.typ
        R_typ = global_.pinParasitics.R_pkg.typ
        assert abs(L_typ - 2.0e-10) < 1e-20, f"L_pkg.typ={L_typ}"
        assert abs(C_typ - 2.0e-12) < 1e-24, f"C_pkg.typ={C_typ}"
        assert abs(R_typ - 2.0e-3) < 1e-12, f"R_pkg.typ={R_typ}"

        # Voltage range and sim params
        assert global_.voltageRange.typ == 3.3
        assert global_.voltageRange.min == 3.0
        assert global_.voltageRange.max == 3.6
        assert global_.Rload == 500.0
        # [sim time] 3ns -> 3e-9
        assert abs(global_.simTime - 3e-9) < 1e-18

        # Models
        names = sorted(m.modelName for m in mlist)
        assert names == ["driver", "dummy"]
        driver = next(m for m in mlist if m.modelName == "driver")
        # Two rising + two falling waveforms parsed
        assert len(driver.risingWaveList) == 2
        assert len(driver.fallingWaveList) == 2

        # --- NEW: verify pin relationships from the "-> in" continuation ---
        assert ibis.cList, "No components parsed"
        comp = ibis.cList[0]
        assert comp.pList, "No pins parsed in component"

        pins_by_name = {p.pinName: p for p in comp.pList}

        # Check that 'out' pin is present and has inputPin='in' and no enablePin
        assert "out" in pins_by_name, "Expected pin 'out' not found"
        out_pin = pins_by_name["out"]
        assert out_pin.inputPin == "in", f"Expected out.inputPin == 'in', got {out_pin.inputPin!r}"
        assert (out_pin.enablePin == "" or out_pin.enablePin is None), (
            f"Expected out.enablePin to be empty, got {out_pin.enablePin!r}"
        )

        # Sanity check that the 'in' pin itself has no input/enable mappings
        assert "in" in pins_by_name, "Expected pin 'in' not found"
        in_pin = pins_by_name["in"]
        assert (in_pin.inputPin == "" or in_pin.inputPin is None), (
            f"Expected in.inputPin to be empty, got {in_pin.inputPin!r}"
        )
        assert (in_pin.enablePin == "" or in_pin.enablePin is None), (
            f"Expected in.enablePin to be empty, got {in_pin.enablePin!r}"
        )

        # --- Summary printout ---
        print("=== Parse OK ===")
        print(f"IBIS Ver     : {ibis.ibisVersion}")
        print(f"Output file  : {ibis.thisFileName}")
        print(f"Date         : {ibis.date}")
        print(f"Components   : {len(ibis.cList)} -> {[c.component for c in ibis.cList]}")
        print(f"Pins         : {[ (p.pinName, p.modelName) for p in comp.pList ]}")
        print(f"Models       : {names}")
        print(f"L_pkg.typ    : {L_typ:.3e} H")
        print(f"C_pkg.typ    : {C_typ:.3e} F")
        print(f"R_pkg.typ    : {R_typ:.3e} Ohm")
        print(f"Vrange (typ/min/max): {global_.voltageRange.typ}, {global_.voltageRange.min}, {global_.voltageRange.max}")
        print(f"Rload        : {global_.Rload}")
        print(f"Sim time     : {global_.simTime:.3e} s")

        print("Pin relationships:")
        for p in comp.pList:
            print(f"  {p.pinName:>4}  input={p.inputPin!r}  enable={p.enablePin!r}")

if __name__ == "__main__":
    main()
