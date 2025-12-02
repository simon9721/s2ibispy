# s2i_to_yaml.py — The Bridge of Mercy
# Converts any old .s2i file → perfect modern .yaml
# One command: python s2i_to_yaml.py buffer.s2i → buffer.yaml

import argparse
import math
import yaml
from pathlib import Path
from s2ibispy.legacy.parser import S2IParser

def convert_s2i_to_yaml(s2i_path: Path, yaml_path: Path):
    """Convert .s2i file to YAML format."""
    parser = S2IParser()
    ibis, global_, mList = parser.parse(str(s2i_path))
    
    # Helper to convert IbisTypMinMax to dict
    def tmm_to_dict(tmm):
        import math
        if tmm is None:
            return None
        return {
            "typ": tmm.typ if hasattr(tmm, 'typ') else 0,
            "min": tmm.min if hasattr(tmm, 'min') else 0,
            "max": tmm.max if hasattr(tmm, 'max') else 0,
        }
    
    # Helper to check if a TMM has actual values (not all NaN)
    def tmm_has_values(tmm):
        import math
        if tmm is None:
            return False
        return not (math.isnan(tmm.typ) and math.isnan(tmm.min) and math.isnan(tmm.max))
    
    # Build YAML structure
    yaml_data = {
        "spice_subckt": getattr(global_, 'spice_subckt', None) or None,
        "ibis_version": ibis.ibisVersion,
        "file_name": ibis.thisFileName,
        "file_rev": ibis.fileRev,
        "date": ibis.date,
        "source": ibis.source,
        "notes": ibis.notes,
        "disclaimer": ibis.disclaimer,
        "copyright": ibis.copyright,
        "spice_type": "hspice" if ibis.spiceType == 0 else "pspice",
        "iterate": str(ibis.iterate),
        "cleanup": str(ibis.cleanup),
        "global_defaults": {
            "sim_time": global_.simTime,
            "r_load": str(global_.Rload),
            "temp_range": tmm_to_dict(global_.tempRange),
            "voltage_range": tmm_to_dict(global_.voltageRange),
            "vil": tmm_to_dict(global_.vil),
            "vih": tmm_to_dict(global_.vih),
        }
    }
    
    # Add optional reference voltages only if they exist and have actual values (not all NaN)
    if hasattr(global_, 'pullupRef') and tmm_has_values(global_.pullupRef):
        yaml_data["global_defaults"]["pullup_ref"] = tmm_to_dict(global_.pullupRef)
    if hasattr(global_, 'pulldownRef') and tmm_has_values(global_.pulldownRef):
        yaml_data["global_defaults"]["pulldown_ref"] = tmm_to_dict(global_.pulldownRef)
    if hasattr(global_, 'powerClampRef') and tmm_has_values(global_.powerClampRef):
        yaml_data["global_defaults"]["power_clamp_ref"] = tmm_to_dict(global_.powerClampRef)
    if hasattr(global_, 'gndClampRef') and tmm_has_values(global_.gndClampRef):
        yaml_data["global_defaults"]["gnd_clamp_ref"] = tmm_to_dict(global_.gndClampRef)
    
    # Add pin parasitics
    if hasattr(global_, 'pinParasitics') and global_.pinParasitics:
        pp = global_.pinParasitics
        yaml_data["global_defaults"]["pin_parasitics"] = {
            "R_pkg": tmm_to_dict(pp.R_pkg),
            "L_pkg": tmm_to_dict(pp.L_pkg),
            "C_pkg": tmm_to_dict(pp.C_pkg),
        }
    
    # Convert models
    # Map ModelType enum to YAML schema format
    model_type_map = {
        "INPUT": "Input",
        "OUTPUT": "Output",
        "I_O": "I/O",
        "IO": "I/O",
        "THREE_STATE": "3-state",
        "OPEN_DRAIN": "Open_drain",
        "OPEN_SINK": "Open_sink",
        "OPEN_SOURCE": "Open_source",
        "IO_OPEN_DRAIN": "I/O_Open_drain",
        "IO_OPEN_SINK": "I/O_Open_sink",
        "IO_OPEN_SOURCE": "I/O_Open_source",
        "SERIES": "Series",
        "SERIES_SWITCH": "Series_switch",
        "TERMINATOR": "Terminator",
        "INPUT_ECL": "Input_ECL",
        "OUTPUT_ECL": "Output_ECL",
        "IO_ECL": "I/O_ECL",
    }
    
    models = []
    for model in mList:
        # Get model type name
        type_name = model.modelType.name if hasattr(model.modelType, 'name') else str(model.modelType)
        # Map to YAML schema format
        yaml_type = model_type_map.get(type_name, "I/O")  # Default to I/O if unknown
        
        m = {
            "name": model.modelName,
            "type": yaml_type,
        }
        if model.enable:
            m["enable"] = model.enable
        if hasattr(model, 'polarity') and model.polarity:
            m["polarity"] = "Inverting" if model.polarity == 1 else "Non-Inverting"
        
        # Add model files if they exist
        if hasattr(model, 'modelFile') and model.modelFile:
            m["modelFile"] = model.modelFile
        if hasattr(model, 'modelFileMin') and model.modelFileMin:
            m["modelFileMin"] = model.modelFileMin
        if hasattr(model, 'modelFileMax') and model.modelFileMax:
            m["modelFileMax"] = model.modelFileMax
        
        # Add noModel flag if set
        if hasattr(model, 'noModel') and model.noModel:
            m["nomodel"] = True
        
        # Add waveforms if they exist
        if hasattr(model, 'risingWaveList') and model.risingWaveList:
            rising_waveforms = []
            for wave in model.risingWaveList:
                if hasattr(wave, 'R_fixture'):
                    wf = {
                        "R_fixture": wave.R_fixture,
                        "V_fixture": wave.V_fixture,
                    }
                    # Add optional parameters if they're not NA/NaN
                    if hasattr(wave, 'V_fixture_min') and not math.isnan(wave.V_fixture_min):
                        wf["V_fixture_min"] = wave.V_fixture_min
                    if hasattr(wave, 'V_fixture_max') and not math.isnan(wave.V_fixture_max):
                        wf["V_fixture_max"] = wave.V_fixture_max
                    if hasattr(wave, 'L_fixture') and not math.isnan(wave.L_fixture):
                        wf["L_fixture"] = wave.L_fixture
                    if hasattr(wave, 'C_fixture') and not math.isnan(wave.C_fixture):
                        wf["C_fixture"] = wave.C_fixture
                    if hasattr(wave, 'R_dut') and not math.isnan(wave.R_dut):
                        wf["R_dut"] = wave.R_dut
                    if hasattr(wave, 'L_dut') and not math.isnan(wave.L_dut):
                        wf["L_dut"] = wave.L_dut
                    if hasattr(wave, 'C_dut') and not math.isnan(wave.C_dut):
                        wf["C_dut"] = wave.C_dut
                    rising_waveforms.append(wf)
            if rising_waveforms:
                m["rising_waveforms"] = rising_waveforms
        
        if hasattr(model, 'fallingWaveList') and model.fallingWaveList:
            falling_waveforms = []
            for wave in model.fallingWaveList:
                if hasattr(wave, 'R_fixture'):
                    wf = {
                        "R_fixture": wave.R_fixture,
                        "V_fixture": wave.V_fixture,
                    }
                    # Add optional parameters if they're not NA/NaN
                    if hasattr(wave, 'V_fixture_min') and not math.isnan(wave.V_fixture_min):
                        wf["V_fixture_min"] = wave.V_fixture_min
                    if hasattr(wave, 'V_fixture_max') and not math.isnan(wave.V_fixture_max):
                        wf["V_fixture_max"] = wave.V_fixture_max
                    if hasattr(wave, 'L_fixture') and not math.isnan(wave.L_fixture):
                        wf["L_fixture"] = wave.L_fixture
                    if hasattr(wave, 'C_fixture') and not math.isnan(wave.C_fixture):
                        wf["C_fixture"] = wave.C_fixture
                    if hasattr(wave, 'R_dut') and not math.isnan(wave.R_dut):
                        wf["R_dut"] = wave.R_dut
                    if hasattr(wave, 'L_dut') and not math.isnan(wave.L_dut):
                        wf["L_dut"] = wave.L_dut
                    if hasattr(wave, 'C_dut') and not math.isnan(wave.C_dut):
                        wf["C_dut"] = wave.C_dut
                    falling_waveforms.append(wf)
            if falling_waveforms:
                m["falling_waveforms"] = falling_waveforms
        
        models.append(m)
    yaml_data["models"] = models
    
    # Convert components
    components = []
    for comp in ibis.cList:
        pins = []
        for pin in comp.pList:
            p = {
                "pinName": pin.pinName,
                "signalName": pin.signalName,
                "modelName": pin.modelName,
            }
            # Preserve SPICE node mapping from [Pin] (second column)
            if hasattr(pin, 'spiceNodeName') and pin.spiceNodeName:
                p["spiceNodeName"] = pin.spiceNodeName
            if hasattr(pin, 'inputPin') and pin.inputPin:
                p["inputPin"] = pin.inputPin
            if hasattr(pin, 'enablePin') and pin.enablePin:
                p["enablePin"] = pin.enablePin
            pins.append(p)
        
        components.append({
            "component": comp.component,
            "manufacturer": comp.manufacturer,
            "spiceFile": getattr(comp, 'spiceFile', ''),
            "pList": pins
        })
    yaml_data["components"] = components
    
    # Write YAML file
    with open(yaml_path, 'w', encoding='utf-8') as f:
        yaml.dump(yaml_data, f, sort_keys=False, default_flow_style=False, 
                 indent=2, allow_unicode=True)
    
    print(f"Converted {s2i_path} → {yaml_path}")
    print("You are now free from the past.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert legacy .s2i → modern .yaml")
    parser.add_argument("s2i_file", help=".s2i input file")
    parser.add_argument("--output", "-o", help="Output .yaml file")
    args = parser.parse_args()
    
    s2i_path = Path(args.s2i_file)
    yaml_path = Path(args.output or s2i_path.with_suffix(".yaml"))
    convert_s2i_to_yaml(s2i_path, yaml_path)
