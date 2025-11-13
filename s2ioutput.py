# s2ioutput.py — FINAL, CORRECT, MERGED VERSION
import logging
import math
from typing import List, Optional
from models import (
    IbisTOP, IbisGlobal, IbisComponent, IbisModel, IbisPin,
    IbisDiffPin, IbisSeriesPin, IbisSeriesSwitchGroup,
    IbisVItable, IbisWaveTable, IbisTypMinMax, IbisVItableEntry
)
from s2i_constants import ConstantStuff as CS

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
        self._print_header(f, comp.component, "Component")
        self._print_keyword(f, "[Component]", comp.component)
        self._print_keyword(f, "[Manufacturer]", comp.manufacturer)

        # [Package]
        logging.info("=== [Package] DEBUG for component: %s ===", comp.component)
        if comp.pinParasitics is None:
            logging.info("  comp.pinParasitics = None")
        else:
            logging.info(
                "  R_pkg: typ=%.6f min=%.6f max=%.6f",
                comp.pinParasitics.R_pkg.typ,
                comp.pinParasitics.R_pkg.min,
                comp.pinParasitics.R_pkg.max
            )
            logging.info(
                "  L_pkg: typ=%.6g min=%.6g max=%.6g (H)",
                comp.pinParasitics.L_pkg.typ,
                comp.pinParasitics.L_pkg.min,
                comp.pinParasitics.L_pkg.max
            )
            logging.info(
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

        # [Pin]
        if comp.pList:
            f.write("[Pin]  signal_name          model_name           R_pin     L_pin     C_pin\n")
            for pin in comp.pList:
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
        self._print_header(f, model.modelName, "Model")
        self._print_keyword(f, "[Model]", model.modelName)
        self._print_keyword(f, "Model_type", self._model_type_str(model.modelType))

        polarity = {CS.MODEL_POLARITY_NON_INVERTING: "Non-Inverting", CS.MODEL_POLARITY_INVERTING: "Inverting"}.get(model.polarity)
        if polarity:
            self._print_keyword(f, "Polarity", polarity)

        enable = {CS.MODEL_ENABLE_ACTIVE_HIGH: "Active-High", CS.MODEL_ENABLE_ACTIVE_LOW: "Active-Low"}.get(model.enable)
        if enable:
            self._print_keyword(f, "Enable", enable)

        if not self._is_na(model.Vinl.typ):
            self._print_keyword(f, "Vinl", f"{model.Vinl.typ:.10g}V")
        if not self._is_na(model.Vinh.typ):
            self._print_keyword(f, "Vinh", f"{model.Vinh.typ:.10g}V")

        self._print_keyword(f, "C_comp", self._fmt_tmm(model.c_comp, "F"))

        if ibis_ver != CS.VERSION_ONE_ONE:
            for key, tmm, unit in [
                ("[Temperature Range]", model.tempRange, ""),
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

        # Ramp
        if model.ramp and not self._is_na(model.ramp.dv_r.typ):
            self._print_ramp(f, model.ramp, model.Rload)

        # Waveforms
        for wave in model.risingWaveList or []:
            self._print_waveform(f, wave, "Rising")
        for wave in model.fallingWaveList or []:
            self._print_waveform(f, wave, "Falling")

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

    def _print_ramp(self, f, ramp, rload: float) -> None:
        f.write("[Ramp]\n")
        f.write("| variable    typ          min          max\n")
        for edge, dv, dt in [("r", ramp.dv_r, ramp.dt_r), ("f", ramp.dv_f, ramp.dt_f)]:
            line = f"dV/dt_{edge}     "
            for corner in ['typ', 'min', 'max']:
                dv_val = getattr(dv, corner)
                dt_val = getattr(dt, corner)
                if self._is_na(dv_val) or self._is_na(dt_val) or dt_val == 0:
                    val = "NA"
                else:
                    val = f"{dv_val/dt_val:.4g}"
                line += f"{val:>10}  "
            f.write(line + "\n")
        if not self._is_na(rload):
            f.write(f"R_load = {rload:.4g}\n")
        f.write("\n")

    def _print_waveform(self, f, wave: IbisWaveTable, direction: str) -> None:
        header = f"[{direction} Waveform]"
        params = [self._fmt_float(wave.R_fixture), self._fmt_float(wave.V_fixture)]
        for attr, unit in [
            ("V_fixture_min", ""), ("V_fixture_max", ""),
            ("L_fixture", "H"), ("C_fixture", "F"),
            ("R_dut", ""), ("L_dut", "H"), ("C_dut", "F")
        ]:
            val = getattr(wave, attr, CS.USE_NA)
            if not self._is_na(val):
                params.append(self._fmt_float(val, unit))
        f.write(f"{header} {' '.join(params)}\n")
        f.write("| time       V(typ)       V(min)       V(max)\n")
        for e in wave.waveData or []:
            f.write(f"{self._fmt_float(e.t, 's'):>8}  "
                    f"{self._fmt_float(e.v.typ):>10}  "
                    f"{self._fmt_float(e.v.min):>10}  "
                    f"{self._fmt_float(e.v.max):>10}\n")
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
        if value:
            for line in value.splitlines():
                f.write(f"{keyword} {line}\n")
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
        mapping = {
            CS.ModelType.INPUT: "Input", CS.ModelType.OUTPUT: "Output",
            CS.ModelType.IO: "I/O", CS.ModelType.SERIES: "Series",
            CS.ModelType.SERIES_SWITCH: "Series_switch", CS.ModelType.TERMINATOR: "Terminator",
            CS.ModelType.OPEN_DRAIN: "Open_drain", CS.ModelType.OPEN_SINK: "Open_sink",
            CS.ModelType.OPEN_SOURCE: "Open_source", CS.ModelType.IO_OPEN_DRAIN: "I/O_Open_drain",
            CS.ModelType.IO_OPEN_SINK: "I/O_Open_sink", CS.ModelType.IO_OPEN_SOURCE: "I/O_Open_source",
            CS.ModelType.OUTPUT_ECL: "Output_ECL", CS.ModelType.IO_ECL: "I/O_ECL",
            CS.ModelType.THREE_STATE: "3-state",
        }
        return mapping.get(mt, "Output") if isinstance(mt, int) else str(mt)

    def _is_na(self, x) -> bool:
        return x is None or (isinstance(x, float) and (math.isnan(x) or x == CS.USE_NA))

    def _is_na_tmm(self, tmm: Optional[IbisTypMinMax]) -> bool:
        return not tmm or all(self._is_na(getattr(tmm, c)) for c in ('typ', 'min', 'max'))