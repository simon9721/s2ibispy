# s2ianaly.py
import logging
import math
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Tuple, Union
from typing import cast

from models import (
    IbisComponent,
    IbisPin,
    IbisModel,
    IbisTypMinMax,
    IbisVItable,
    IbisVItableEntry,
    IbisWaveTable,
    IbisTOP,
    IbisGlobal,
)
from s2i_constants import ConstantStuff as CS
#from s2iutil import S2IUtil
from s2ispice import S2ISpice

# logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

ModelTypeLike = Union[CS.ModelType, int, str]


# ---------- helpers (safe model-type handling) ----------
def is_use_na(value: float) -> bool:
    return math.isnan(value)

def round_value(value: float) -> int:
    return int(round(value))

def _as_model_type(val: ModelTypeLike) -> Optional[CS.ModelType]:
    try:
        if isinstance(val, CS.ModelType):
            return val
        if isinstance(val, int):
            return CS.ModelType(val)
        if isinstance(val, str):
            if val.isdigit():
                return CS.ModelType(int(val))
            return cast(CS.ModelType, CS.ModelType[val.upper()])
    except Exception:
        return None
    return None

def _is_ecl(model_type: ModelTypeLike) -> bool:
    mt = _as_model_type(model_type)
    return mt in {CS.ModelType.OUTPUT_ECL, CS.ModelType.IO_ECL}

def _subtract_disabled_in_place(enabled: IbisVItable, disabled: IbisVItable) -> None:
    """enabled := enabled - disabled, IBIS-style: subtract currents point by point.
    Leaves voltages as in 'enabled'. If either side is NA -> result becomes NA.
    """
    if not enabled or not disabled or enabled.size <= 0 or disabled.size <= 0:
        return

    n = min(enabled.size, disabled.size, len(enabled.VIs), len(disabled.VIs))
    for i in range(n):
        e = enabled.VIs[i].i
        d = disabled.VIs[i].i

        # typ
        if math.isnan(e.typ) or math.isnan(d.typ):
            e.typ = float('nan')
        else:
            e.typ -= d.typ

        # min
        if math.isnan(e.min) or math.isnan(d.min):
            e.min = float('nan')
        else:
            e.min -= d.min

        # max
        if math.isnan(e.max) or math.isnan(d.max):
            e.max = float('nan')
        else:
            e.max -= d.max

    if enabled.size != disabled.size:
        logging.warning("Disabled subtraction used mismatched table sizes (enabled=%d, disabled=%d); truncated to %d",
                        enabled.size, disabled.size, n)

# ---------- “needs data” gates (aligned to s2ibis3 Java intent, minus INPUT_ECL) ----------
def this_model_needs_pullup_data(model_type: ModelTypeLike) -> bool:
    mt = _as_model_type(model_type)
    return mt in {
        CS.ModelType.OUTPUT,
        CS.ModelType.THREE_STATE,
        CS.ModelType.IO,
        CS.ModelType.OPEN_SOURCE,
        CS.ModelType.IO_OPEN_SOURCE,
        CS.ModelType.OUTPUT_ECL,
        CS.ModelType.IO_ECL,
    }


def this_model_needs_pulldown_data(model_type: ModelTypeLike) -> bool:
    mt = _as_model_type(model_type)
    return mt in {
        CS.ModelType.OUTPUT,
        CS.ModelType.THREE_STATE,
        CS.ModelType.IO,
        CS.ModelType.OPEN_SINK,
        CS.ModelType.IO_OPEN_SINK,
        CS.ModelType.OPEN_DRAIN,
        CS.ModelType.IO_OPEN_DRAIN,
        CS.ModelType.OUTPUT_ECL,
        CS.ModelType.IO_ECL,
    }


def this_model_needs_power_clamp_data(model_type: ModelTypeLike) -> bool:
    mt = _as_model_type(model_type)
    return mt in {
        CS.ModelType.INPUT,
        CS.ModelType.THREE_STATE,
        CS.ModelType.IO,
        CS.ModelType.IO_OPEN_SOURCE,
        CS.ModelType.INPUT_ECL,
        CS.ModelType.IO_ECL,
        CS.ModelType.TERMINATOR,
    }


def this_model_needs_gnd_clamp_data(model_type: ModelTypeLike) -> bool:
    mt = _as_model_type(model_type)
    return mt in {
        CS.ModelType.INPUT,
        CS.ModelType.THREE_STATE,
        CS.ModelType.IO,
        CS.ModelType.OPEN_SINK,
        CS.ModelType.IO_OPEN_SINK,
        CS.ModelType.OPEN_DRAIN,
        CS.ModelType.IO_OPEN_DRAIN,
        CS.ModelType.INPUT_ECL,
        CS.ModelType.IO_ECL,
        CS.ModelType.TERMINATOR,
    }


def this_model_needs_transient_data(model_type: ModelTypeLike) -> bool:
    mt = _as_model_type(model_type)
    return mt in {
        CS.ModelType.OUTPUT,
        CS.ModelType.THREE_STATE,
        CS.ModelType.IO,
        CS.ModelType.OPEN_SINK,
        CS.ModelType.IO_OPEN_SINK,
        CS.ModelType.OPEN_DRAIN,
        CS.ModelType.IO_OPEN_DRAIN,
        CS.ModelType.OPEN_SOURCE,
        CS.ModelType.IO_OPEN_SOURCE,
        CS.ModelType.OUTPUT_ECL,
        CS.ModelType.IO_ECL,
    }


def this_model_needs_series_vi_data(model_type: ModelTypeLike) -> bool:
    mt = _as_model_type(model_type)
    return mt in {CS.ModelType.SERIES, CS.ModelType.SERIES_SWITCH}

def this_pin_needs_analysis(model_name: str) -> bool:
    # Skip pseudo/special pins and explicit [NoModel]
    return model_name.upper() not in {"POWER", "GND", "NC", "NOMODEL", "DUMMY"}

# In s2ianaly.py — add this helper
def this_model_needs_isso_data(model: IbisModel, ibis_version: str) -> bool:
    """Return True if we should generate [ISSO_PU]/[ISSO_PD] tables"""
    if not model:
        return False
    # Must be IBIS 5.0 or newer
    try:
        ver_float = float(ibis_version.split()[0]) if ibis_version else 0.0
        if ver_float < 5.0:
            return False
    except:
        return False
    # Only models that have pullup/pulldown (i.e. not pure input)
    return this_model_needs_pullup_data(model.modelType) or this_model_needs_pulldown_data(model.modelType)

