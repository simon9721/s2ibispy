# s2ioutput.py — FINAL, CORRECT, MERGED VERSION
import logging
import math
from typing import List, Optional
from s2ibispy.models import (
    IbisTOP, IbisGlobal, IbisComponent, IbisModel, IbisPin,
    IbisDiffPin, IbisSeriesPin, IbisSeriesSwitchGroup,
    IbisVItable, IbisWaveTable, IbisTypMinMax, IbisVItableEntry
)
from s2ibispy.s2i_constants import ConstantStuff as CS

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class IbisWriter:
    def __init__(self, ibis_head: IbisTOP):
        self.ibis_head = ibis_head

    def write_ibis_file(self, filename: Optional[str] = None) -> int:
        filename = filename or self.ibis_head.thisFileName or "buffer.ibs"
        try:
            with open(filename, "w", encoding="utf-8") as f:
                self._print_top(f)
            logging.info(f"IBIS file written: {filename}")
            return 0
        except Exception as e:
            logging.error(f"Failed to write IBIS file: {e}")
            return 1

    def _print_top(self, f) -> None:
        f.write("|************************************************************************\n")
        f.write(f"| IBIS file {self.ibis_head.thisFileName} created by PYS2IBIS3\n")
        f.write("| Missouri S&T EMC Lab\n")
        f.write("|************************************************************************\n\n")

        ver_map = {
            "1.0": CS.VERSION_ONE_ZERO, "1.1": CS.VERSION_ONE_ONE,
            "2.0": CS.VERSION_TWO_ZERO, "2.1": CS.VERSION_TWO_ONE,
            "3.2": CS.VERSION_THREE_TWO,
            # IBIS 5.x+ support (commonly used for ISSO and new keywords)
            "5.0": CS.VERSION_FIVE_ZERO,
            "5.1": CS.VERSION_FIVE_ONE,
            # Future-proof mappings
            "6.0": CS.VERSION_SIX_ZERO,
            "7.0": CS.VERSION_SEVEN_ZERO,
        }
        ibis_ver_int = ver_map.get(self.ibis_head.ibisVersion, CS.VERSION_THREE_TWO)
        version_str = {v: k for k, v in ver_map.items()}.get(ibis_ver_int, "3.2")

        self._print_keyword(f, "[IBIS Ver]", version_str)
        self._print_keyword(f, "[File Name]", self.ibis_head.thisFileName)
        self._print_keyword(f, "[File Rev]", self.ibis_head.fileRev)
        self._print_keyword(f, "[Date]", self.ibis_head.date)
        self._print_multiline(f, "[Source]", self.ibis_head.source)
        self._print_multiline(f, "[Notes]", self.ibis_head.notes)
        self._print_multiline(f, "[Disclaimer]", self.ibis_head.disclaimer)
        if ibis_ver_int != CS.VERSION_ONE_ONE:
            self._print_multiline(f, "[Copyright]", self.ibis_head.copyright)
        f.write("\n")

        for comp in reversed(self.ibis_head.cList or []):
            self._print_component(f, comp, ibis_ver_int)

        for model in self.ibis_head.mList or []:
            if not getattr(model, "noModel", False):
                self._print_model(f, model, ibis_ver_int)

        f.write("[End]\n")

    def _print_component(self, f, comp: IbisComponent, ibis_ver: int) -> None:
        f.write(f"[Component] {comp.component}\n")
        self._print_keyword(f, "[Manufacturer]", comp.manufacturer)

        # [Package]
        logging.debug("=== [Package] DEBUG for component: %s ===", comp.component)
        if comp.pinParasitics is None:
            logging.debug("  comp.pinParasitics = None")
        else:
            logging.debug(
                "  R_pkg: typ=%.6f min=%.6f max=%.6f",
                comp.pinParasitics.R_pkg.typ,
                comp.pinParasitics.R_pkg.min,
                comp.pinParasitics.R_pkg.max
            )
            logging.debug(
                "  L_pkg: typ=%.6g min=%.6g max=%.6g (H)",
                comp.pinParasitics.L_pkg.typ,
                comp.pinParasitics.L_pkg.min,
                comp.pinParasitics.L_pkg.max
            )
            logging.debug(
                "  C_pkg: typ=%.6g min=%.6g max=%.6g (F)",
                comp.pinParasitics.C_pkg.typ,
                comp.pinParasitics.C_pkg.min,
                comp.pinParasitics.C_pkg.max
            )
        # Print [Package] keyword
        f.write("[Package]\n")

        # Print table header
        self._print_typ_min_max_header(f)

        # Print values
        self._print_keyword(f, "R_pkg", self._fmt_tmm(comp.pinParasitics.R_pkg, "Ohm"))
        self._print_keyword(f, "L_pkg", self._fmt_tmm(comp.pinParasitics.L_pkg, "H"))
        self._print_keyword(f, "C_pkg", self._fmt_tmm(comp.pinParasitics.C_pkg, "F"))

        f.write("\n")

        # [Pin] — REVERSE INPUT ORDER (per correct .ibs)
        if comp.pList:
            reversed_pins = comp.pList[::-1]  # Reverse the list
            f.write("[Pin]  signal_name          model_name           R_pin     L_pin     C_pin\n")
            for pin in reversed_pins:
                self._print_pin(f, pin)
            f.write("\n")

        # [Pin Mapping]
        if ibis_ver != CS.VERSION_ONE_ONE and comp.hasPinMapping and comp.pmList:
            f.write("[Pin Mapping]  pulldown_ref    pullup_ref      gnd_clamp_ref   power_clamp_ref\n")
            for pm in comp.pmList:
                self._print_pin_map(f, pm)
            f.write("\n")

        # [Diff Pin]
        if ibis_ver != CS.VERSION_ONE_ONE and comp.dpList:
            f.write("[Diff Pin]  inv_pin  vdiff  tdelay_typ  tdelay_min  tdelay_max\n")
            for dp in comp.dpList:
                self._print_diff_pin(f, dp)
            f.write("\n")

        self._print_footer(f, "Component")

    def _print_model(self, f, model: IbisModel, ibis_ver: int) -> None:
        f.write(f"[Model] {model.modelName}\n")
        # === FIX: Convert string digit to int enum ===
        mt = model.modelType
        if isinstance(mt, str) and mt.isdigit():
            mt = int(mt)
        self._print_keyword(f, "Model_type", self._model_type_str(mt))
        #self._print_keyword(f, "Model_type", self._model_type_str(model.modelType))

        # Always print Polarity (default: Non-Inverting)
        polarity_str = {CS.MODEL_POLARITY_NON_INVERTING: "Non-Inverting", CS.MODEL_POLARITY_INVERTING: "Inverting"}.get(
            model.polarity, "Non-Inverting")
        self._print_keyword(f, "Polarity", polarity_str)

        # Always print Enable (default: Active-High)
        enable_str = {CS.MODEL_ENABLE_ACTIVE_HIGH: "Active-High", CS.MODEL_ENABLE_ACTIVE_LOW: "Active-Low"}.get(
            model.enable, "Active-High")
        self._print_keyword(f, "Enable", enable_str)

        if not self._is_na(model.Vinl.typ):
            self._print_keyword(f, "Vinl", f" = {model.Vinl.typ:.10g}V")
        if not self._is_na(model.Vinh.typ):
            self._print_keyword(f, "Vinh", f" = {model.Vinh.typ:.10g}V")

        self._print_keyword(f, "C_comp", self._fmt_tmm(model.c_comp, "F"))

        # [Temperature Range] — print raw values, no scaling
        if not self._is_na_tmm(model.tempRange):
            tr = model.tempRange
            tr_str = f"{tr.typ:.4f} {tr.min:.4f} {tr.max:.4f}"
            self._print_keyword(f, "[Temperature Range]", tr_str)

        if ibis_ver != CS.VERSION_ONE_ONE:
            for key, tmm, unit in [
                #("[Temperature Range]", model.tempRange, ""),
                ("[Voltage Range]", model.voltageRange, "V"),
                ("[Pullup Reference]", model.pullupRef, "V"),
                ("[Pulldown Reference]", model.pulldownRef, "V"),
                ("[POWER Clamp Reference]", model.powerClampRef, "V"),
                ("[GND Clamp Reference]", model.gndClampRef, "V"),
            ]:
                if not self._is_na_tmm(tmm):
                    self._print_keyword(f, key, self._fmt_tmm(tmm, unit))

        # VI Tables
        self._print_vi_table(f, "[Pulldown]", model.pulldown)
        self._print_vi_table(f, "[Pullup]", model.pullup)
        self._print_clamp_table(f, "[GND Clamp]", model.gnd_clamp, model.clampTol)
        self._print_clamp_table(f, "[POWER Clamp]", model.power_clamp, model.clampTol)

        # [ISSO PU], [ISSO PD] Tables — IBIS 5.0+ only
        if ibis_ver >= CS.VERSION_FIVE_ZERO:
            self._print_vi_table(f, "[ISSO_PU]", model.isso_pullup)
            self._print_vi_table(f, "[ISSO_PD]", model.isso_pulldown)

        # Ramp
        if model.ramp and not self._is_na(model.ramp.dv_r.typ):
            self._print_ramp(f, model.ramp, model.Rload)

        # Waveforms
        for wave in model.risingWaveList or []:
            self._print_waveform(f, wave, "Rising")
            if ibis_ver >= CS.VERSION_FIVE_ZERO:
                self._print_composite_current(f, wave, "Rising")
        for wave in model.fallingWaveList or []:
            self._print_waveform(f, wave, "Falling")
            if ibis_ver >= CS.VERSION_FIVE_ZERO:
                self._print_composite_current(f, wave, "Falling")

        self._print_footer(f, "Model")

    def _print_vi_table(self, f, keyword: str, table: Optional[IbisVItable]) -> None:
        if not table or not table.VIs:
            return
        f.write(f"{keyword}\n")
        f.write("| Voltage     I(typ)        I(min)        I(max)\n")
        for entry in table.VIs:
            f.write(f"{self._fmt_float(entry.v):>8}  "
                    f"{self._fmt_float(entry.i.typ):>12}  "
                    f"{self._fmt_float(entry.i.min):>12}  "
                    f"{self._fmt_float(entry.i.max):>12}\n")
        f.write("\n")

    def _print_clamp_table(self, f, keyword: str, table: Optional[IbisVItable], tol: float) -> None:
        if not table or not table.VIs:
            return
        f.write(f"{keyword}\n")
        f.write("| Voltage     I(typ)        I(min)        I(max)\n")
        for entry in table.VIs:
            i = entry.i
            if abs(i.typ) < tol: i.typ = 0
            if abs(i.min) < tol: i.min = 0
            if abs(i.max) < tol: i.max = 0
            f.write(f"{self._fmt_float(entry.v):>8}  "
                    f"{self._fmt_float(i.typ):>12}  "
                    f"{self._fmt_float(i.min):>12}  "
                    f"{self._fmt_float(i.max):>12}\n")
        f.write("\n")

    def _print_ramp(self, f, ramp, model_rload: float) -> None:
        # Use model.Rload if valid; else use global
        effective_rload = model_rload

        f.write("[Ramp]\n")
        f.write("| variable   typ        min        max\n")

        def format_dt(dt_val: float) -> str:
            if self._is_na(dt_val) or dt_val <= 0:
                return "NA"
            # Convert seconds → nanoseconds, add 'n'
            return f"{dt_val * 1e9:.4g}n"

        def format_dv_dv(dt_val: float, dv_val: float) -> str:
            if self._is_na(dv_val) or self._is_na(dt_val) or dt_val <= 0:
                return "NA"
            dv_str = f"{dv_val:.4f}"
            dt_str = format_dt(dt_val)
            return f"{dv_str}/{dt_str}"

        def format_rload(rload: float) -> str:
            if self._is_na(rload) or rload <= 0:
                return ""
            if rload >= 1e3:
                return f"{rload / 1e3:.4g}k"
            else:
                return f"{rload:.4g}"

        for edge, dv, dt in [("r", ramp.dv_r, ramp.dt_r), ("f", ramp.dv_f, ramp.dt_f)]:
            line = f"dV/dt_{edge} "
            for corner in ['typ', 'min', 'max']:
                dv_val = getattr(dv, corner)
                dt_val = getattr(dt, corner)
                val = format_dv_dv(dt_val, dv_val)
                line += f"{val:>13} "
            f.write(line.rstrip() + "\n")

        rload_str = format_rload(effective_rload)
        if rload_str:
            f.write(f"R_load = {rload_str}\n")

        f.write("\n")

    def _print_waveform(self, f, wave: IbisWaveTable, direction: str) -> None:
        if not wave.waveData:
            return

        # === [Rising/Falling Waveform] Header ===
        f.write(f"[{direction} Waveform]\n")
        f.write(f"R_fixture = {wave.R_fixture:.4g}\n")
        f.write(f"V_fixture = {wave.V_fixture:.4g}\n")
        if wave.V_fixture_min is not None and not math.isnan(wave.V_fixture_min):
            f.write(f"V_fixture_min = {wave.V_fixture_min:.4g}\n")
        if wave.V_fixture_max is not None and not math.isnan(wave.V_fixture_max):
            f.write(f"V_fixture_max = {wave.V_fixture_max:.4g}\n")

        # === Java-Exact Table Header ===
        f.write("|time             V(typ)              V(min)              V(max)\n")

        # === DEBUG: LOG LAST BIN VALUE ===
        last_idx = len(wave.waveData) - 1
        last_pt = wave.waveData[last_idx]
        logging.debug(
            f"[PRINT] {direction} LAST BIN [{last_idx}]: "
            f"t={last_pt.t:.4e}  "
            f"V(typ)={last_pt.v.typ:.6g}  V(min)={last_pt.v.min:.6g}  V(max)={last_pt.v.max:.6g}"
        )

        # === Data Rows — Exact Java Format ===
        for pt in wave.waveData:
            # Time: in ns, 4 decimal places, 'n' suffix, right-aligned to 15 chars
            t_str = f"{pt.t * 1e9:.4f}n"
            t_str = t_str.rjust(15)

            # Voltages: up to 10 significant digits, right-aligned to 15 chars
            v_typ = f"{pt.v.typ:.10g}".rjust(15)
            v_min = f"{pt.v.min:.10g}".rjust(15)
            v_max = f"{pt.v.max:.10g}".rjust(15)

            f.write(f"{t_str}  {v_typ}  {v_min}  {v_max}\n")

        f.write("\n")

    def _print_composite_current(self, f, wave: IbisWaveTable, direction: str) -> None:
        """Print [Composite Current] table following the waveform."""
        if not wave.waveData:
            return

        # Check if any current data exists
        has_current = any(
            not math.isnan(pt.i.typ) or not math.isnan(pt.i.min) or not math.isnan(pt.i.max)
            for pt in wave.waveData
        )
        if not has_current:
            return

        # === [Composite Current] Header ===
        f.write("[Composite Current]\n")
        
        # === Table Header ===
        f.write("|time             I(typ)              I(min)              I(max)\n")

        # === Data Rows — Same format as voltage waveform ===
        for pt in wave.waveData:
            # Time: in ns, 4 decimal places, 'n' suffix, right-aligned to 15 chars
            t_str = f"{pt.t * 1e9:.4f}n"
            t_str = t_str.rjust(15)

            # Currents: use _fmt_float for SI formatting (Amperes → will auto-format as mA with 'm' suffix)
            i_typ = self._fmt_float(pt.i.typ, "A").rjust(15)
            i_min = self._fmt_float(pt.i.min, "A").rjust(15)
            i_max = self._fmt_float(pt.i.max, "A").rjust(15)

            f.write(f"{t_str}  {i_typ}  {i_min}  {i_max}\n")

        f.write("\n")

    def _print_pin(self, f, pin: IbisPin) -> None:
        # If the model is "nomodel" (noModel flag set), comment the line
        if pin.model and getattr(pin.model, "noModel", False):
            f.write(f"| {pin.pinName} {pin.signalName} {pin.modelName}\n")
        else:
            r = self._fmt_float(pin.R_pin) if pin.R_pin != CS.NOT_USED else ""
            l = self._fmt_float(pin.L_pin, "H") if pin.L_pin != CS.NOT_USED else ""
            c = self._fmt_float(pin.C_pin, "F") if pin.C_pin != CS.NOT_USED else ""
            f.write(f"{pin.pinName:<6} {pin.signalName:<20} {pin.modelName:<15} {r:>8} {l:>8} {c:>8}\n")

    def _print_pin_map(self, f, pm) -> None:
        if isinstance(pm, list):
            pd, pu, gc, pc = (pm + [""] * 4)[:4]
            pin = pm[0] if pm else ""
        else:
            pin, pd, pu, gc, pc = pm.pinName, pm.pulldownRef, pm.pullupRef, pm.gndClampRef, pm.powerClampRef
        f.write(f"{pin:<6} {pd:<15} {pu:<15} {gc:<15} {pc:<15}\n")

    def _print_diff_pin(self, f, dp: IbisDiffPin) -> None:
        t_min = self._fmt_float(dp.tdelay_min, "s") if dp.tdelay_min is not None else ""
        t_max = self._fmt_float(dp.tdelay_max, "s") if dp.tdelay_max is not None else ""
        f.write(f"{dp.pinName:<6} {dp.invPin:<8} {self._fmt_float(dp.vdiff.typ):>8} "
                f"{self._fmt_float(dp.tdelay_typ):>10} {t_min:>10} {t_max:>10}\n")

    def _print_keyword(self, f, keyword: str, value: str) -> None:
        if value:
            f.write(f"{keyword} {value}\n")

    def _print_multiline(self, f, keyword: str, value: str) -> None:
        if not value:
            return
        lines = value.splitlines()
        if not lines:
            return
        # Print keyword on first line
        f.write(f"{keyword} {lines[0]}\n")
        # Print remaining lines with leading space
        for line in lines[1:]:
            f.write(f" {line}\n")
        f.write("\n")

    def _print_header(self, f, name: str, kind: str) -> None:
        bar = "|" + "*" * 78 + "\n"
        f.write(bar)
        pad = (78 - len(kind) - len(name) - 1) // 2
        f.write(f"|{' ' * pad}{kind} {name}\n")
        f.write(bar)

    def _print_footer(self, f, kind: str) -> None:
        f.write(f"| End of {kind}\n\n")

    def _print_typ_min_max_header(self, f) -> None:
        f.write("| variable    typ          min          max\n")

    def _fmt_tmm(self, tmm: Optional[IbisTypMinMax], unit: str) -> str:
        if not tmm or self._is_na_tmm(tmm):
            return "NA NA NA"
        return f"{self._si(tmm.typ, unit)} {self._si(tmm.min, unit)} {self._si(tmm.max, unit)}"

    def _si(self, val, unit: str) -> str:
        if self._is_na(val):
            return "NA"
        val = float(val)

        # CRITICAL: START FROM LARGEST SCALE → SMALLEST
        suffixes = [
            ("M", 1e6), ("k", 1e3), ("", 1),
            ("m", 1e-3), ("u", 1e-6), ("n", 1e-9), ("p", 1e-12)
        ]

        for suffix, scale in suffixes:
            scaled = val / scale
            if 0.1 <= abs(scaled) < 1000:
                formatted = f"{scaled:.4f}{suffix}"
                if unit == "Ohm":
                    return formatted
                elif unit == "H":
                    return f"{formatted}H"
                elif unit == "F":
                    return f"{formatted}F"
                else:
                    return f"{formatted}{unit}"

        fallback = f"{val:.4g}"
        if unit == "Ohm":
            return fallback
        elif unit == "H":
            return f"{fallback}H"
        elif unit == "F":
            return f"{fallback}F"
        else:
            return f"{fallback}{unit}"

    def _fmt_float(self, val, unit: str = "") -> str:
        return self._si(val, unit) if not self._is_na(val) else "NA"

    def _model_type_str(self, mt) -> str:
        """
        Convert whatever is in model.modelType → the exact official IBIS string.
        Handles:
          • old integer enums (0,1,2,3,...)
          • new canonical strings ("I/O", "Open_drain", ...)
          • anything else (fallback to "I/O")
        """
        # 1. If it's already a proper string → just return it
        if isinstance(mt, str):
            s = mt.strip()
            if s:  # non-empty
                return s
            # empty string → fall through to mapping below

        # 2. If it's an integer (enum) → map to official string
        if isinstance(mt, int):
            mapping = {
                CS.ModelType.INPUT: "Input",
                CS.ModelType.OUTPUT: "Output",
                CS.ModelType.IO: "I/O",
                CS.ModelType.THREE_STATE: "3-state",
                CS.ModelType.OPEN_DRAIN: "Open_drain",
                CS.ModelType.OPEN_SINK: "Open_sink",
                CS.ModelType.OPEN_SOURCE: "Open_source",
                CS.ModelType.IO_OPEN_DRAIN: "I/O_Open_drain",
                CS.ModelType.IO_OPEN_SINK: "I/O_Open_sink",
                CS.ModelType.IO_OPEN_SOURCE: "I/O_Open_source",
                CS.ModelType.SERIES: "Series",
                CS.ModelType.SERIES_SWITCH: "Series_switch",
                CS.ModelType.TERMINATOR: "Terminator",
                CS.ModelType.INPUT_ECL: "Input_ECL",
                CS.ModelType.OUTPUT_ECL: "Output_ECL",
                CS.ModelType.IO_ECL: "I/O_ECL",
            }
            return mapping.get(mt, "I/O")  # safe default

        # 3. Anything else (None, garbage) → spec-compliant default
        return "I/O"

    def _is_na(self, x) -> bool:
        return x is None or (isinstance(x, float) and (math.isnan(x) or x == CS.USE_NA or x == CS.NOT_USED))

    def _is_na_tmm(self, tmm: Optional[IbisTypMinMax]) -> bool:
        return not tmm or all(self._is_na(getattr(tmm, c)) for c in ('typ', 'min', 'max'))