# tests/fakes.py
from typing import List, Optional
from models import IbisTypMinMax, IbisVItable, IbisVItableEntry, IbisWaveTable, IbisWaveTableEntry

class FakeSpiceTransient:
    def __init__(self, mlist):
        self.mlist = mlist
        self.calls = {
            "generate_ramp_data": [],
            "generate_wave_data": [],
        }
        # Keep symmetry with AnalyzePin expectations (we don’t use last_vi_table here)
        self.last_vi_table: Optional[IbisVItable] = None

    # ---- Doubles that mimic S2ISpice API ----
    def generate_ramp_data(self, current_pin, enable_pin, input_pin,
                           pullup_pin, pulldown_pin, power_clamp_pin, gnd_clamp_pin,
                           vcc, gnd, vcc_clamp, gnd_clamp, curve_type, spice_command,
                           iterate, cleanup):
        self.calls["generate_ramp_data"].append({
            "pin": current_pin.pinName,
            "curve_type": curve_type
        })
        # Populate a simple, deterministic ramp back into the model
        m = current_pin.model
        if m.ramp is None:
            # this shouldn’t happen in your code, but be safe
            from models import IbisRamp
            m.ramp = IbisRamp()
        if curve_type == 5:  # CS.CurveType.RISING_RAMP
            m.ramp.dv_r.typ = 1.0
            m.ramp.dt_r.typ = 1e-9
        elif curve_type == 6:  # CS.CurveType.FALLING_RAMP
            m.ramp.dv_f.typ = 1.0
            m.ramp.dt_f.typ = 1e-9
        return 0  # success

    def generate_wave_data(self, current_pin, enable_pin, input_pin,
                           pullup_pin, pulldown_pin, power_clamp_pin, gnd_clamp_pin,
                           vcc, gnd, vcc_clamp, gnd_clamp, curve_type, spice_command,
                           iterate, cleanup, idx):
        self.calls["generate_wave_data"].append({
            "pin": current_pin.pinName,
            "curve_type": curve_type,
            "idx": idx
        })
        # Synthesize a small monotonic waveform into the model’s list slot
        tbl_list = (current_pin.model.risingWaveList
                    if curve_type == 7  # CS.CurveType.RISING_WAVE
                    else current_pin.model.fallingWaveList)
        # Ensure the slot exists
        if idx >= len(tbl_list):
            return 2  # failure if mis-indexed
        tbl: IbisWaveTable = tbl_list[idx]
        tbl.waveData = []
        # 5 points, 0.0..0.4ns; voltages 0..Vcc for rising, Vcc..0 for falling
        for k in range(5):
            t = k * 0.1e-9
            if curve_type == 7:
                v = (k / 4.0) * vcc.typ
            else:
                v = (1.0 - k / 4.0) * vcc.typ
            tbl.waveData.append(IbisWaveTableEntry(t=t, v=IbisTypMinMax(typ=v)))
        tbl.size = len(tbl.waveData)
        return 0