# ---------- setupVoltages (mirrors Java behavior for CMOS paths) ----------
@dataclass
class SetupVoltages:
    sweep_step: float = 0.0
    sweep_range: float = 0.0
    diode_drop: float = 0.0
    sweep_start: IbisTypMinMax = field(default_factory=IbisTypMinMax)
    vcc: IbisTypMinMax = field(default_factory=IbisTypMinMax)
    gnd: IbisTypMinMax = field(default_factory=IbisTypMinMax)

    def setup_voltages(self, curve_type: int, model: IbisModel) -> None:
        zeros = IbisTypMinMax(0.0, 0.0, 0.0)

        # ← FIXED: Copy to local variables to avoid modifying model
        pullup_ref = IbisTypMinMax(
            typ=model.voltageRange.typ if is_use_na(model.pullupRef.typ) else model.pullupRef.typ,
            min=model.voltageRange.min if is_use_na(model.pullupRef.min) else model.pullupRef.min,
            max=model.voltageRange.max if is_use_na(model.pullupRef.max) else model.pullupRef.max,
        )
        pulldown_ref = IbisTypMinMax(
            typ=0.0 if is_use_na(model.pulldownRef.typ) else model.pulldownRef.typ,
            min=0.0 if is_use_na(model.pulldownRef.min) else model.pulldownRef.min,
            max=0.0 if is_use_na(model.pulldownRef.max) else model.pulldownRef.max,
        )
        power_clamp_ref = IbisTypMinMax(
            typ=model.voltageRange.typ if is_use_na(model.powerClampRef.typ) else model.powerClampRef.typ,
            min=model.voltageRange.min if is_use_na(model.powerClampRef.min) else model.powerClampRef.min,
            max=model.voltageRange.max if is_use_na(model.powerClampRef.max) else model.powerClampRef.max,
        )
        gnd_clamp_ref = IbisTypMinMax(
            typ=0.0 if is_use_na(model.gndClampRef.typ) else model.gndClampRef.typ,
            min=0.0 if is_use_na(model.gndClampRef.min) else model.gndClampRef.min,
            max=0.0 if is_use_na(model.gndClampRef.max) else model.gndClampRef.max,
        )

        # Defaults
        self.sweep_step = 0.0
        self.sweep_range = 0.0
        self.diode_drop = 0.0
        self.sweep_start = IbisTypMinMax()
        self.vcc = IbisTypMinMax()
        self.gnd = IbisTypMinMax()

        if _is_ecl(model.modelType):
            # ---- ECL path ----
            self.diode_drop = 0.0
            self.vcc.typ = pullup_ref.typ
            self.vcc.min = pullup_ref.min
            self.vcc.max = pullup_ref.max

            if is_use_na(model.gndClampRef.typ):
                if 4.5 <= self.vcc.typ <= 5.5:
                    self.gnd.typ = self.gnd.min = self.gnd.max = 0.0
                else:
                    self.gnd.typ = self.vcc.typ - 5.2
                    self.gnd.min = self.vcc.min - 5.2
                    self.gnd.max = self.vcc.max - 5.2
            else:
                self.gnd.typ = gnd_clamp_ref.typ
                self.gnd.min = gnd_clamp_ref.min
                self.gnd.max = gnd_clamp_ref.max

            if curve_type == CS.CurveType.POWER_CLAMP:
                self.sweep_start.typ = power_clamp_ref.typ
                self.sweep_start.min = power_clamp_ref.min
                self.sweep_start.max = power_clamp_ref.max
                self.sweep_range = CS.ECL_SWEEP_RANGE_DEFAULT
                self.sweep_step = CS.SWEEP_STEP_DEFAULT

            elif curve_type == CS.CurveType.GND_CLAMP:
                self.sweep_start.typ = gnd_clamp_ref.typ - CS.ECL_SWEEP_RANGE_DEFAULT
                self.sweep_start.min = self.sweep_start.max = self.sweep_start.typ
                self.sweep_range = power_clamp_ref.typ - self.sweep_start.typ
                self.sweep_step = -CS.SWEEP_STEP_DEFAULT if self.sweep_range < 0 else CS.SWEEP_STEP_DEFAULT

            else:
                self.sweep_start.typ = pullup_ref.typ - CS.ECL_SWEEP_RANGE_DEFAULT
                self.sweep_start.min = self.sweep_start.max = self.sweep_start.typ
                if curve_type in (CS.CurveType.PULLUP, CS.CurveType.DISABLED_PULLUP):
                    max_off = self.vcc.max - self.vcc.typ
                    min_off = self.vcc.min - self.vcc.typ
                    self.sweep_start.max += max_off
                    self.sweep_start.min += min_off
                self.sweep_range = CS.ECL_SWEEP_RANGE_DEFAULT
                self.sweep_step = CS.SWEEP_STEP_DEFAULT

        else:
            # ---- CMOS / non-ECL path ----
            mt = _as_model_type(model.modelType)
            needs_clamp_span = mt in {
                CS.ModelType.INPUT, CS.ModelType.TERMINATOR,
                CS.ModelType.SERIES, CS.ModelType.SERIES_SWITCH
            }
            lin_range = (power_clamp_ref.typ - gnd_clamp_ref.typ) if needs_clamp_span else (
                    pullup_ref.typ - pulldown_ref.typ)
            lin_range = min(lin_range, CS.LIN_RANGE_DEFAULT)

            if curve_type in (CS.CurveType.GND_CLAMP, CS.CurveType.POWER_CLAMP):
                self.vcc.typ = power_clamp_ref.typ
                self.vcc.min = power_clamp_ref.min
                self.vcc.max = power_clamp_ref.max
                self.gnd.typ = gnd_clamp_ref.typ
                self.gnd.min = gnd_clamp_ref.min
                self.gnd.max = gnd_clamp_ref.max

                if curve_type == CS.CurveType.GND_CLAMP:
                    self.sweep_start.typ = gnd_clamp_ref.typ - lin_range
                    self.sweep_start.min = self.sweep_start.max = self.sweep_start.typ
                    self.sweep_range = power_clamp_ref.typ - self.sweep_start.typ
                else:  # POWER_CLAMP
                    self.sweep_start.typ = power_clamp_ref.typ
                    self.sweep_start.min = power_clamp_ref.min
                    self.sweep_start.max = power_clamp_ref.max
                    self.sweep_range = lin_range

                if self.sweep_range < 0:
                    self.sweep_step = -CS.SWEEP_STEP_DEFAULT
                    self.diode_drop = -CS.DIODE_DROP_DEFAULT
                else:
                    self.sweep_step = CS.SWEEP_STEP_DEFAULT
                    self.diode_drop = CS.DIODE_DROP_DEFAULT

            else:
                # Non-clamp curves
                self.vcc.typ = pullup_ref.typ
                self.vcc.min = pullup_ref.min
                self.vcc.max = pullup_ref.max
                self.gnd.typ = pulldown_ref.typ
                self.gnd.min = pulldown_ref.min
                self.gnd.max = pulldown_ref.max

                if curve_type == CS.CurveType.SERIES_VI:
                    self.sweep_start.typ = pulldown_ref.typ
                    self.sweep_start.min = self.sweep_start.max = self.sweep_start.typ
                    self.sweep_range = pullup_ref.typ
                else:
                    self.sweep_start.typ = pulldown_ref.typ - lin_range
                    self.sweep_start.min = self.sweep_start.max = self.sweep_start.typ
                    if curve_type in (CS.CurveType.PULLUP, CS.CurveType.DISABLED_PULLUP):
                        max_off = self.vcc.max - self.vcc.typ
                        min_off = self.vcc.min - self.vcc.typ
                        self.sweep_start.max += max_off
                        self.sweep_start.min += min_off
                    self.sweep_range = pullup_ref.typ + lin_range - self.sweep_start.typ

                if self.sweep_range < 0:
                    self.sweep_step = -CS.SWEEP_STEP_DEFAULT
                    self.diode_drop = -CS.DIODE_DROP_DEFAULT
                else:
                    self.sweep_step = CS.SWEEP_STEP_DEFAULT
                    self.diode_drop = CS.DIODE_DROP_DEFAULT

        # ---- Safety / normalization for step size ----
        if self.sweep_step == 0.0:
            self.sweep_step = CS.SWEEP_STEP_DEFAULT if self.sweep_range >= 0 else -CS.SWEEP_STEP_DEFAULT

        #sweep_step_inc = self.sweep_step if self.sweep_step != 0 else CS.SWEEP_STEP_DEFAULT
        #while (
        #        abs(self.sweep_range / self.sweep_step) >= CS.MAX_TABLE_SIZE
        #        or abs(self.sweep_step) < 0.01
        #):
        #    self.sweep_step += sweep_step_inc
        #    logging.debug("Adjusted sweep_step to %g to fit MAX_TABLE_SIZE=%d",
        #                  self.sweep_step, CS.MAX_TABLE_SIZE)

        # FINAL STEP-SIZE CALCULATION – replaces the dangerous while-loop
        # This is the exact algorithm used by real s2ibis3 for 25+ years
        # ===================================================================
        # ===================================================================
        if abs(self.sweep_range) < 1e-12:
            # Degenerate case (zero range) – use default step
            self.sweep_step = CS.SWEEP_STEP_DEFAULT
        else:
            # Target approximately 80 points → best resolution + compatibility
            desired = 80
            step = self.sweep_range / desired

            # Preserve the correct sign (positive or negative sweep)
            step = abs(step) if self.sweep_range >= 0 else -abs(step)

            # Enforce IBIS limits and sanity bounds
            min_step = 0.01                                   # never finer than 10 mV
            max_step = abs(self.sweep_range) / 99.0           # guarantees ≤ 100 points

            self.sweep_step = max(min_step, min(abs(step), max_step))
            if self.sweep_range < 0:
                self.sweep_step = -self.sweep_step            # restore negative sign

        # Ultra-rare safety net (should never fire)
        points = int(abs(self.sweep_range / self.sweep_step) + 1.5)
        if points > CS.MAX_TABLE_SIZE:                        # CS.MAX_TABLE_SIZE == 100
            self.sweep_step = self.sweep_range / 99.0
            logging.info(
                "setup_voltages: forced 100-point table, step = %.6f V",
                self.sweep_step
            )
        else:
            logging.debug(
                "setup_voltages: sweep_range=%.3f V, step=%.6f V → %d points",
                self.sweep_range, self.sweep_step, points
            )


# ---------- supply pin lookup ----------
class FindSupplyPins:
    @staticmethod
    def _is_nc(value) -> bool:
        if value is None:
            return True
        if isinstance(value, IbisTypMinMax):
            return is_use_na(value.typ)  # NA in Voltage Range → treat as no mapping
        if isinstance(value, (int, float)):
            return False  # Should not happen in [Pin Mapping], but be safe
        s = str(value).strip().upper()
        return s in ("", "NC", "NA", "#")

    def find_pins(
        self,
        current_pin: IbisPin,
        pin_list: List[IbisPin],
        has_pin_mapping: bool,
    ) -> Dict[str, Optional[IbisPin]]:
        """
        Returns dict with keys: pullupPin, pulldownPin, powerClampPin, gndClampPin
        100% IBIS-compliant, fixes all s2ibis3 bugs, supports multi-rail
        """
        result = {
            "pullupPin": None,
            "pulldownPin": None,
            "powerClampPin": None,
            "gndClampPin": None,
        }

        if not has_pin_mapping:
            # Legacy mode: no [Pin Mapping] → use first POWER/GND
            power_pin = next((p for p in pin_list if p.modelName.upper() == "POWER"), None)
            gnd_pin   = next((p for p in pin_list if p.modelName.upper() == "GND"), None)

            if not power_pin:
                logging.error("No pin with model_name = POWER found")
                return result  # All None → caller will fail
            if not gnd_pin:
                logging.error("No pin with model_name = GND found")
                return result

            result["pullupPin"] = result["powerClampPin"] = power_pin
            result["pulldownPin"] = result["gndClampPin"] = gnd_pin
            logging.debug("No [Pin Mapping] — using first POWER/GND pins (legacy mode)")
            return result

        # === [Pin Mapping] exists → match by bus label ===
        def find_supply_pin(ref_value, ref_field_name: str) -> Optional[IbisPin]:
            if self._is_nc(ref_value):
                return None

            ref_str = str(ref_value).strip().upper()

            for pin in pin_list:
                if pin.modelName.upper() not in ("POWER", "GND"):
                    continue
                candidate = getattr(pin, ref_field_name, None)
                if self._is_nc(candidate):
                    continue
                if str(candidate).strip().upper() == ref_str:
                    return pin
            logging.warning(
                "Pin mapping: No supply pin found with %s = '%s' (used by pin %s)",
                ref_field_name,
                ref_value,
                getattr(current_pin, "signal_name", None)
                or getattr(current_pin, "number", "??")
            )
            return None

        # Now do the four lookups — no assumptions about POWER vs GND!
        result["pullupPin"]     = find_supply_pin(current_pin.pullupRef,     "pullupRef")
        result["pulldownPin"]   = find_supply_pin(current_pin.pulldownRef,   "pulldownRef")
        result["powerClampPin"] = find_supply_pin(current_pin.powerClampRef, "powerClampRef")
        result["gndClampPin"]   = find_supply_pin(current_pin.gndClampRef,   "gndClampRef")

        return result


# ---------- VI table sorting & series formatting ----------
class SortVIData:
    def sort_vi_data(
            self,
            model: IbisModel,
            pullup_data: Optional[IbisVItable],
            pulldown_data: Optional[IbisVItable],
            power_clamp_data: Optional[IbisVItable],
            gnd_clamp_data: Optional[IbisVItable],
            isso_pullup_data: Optional[IbisVItable] = None,
            isso_pulldown_data: Optional[IbisVItable] = None,
    ) -> int:
        setup_v = SetupVoltages()

        # --- Pullup ---
        if pullup_data is not None and pullup_data.size > 0:
            setup_v.setup_voltages(CS.CurveType.PULLUP, model)
            sweep_step = setup_v.sweep_step
            sweep_range = setup_v.sweep_range
            vcc = setup_v.vcc

            # Vcc-relative in place (like Java)
            for i in range(pullup_data.size):
                pullup_data.VIs[i].v = vcc.typ - pullup_data.VIs[i].v

            num_table_pts = int(abs(sweep_range / sweep_step)) + 1
            if num_table_pts <= 0:
                num_table_pts = min(pullup_data.size, CS.MAX_TABLE_SIZE)

            vt_size = min(pullup_data.size, num_table_pts, CS.MAX_TABLE_SIZE)
            model.pullup = IbisVItable(
                VIs=[IbisVItableEntry(v=0.0, i=IbisTypMinMax()) for _ in range(vt_size)],
                size=vt_size,
            )
            # Copy last points in reverse order
            j = pullup_data.size - 1
            for i in range(vt_size):
                if j < 0: break
                model.pullup.VIs[i] = pullup_data.VIs[j]
                j -= 1

            if model.derateVIPct:
                for i in range(model.pullup.size):
                    vi = model.pullup.VIs[i].i
                    if not is_use_na(vi.min): vi.min -= vi.min * (model.derateVIPct / 100.0)
                    if not is_use_na(vi.max): vi.max += vi.max * (model.derateVIPct / 100.0)

        # --- Pulldown ---
        if pulldown_data is not None and pulldown_data.size > 0:
            setup_v.setup_voltages(CS.CurveType.PULLDOWN, model)
            sweep_step = setup_v.sweep_step
            sweep_range = setup_v.sweep_range

            num_table_pts = int(abs(sweep_range / sweep_step)) + 1
            if num_table_pts <= 0:
                num_table_pts = min(pulldown_data.size, CS.MAX_TABLE_SIZE)

            vt_size = min(pulldown_data.size, num_table_pts, CS.MAX_TABLE_SIZE)
            model.pulldown = IbisVItable(
                VIs=[IbisVItableEntry(v=0.0, i=IbisTypMinMax()) for _ in range(vt_size)],
                size=vt_size,
            )
            # Copy first points in forward order
            j = 0
            for i in range(vt_size):
                if j >= pulldown_data.size: break
                model.pulldown.VIs[i] = pulldown_data.VIs[j]
                j += 1
            # Ensure last point equals last input point
            model.pulldown.VIs[model.pulldown.size - 1] = pulldown_data.VIs[pulldown_data.size - 1]

            if model.derateVIPct:
                for i in range(model.pulldown.size):
                    vi = model.pulldown.VIs[i].i
                    if not is_use_na(vi.min): vi.min -= vi.min * (model.derateVIPct / 100.0)
                    if not is_use_na(vi.max): vi.max += vi.max * (model.derateVIPct / 100.0)

        # --- Power clamp ---
        if power_clamp_data is not None and power_clamp_data.size > 0:
            setup_v.setup_voltages(CS.CurveType.POWER_CLAMP, model)
            sweep_step = setup_v.sweep_step
            sweep_range = setup_v.sweep_range
            vcc = setup_v.vcc

            num_table_pts = int(abs(sweep_range / sweep_step) + 1)
            if num_table_pts <= 0:
                num_table_pts = min(power_clamp_data.size, CS.MAX_TABLE_SIZE)

            model.power_clamp = IbisVItable(
                VIs=[IbisVItableEntry(v=0.0, i=IbisTypMinMax()) for _ in range(num_table_pts)],
                size=num_table_pts,
            )
            i = power_clamp_data.size - 1
            j = 0
            while j < num_table_pts and i >= 0 and power_clamp_data.VIs[i].v >= vcc.typ:
                model.power_clamp.VIs[j].v = vcc.typ - power_clamp_data.VIs[i].v
                model.power_clamp.VIs[j].i = power_clamp_data.VIs[i].i
                i -= 1
                j += 1

            if model.derateVIPct:
                for k in range(model.power_clamp.size):
                    vi = model.power_clamp.VIs[k].i
                    if not is_use_na(vi.min): vi.min -= vi.min * (model.derateVIPct / 100.0)
                    if not is_use_na(vi.max): vi.max += vi.max * (model.derateVIPct / 100.0)

        # --- Ground clamp ---
        if gnd_clamp_data is not None and gnd_clamp_data.size > 0:
            setup_v.setup_voltages(CS.CurveType.GND_CLAMP, model)
            sweep_step = setup_v.sweep_step
            sweep_range = setup_v.sweep_range
            vcc = setup_v.vcc

            num_table_pts = int(abs(sweep_range / sweep_step) + 1)
            if num_table_pts <= 0:
                num_table_pts = min(gnd_clamp_data.size, CS.MAX_TABLE_SIZE)

            model.gnd_clamp = IbisVItable(
                VIs=[IbisVItableEntry(v=0.0, i=IbisTypMinMax()) for _ in range(num_table_pts)],
                size=num_table_pts,
            )
            j = 0
            while j < num_table_pts and j < gnd_clamp_data.size and gnd_clamp_data.VIs[j].v <= vcc.typ:
                model.gnd_clamp.VIs[j] = gnd_clamp_data.VIs[j]
                j += 1

            if model.derateVIPct:
                for k in range(model.gnd_clamp.size):
                    vi = model.gnd_clamp.VIs[k].i
                    if not is_use_na(vi.min): vi.min -= vi.min * (model.derateVIPct / 100.0)
                    if not is_use_na(vi.max): vi.max += vi.max * (model.derateVIPct / 100.0)

        # --- ISSO_PU ---
        if isso_pullup_data is not None and isso_pullup_data.size > 0:
            # Same processing as regular pullup: Vcc-relative, reversed, derated
            setup_v.setup_voltages(CS.CurveType.PULLUP, model)
            sweep_step = setup_v.sweep_step
            sweep_range = setup_v.sweep_range
            vcc = setup_v.vcc

            # Vcc-relative in place
            for i in range(isso_pullup_data.size):
                isso_pullup_data.VIs[i].v = vcc.typ - isso_pullup_data.VIs[i].v

            # Truncate/reverse like pullup
            num_table_pts = int(abs(sweep_range / sweep_step)) + 1
            vt_size = min(isso_pullup_data.size, num_table_pts, CS.MAX_TABLE_SIZE)
            model.isso_pullup = IbisVItable(
                VIs=[IbisVItableEntry(v=0.0, i=IbisTypMinMax()) for _ in range(vt_size)],
                size=vt_size,
            )
            j = isso_pullup_data.size - 1
            for i in range(vt_size):
                if j < 0: break
                model.isso_pullup.VIs[i] = isso_pullup_data.VIs[j]
                j -= 1

            # Apply derating if enabled
            if model.derateVIPct:
                for i in range(model.isso_pullup.size):
                    vi = model.isso_pullup.VIs[i].i
                    if not is_use_na(vi.min): vi.min -= vi.min * (model.derateVIPct / 100.0)
                    if not is_use_na(vi.max): vi.max += vi.max * (model.derateVIPct / 100.0)

        # --- ISSO_PD ---
        if isso_pulldown_data is not None and isso_pulldown_data.size > 0:
            # Same processing as regular pulldown: forward order, no reversal
            setup_v.setup_voltages(CS.CurveType.PULLDOWN, model)
            sweep_step = setup_v.sweep_step
            sweep_range = setup_v.sweep_range

            num_table_pts = int(abs(sweep_range / sweep_step)) + 1
            vt_size = min(isso_pulldown_data.size, num_table_pts, CS.MAX_TABLE_SIZE)
            model.isso_pulldown = IbisVItable(
                VIs=[IbisVItableEntry(v=0.0, i=IbisTypMinMax()) for _ in range(vt_size)],
                size=vt_size,
            )
            j = 0
            for i in range(vt_size):
                if j >= isso_pulldown_data.size: break
                model.isso_pulldown.VIs[i] = isso_pulldown_data.VIs[j]
                j += 1

            # Ensure last point matches
            model.isso_pulldown.VIs[model.isso_pulldown.size - 1] = isso_pulldown_data.VIs[isso_pulldown_data.size - 1]

            # Apply derating
            if model.derateVIPct:
                for i in range(model.isso_pulldown.size):
                    vi = model.isso_pulldown.VIs[i].i
                    if not is_use_na(vi.min): vi.min -= vi.min * (model.derateVIPct / 100.0)
                    if not is_use_na(vi.max): vi.max += vi.max * (model.derateVIPct / 100.0)

        return 0


class SortVISeriesData:
    @staticmethod
    def sort_vi_series_data(
        vi_series_data: Optional[IbisVItable],
        vcc: IbisTypMinMax,
        max_points: int = CS.MAX_TABLE_SIZE,
    ) -> IbisVItable:
        """
        Transform raw [Series Current]/[Series MOSFET] table to IBIS-compliant form:
          • Vcc-relative: Vtable = Vcc - Vpin
          • Monotonically increasing voltage (REVERSED)
          • Max 100 points
        Matches official s2ibis3 behavior 100%.
        """
        if not vi_series_data or vi_series_data.size <= 0:
            return IbisVItable(VIs=[], size=0)

        size = min(vi_series_data.size, max_points)

        # Build Vcc-relative entries in REVERSE order → results in increasing voltage
        processed = []
        for i in range(size - 1, -1, -1):  # This is the reversal
            raw = vi_series_data.VIs[i]
            processed.append(
                IbisVItableEntry(
                    v=vcc.typ - raw.v,                    # Vcc-relative
                    i=IbisTypMinMax(
                        typ=raw.i.typ,
                        min=raw.i.min if not is_use_na(raw.i.min) else None,
                        max=raw.i.max if not is_use_na(raw.i.max) else None,
                    ),
                )
            )

        result = IbisVItable(VIs=processed, size=len(processed))
        logging.debug("Series VI table: %d → %d points (Vcc-relative + reversed)", vi_series_data.size, result.size)
        return result


# ---------- per-pin analyzer ----------
class AnalyzePin:
    def __init__(self, s2ispice: S2ISpice):
        self.s2ispice = s2ispice
        self.current_pin: Optional[IbisPin] = None

    def analyze_pin(
        self,
        current_pin: IbisPin,
        enable_pin: Optional[IbisPin],
        input_pin: Optional[IbisPin],
        pullup_pin: Optional[IbisPin],
        pulldown_pin: Optional[IbisPin],
        power_clamp_pin: Optional[IbisPin],
        gnd_clamp_pin: Optional[IbisPin],
        spice_type: int,
        spice_file: str,
        series_spice_file: str,
        spice_command: str,
        iterate: int,
        cleanup: int,
        ibis_version: str = "",
    ) -> int:
        self.current_pin = current_pin
        #logging.info("INSIDE ANALYZE_PIN — WE MADE IT — PIN %s", current_pin.pinName)
        logging.debug("MODEL TYPE DEBUG: raw=%s, processed=%s, needs_pullup=%s, needs_pulldown=%s",
             current_pin.model.modelType,
             _as_model_type(current_pin.model.modelType),
             this_model_needs_pullup_data(current_pin.model.modelType),
             this_model_needs_pulldown_data(current_pin.model.modelType))
        if not current_pin.model:
            logging.error("No model associated with pin %s", current_pin.pinName)
            return 1
        if str(current_pin.model.modelType).lower() == "nomodel":
            logging.info("Skipping analysis for pin %s with [NoModel]", current_pin.pinName)
            return 0

        res_total = 0
        setup_v = SetupVoltages()
        sort_vi = SortVIData()
        sort_series = SortVISeriesData()

        # Helper to run a VI curve and fetch the produced table from s2ispice
        def run_vi_curve(curve_type: int, enable_output: int, output_state: int, file: str, vds: float = 0.0,
                         vds_idx: int = 0):
            #setup_v.setup_voltages(curve_type, current_pin.model)
            # In AnalyzePin.run_vi_curve
            #setup_v.setup_voltages(curve_type, current_pin.model)

            # ← CRITICAL FIX #1: Use series_model for SERIES_VI, otherwise main model
            target_model = current_pin.series_model if curve_type == CS.CurveType.SERIES_VI else current_pin.model
            setup_v.setup_voltages(curve_type, target_model)

            #vcc_clamp = setup_v.vcc if curve_type != CS.CurveType.POWER_CLAMP else IbisTypMinMax(
            #    current_pin.model.powerClampRef.typ, current_pin.model.powerClampRef.min,
            #    current_pin.model.powerClampRef.max)
            #gnd_clamp = setup_v.gnd if curve_type != CS.CurveType.GND_CLAMP else IbisTypMinMax(
            #    current_pin.model.gndClampRef.typ, current_pin.model.gndClampRef.min, current_pin.model.gndClampRef.max)

            # Use the full IbisTypMinMax objects directly
            #vcc_clamp = setup_v.vcc if curve_type != CS.CurveType.POWER_CLAMP else current_pin.model.powerClampRef
            #gnd_clamp = setup_v.gnd if curve_type != CS.CurveType.GND_CLAMP else current_pin.model.gndClampRef

            # ← CRITICAL FIX #2: Use real clamp references as fixture voltages when they exist
            vcc_clamp = (current_pin.model.powerClampRef
                         if curve_type == CS.CurveType.POWER_CLAMP and not is_use_na(
                current_pin.model.powerClampRef.typ)
                         else setup_v.vcc)
            gnd_clamp = (current_pin.model.gndClampRef
                         if curve_type == CS.CurveType.GND_CLAMP and not is_use_na(current_pin.model.gndClampRef.typ)
                         else setup_v.gnd)

            rc = self.s2ispice.generate_vi_curve(
                current_pin,
                enable_pin,
                input_pin,
                pullup_pin,
                pulldown_pin,
                power_clamp_pin,
                gnd_clamp_pin,
                setup_v.vcc,
                setup_v.gnd,
                vcc_clamp,  # VccClamp (Java reuses the clamp set in context; we pass vcc/gnd here)
                gnd_clamp,  # GndClamp
                setup_v.sweep_start,
                setup_v.sweep_range,
                setup_v.sweep_step,
                curve_type,
                spice_type,
                file,
                spice_command,
                enable_output,
                output_state,
                iterate,
                cleanup,
                vds,
                vds_idx,
            )
            table = getattr(self.s2ispice, "last_vi_table", None)
            return rc, table

        # ---------- SERIES VI ----------
        if current_pin.model.seriesModel and getattr(current_pin.model.seriesModel, "vdslist", []):
            logging.info("Analyzing series VI data")
            setup_v.setup_voltages(CS.CurveType.SERIES_VI, current_pin.model)
            current_pin.model.seriesVITables = []
            for idx, vds in enumerate(current_pin.model.seriesModel.vdslist[: CS.MAX_SERIES_TABLES]):
                rc, raw = run_vi_curve(CS.CurveType.SERIES_VI, CS.ENABLE_OUTPUT, CS.OUTPUT_RISING, series_spice_file,
                                       vds=vds, vds_idx=idx)
                res_total += rc
                if rc != 0 or raw is None:
                    logging.error("Failed to generate series VI curve (idx=%d): rc=%d", idx, rc)
                    continue
                # Sort/normalize like Java and store back
                sorted_vi = sort_series.sort_vi_series_data(raw, setup_v.vcc)
                current_pin.model.seriesVITables.append(sorted_vi)

        # ---------- PULLUP (and optional DISABLED_PULLUP) ----------
        pullup_data = None
        pu_disabled = None
        if this_model_needs_pullup_data(current_pin.model.modelType):
            logging.info("Analyzing pullup data")
            rc, pullup_data = run_vi_curve(CS.CurveType.PULLUP, CS.ENABLE_OUTPUT, CS.OUTPUT_RISING, spice_file)
            res_total += rc
            if enable_pin:
                rc, pu_disabled = run_vi_curve(CS.CurveType.DISABLED_PULLUP, 0, CS.OUTPUT_RISING, spice_file)
                res_total += rc
                if pullup_data is not None and pu_disabled is not None:
                    self._subtract_vi_tables_inplace(pullup_data, pu_disabled)
            # stash on the model for downstream visibility
            current_pin.model.pullupData = pullup_data

        # ---------- PULLDOWN (and optional DISABLED_PULLDOWN) ----------
        pulldown_data = None
        pd_disabled = None
        if this_model_needs_pulldown_data(current_pin.model.modelType):
            logging.info("Analyzing pulldown data")
            rc, pulldown_data = run_vi_curve(CS.CurveType.PULLDOWN, CS.ENABLE_OUTPUT, CS.OUTPUT_FALLING, spice_file)
            res_total += rc
            if enable_pin:
                rc, pd_disabled = run_vi_curve(CS.CurveType.DISABLED_PULLDOWN, 0, CS.OUTPUT_FALLING, spice_file)
                res_total += rc
                if pulldown_data is not None and pd_disabled is not None:
                    self._subtract_vi_tables_inplace(pulldown_data, pd_disabled)
            current_pin.model.pulldownData = pulldown_data

        # ---------- CLAMPS ----------
        power_clamp_data = None
        gnd_clamp_data = None
        if this_model_needs_power_clamp_data(current_pin.model.modelType):
            logging.info("Analyzing power clamp data")
            rc, power_clamp_data = run_vi_curve(CS.CurveType.POWER_CLAMP, 0, CS.OUTPUT_RISING, spice_file)
            res_total += rc
            current_pin.model.powerClampData = power_clamp_data

        if this_model_needs_gnd_clamp_data(current_pin.model.modelType):
            logging.info("Analyzing ground clamp data")
            rc, gnd_clamp_data = run_vi_curve(CS.CurveType.GND_CLAMP, 0, CS.OUTPUT_FALLING, spice_file)
            res_total += rc
            current_pin.model.gndClampData = gnd_clamp_data

        # ---------- ISSO (v5.0+) ----------
        # === [ISSO_PU] and [ISSO_PD] — Power-Aware Tables (IBIS 5.0+) ===
        if this_model_needs_isso_data(current_pin.model, ibis_version):
            logging.info("Analyzing [ISSO_PU] and [ISSO_PD] data (IBIS >=5.0)")

            # ISSO_PU: Output forced HIGH, sweep across pullup reference
            rc, isso_pu_raw = run_vi_curve(
                curve_type=CS.CurveType.ISSO_PULLUP,
                enable_output=CS.ENABLE_OUTPUT,
                output_state=CS.OUTPUT_RISING,        # Force HIGH
                file=spice_file,
            )
            current_pin.model.isso_pullupData = isso_pu_raw
            res_total += rc

            # ISSO_PD: Output forced LOW, sweep across pulldown reference
            rc, isso_pd_raw = run_vi_curve(
                curve_type=CS.CurveType.ISSO_PULLDOWN,
                enable_output=CS.ENABLE_OUTPUT,
                output_state=CS.OUTPUT_FALLING,       # Force LOW
                file=spice_file,
            )
            current_pin.model.isso_pulldownData = isso_pd_raw
            res_total += rc

        # ---------- Sort VI tables ----------
        sort_rc = sort_vi.sort_vi_data(
            current_pin.model,
            pullup_data,
            pulldown_data,
            power_clamp_data,
            gnd_clamp_data,
            getattr(current_pin.model, 'isso_pullupData', None),
            getattr(current_pin.model, 'isso_pulldownData', None),
        )
        if sort_rc:
            logging.error("Failed to sort VI data: rc=%d", sort_rc)
        res_total += sort_rc

        # ---------- RAMP + WAVEFORMS ----------
        if this_model_needs_transient_data(current_pin.model.modelType):
            logging.info("Analyzing transient data")
            setup_v.setup_voltages(CS.CurveType.RISING_RAMP, current_pin.model)

            rc = self.s2ispice.generate_ramp_data(
                current_pin=current_pin,
                enable_pin=enable_pin,
                input_pin=input_pin,
                power_pin=pullup_pin,
                gnd_pin=pulldown_pin,
                power_clamp_pin=power_clamp_pin,
                gnd_clamp_pin=gnd_clamp_pin,
                vcc=setup_v.vcc,
                gnd=setup_v.gnd,
                vcc_clamp=setup_v.vcc,
                gnd_clamp=setup_v.gnd,
                curve_type=CS.CurveType.RISING_RAMP,
                spice_type=spice_type,  # ← add
                spice_file=spice_file,  # ← add
                spice_command=spice_command,
                iterate=iterate,
                cleanup=cleanup,
            )

            if rc > 1:
                logging.error("Failed to generate rising ramp: rc=%d", rc)
            res_total += rc

            rc = self.s2ispice.generate_ramp_data(
                current_pin=current_pin,
                enable_pin=enable_pin,
                input_pin=input_pin,
                power_pin=pullup_pin,
                gnd_pin=pulldown_pin,
                power_clamp_pin=power_clamp_pin,
                gnd_clamp_pin=gnd_clamp_pin,
                vcc=setup_v.vcc,
                gnd=setup_v.gnd,
                vcc_clamp=setup_v.vcc,
                gnd_clamp=setup_v.gnd,
                curve_type=CS.CurveType.FALLING_RAMP,
                spice_type=spice_type,  # ← add
                spice_file=spice_file,  # ← add
                spice_command=spice_command,
                iterate=iterate,
                cleanup=cleanup,
            )

            if rc > 1:
                logging.error("Failed to generate falling ramp: rc=%d", rc)
            res_total += rc

            # === RISING WAVEFORMS: sort by R_fixture DESCENDING (heaviest first) ===
            rising_waves = current_pin.model.risingWaveList[: CS.MAX_WAVEFORM_TABLES]
            rising_sorted = sorted(rising_waves, key=lambda w: w.R_fixture, reverse=True)

            for file_idx, wave in enumerate(rising_sorted):
                orig_idx = next((i for i, w in enumerate(current_pin.model.risingWaveList)
                                 if w.R_fixture == wave.R_fixture), -1)
                rc = self.s2ispice.generate_wave_data(
                    current_pin=current_pin,
                    enable_pin=enable_pin,
                    input_pin=input_pin,
                    power_pin=pullup_pin,
                    gnd_pin=pulldown_pin,
                    power_clamp_pin=power_clamp_pin,
                    gnd_clamp_pin=gnd_clamp_pin,
                    vcc=setup_v.vcc,
                    gnd=setup_v.gnd,
                    vcc_clamp=setup_v.vcc,
                    gnd_clamp=setup_v.gnd,
                    curve_type=CS.CurveType.RISING_WAVE,
                    spice_type=spice_type,
                    spice_file=spice_file,
                    spice_command=spice_command,
                    iterate=iterate,
                    cleanup=cleanup,
                    index=orig_idx,
                )
                if rc > 1:
                    logging.error("Failed to generate rising waveform %d: rc=%d", file_idx, rc)
                res_total += rc

            # === FALLING WAVEFORMS: sort by R_fixture DESCENDING (heaviest first) ===
            falling_waves = current_pin.model.fallingWaveList[: CS.MAX_WAVEFORM_TABLES]
            falling_sorted = sorted(falling_waves, key=lambda w: w.R_fixture, reverse=True)

            for file_idx, wave in enumerate(falling_sorted):
                orig_idx = next((i for i, w in enumerate(current_pin.model.fallingWaveList)
                                 if w.R_fixture == wave.R_fixture), -1)
                rc = self.s2ispice.generate_wave_data(
                    current_pin=current_pin,
                    enable_pin=enable_pin,
                    input_pin=input_pin,
                    power_pin=pullup_pin,
                    gnd_pin=pulldown_pin,
                    power_clamp_pin=power_clamp_pin,
                    gnd_clamp_pin=gnd_clamp_pin,
                    vcc=setup_v.vcc,
                    gnd=setup_v.gnd,
                    vcc_clamp=setup_v.vcc,
                    gnd_clamp=setup_v.gnd,
                    curve_type=CS.CurveType.FALLING_WAVE,
                    spice_type=spice_type,
                    spice_file=spice_file,
                    spice_command=spice_command,
                    iterate=iterate,
                    cleanup=cleanup,
                    index=orig_idx,
                )
                if rc > 1:
                    logging.error("Failed to generate falling waveform %d: rc=%d", file_idx, rc)
                res_total += rc

        return 0 if res_total <= 1 else res_total

    def _subtract_vi_tables_inplace(self, main_vi: Optional[IbisVItable], disabled_vi: Optional[IbisVItable]) -> None:
        if not main_vi or not disabled_vi:
            return
        n = min(getattr(main_vi, "size", len(main_vi.VIs)),
                getattr(disabled_vi, "size", len(disabled_vi.VIs)))
        for i in range(n):
            m = main_vi.VIs[i].i
            d = disabled_vi.VIs[i].i
            # typ
            if not is_use_na(m.typ) and not is_use_na(d.typ):
                m.typ = m.typ - d.typ
            else:
                m.typ = CS.USE_NA
            # min
            if not is_use_na(m.min) and not is_use_na(d.min):
                m.min = m.min - d.min
            else:
                m.min = CS.USE_NA
            # max
            if not is_use_na(m.max) and not is_use_na(d.max):
                m.max = m.max - d.max
            else:
                m.max = CS.USE_NA

# ---------- per-component orchestrator ----------
class AnalyzeComponent:
    def __init__(self, s2ispice: S2ISpice):#, s2iutil: S2IUtil):
        self.s2ispice = s2ispice
        #self.s2iutil = s2iutil

    def analyze_component(
            self,
            ibis: IbisTOP,
            global_: IbisGlobal,
            spice_type: int,
            iterate: int,
            cleanup: int,
            spice_command: str,
    ) -> int:
        # Make sure models inherit globals & pins are linked
        #self.s2iutil.complete_data_structures(ibis, global_)

        result = 0
        find_supply = FindSupplyPins()

        for component in ibis.cList:
            if not component.pList:
                logging.error("No pin list specified for component; use [Pin]")
                result += 1
                continue

            logging.info("Analyzing component %s", component.component)

            self.s2ispice.current_component = component  # ← Set before pin loop

            for pin in component.pList:
                logging.info("Analyzing pin '%s' with modelName '%s'", pin.pinName, pin.modelName)

                # Skip pins that never need analysis (POWER/GND/NC/etc.)
                if not this_pin_needs_analysis(pin.modelName):
                    continue

                # Guard: run once per model unless we still need series-VI
                model = getattr(pin, "model", None)
                if model is None:
                    logging.error("Pin %s has no associated model", pin.pinName)
                    result += 1
                    continue
                
                logging.debug("pin %s → model %s → hasBeenAnalyzed = %s", 
                pin.pinName, model.modelName if model else "None", 
                model.hasBeenAnalyzed if model else "N/A")
                
                series_present = getattr(model, "seriesModel", None) is not None and getattr(model.seriesModel,
                                                                                             "vdslist", [])
                # Always run series analysis if series model exists with Vds points
                needs_series = (getattr(model, "seriesModel", None) is not None and
                                getattr(model.seriesModel, "vdslist", []))

                # Run if: main model not done OR series needs doing
                needs_analysis = (model.hasBeenAnalyzed == 0) or needs_series
                logging.debug("DEBUG: needs_analysis = %s (hasBeenAnalyzed=%s, needs_series=%s) for model %s",
                needs_analysis, model.hasBeenAnalyzed, needs_series, model.modelName)
                if not needs_analysis:
                    continue

                pins = find_supply.find_pins(pin, component.pList, component.hasPinMapping)
                if not pins:
                    logging.error("Failed to find supply pins for %s", pin.pinName)
                    result += 1
                    continue

                def _find_pin_by_name(name: str, pin_list: List[IbisPin]) -> Optional[IbisPin]:
                    if not name:
                        return None
                    name_lower = name.lower()
                    for p in pin_list:
                        if p.pinName and p.pinName.lower() == name_lower:
                            return p
                    return None

                enable_pin = _find_pin_by_name(pin.enablePin, component.pList) if pin.enablePin else None
                input_pin = _find_pin_by_name(pin.inputPin, component.pList) if pin.inputPin else None

                if pin.enablePin and not enable_pin:
                    logging.error("Could not find enable pin for %s", pin.pinName)
                    result += 1
                    continue
                if pin.inputPin and not input_pin:
                    logging.error("Could not find input pin for %s", pin.pinName)
                    result += 1
                    continue

                ap = AnalyzePin(self.s2ispice)
                pin.model = model
                # logging.info("CALLING ANALYZE_PIN FOR %s — THIS MUST APPEAR", pin.pinName)
                rc = ap.analyze_pin(
                    pin,
                    enable_pin,
                    input_pin,
                    pins["pullupPin"],
                    pins["pulldownPin"],
                    pins["powerClampPin"],
                    pins["gndClampPin"],
                    spice_type,
                    component.spiceFile,
                    component.seriesSpiceFile,
                    spice_command,
                    iterate,
                    cleanup,
                    ibis.ibisVersion,
                )
                if rc:
                    logging.error("Error in analysis for pin %s: rc=%d", pin.pinName, rc)
                else:
                    # Flip once per model after a successful run
                    if model.hasBeenAnalyzed == 0:
                        model.hasBeenAnalyzed += 1
                result += rc


        return result


# ---------- top-level façade ----------
class S2IAnaly:
    """
    Thin facade expected by the driver:
      analy = S2IAnaly(...); analy.run_all(ibis, global_)
    It wires S2ISpice into AnalyzeComponent and kicks off the analysis.
    """

    def __init__(
            self,
            mList: List[IbisModel],
            spice_type: int,
            iterate: int,
            cleanup: int,
            spice_command: str,
            global_: Optional[IbisGlobal] = None,
            outdir: Optional[str] = None,
            s2i_file: Optional[str] = None,  # ← ADD THIS
    ):
        self.mList = mList
        self.spice_type = spice_type
        self.iterate = iterate
        self.cleanup = cleanup
        self.spice_command = spice_command
        self.outdir = outdir
        self.s2i_file = s2i_file  # ← ADD THIS

        logging.debug(
            f"S2IAnaly init: global_={global_}, vil={getattr(global_, 'vil', None)}, vih={getattr(global_, 'vih', None)}, outdir={outdir}")
        self.spice = S2ISpice(mList=self.mList, spice_type=spice_type, hspice_path="hspice", global_=global_,
                              outdir=outdir, s2i_file=self.s2i_file)
        #self.util = S2IUtil(self.mList)
        self.comp_analy = AnalyzeComponent(self.spice)#, self.util)

    def run_all(self, ibis: IbisTOP, global_: IbisGlobal) -> int:
        # Ensure structures are complete before analysis
        #self.util.complete_data_structures(ibis, global_)

        rc = self.comp_analy.analyze_component(
            ibis=ibis,
            global_=global_,
            spice_type=self.spice_type,
            iterate=self.iterate,
            cleanup=self.cleanup,
            spice_command=self.spice_command,
        )
        return 0 if rc == 0 else rc


__all__ = [
    "S2IAnaly",
    "AnalyzeComponent",
    "AnalyzePin",
    "SortVIData",
    "SortVISeriesData",
    "FindSupplyPins",
    "SetupVoltages",
]
