"""Package copy of s2ioutput.py with package imports."""
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

        # Minimal version mapping to avoid requiring constants not present
        version_str = getattr(self.ibis_head, 'ibisVersion', '3.2')

        self._print_keyword(f, "[IBIS Ver]", version_str)
        self._print_keyword(f, "[File Name]", self.ibis_head.thisFileName)
        self._print_keyword(f, "[File Rev]", self.ibis_head.fileRev)
        self._print_keyword(f, "[Date]", self.ibis_head.date)
        self._print_multiline(f, "[Source]", self.ibis_head.source)
        self._print_multiline(f, "[Notes]", self.ibis_head.notes)
        self._print_multiline(f, "[Disclaimer]", self.ibis_head.disclaimer)
        if getattr(self.ibis_head, 'copyright', None):
            self._print_multiline(f, "[Copyright]", self.ibis_head.copyright)
        f.write("\n")

        for comp in reversed(self.ibis_head.cList or []):
            self._print_component(f, comp, version_str)

        for model in self.ibis_head.mList or []:
            if not getattr(model, "noModel", False):
                self._print_model(f, model, version_str)

        f.write("[End]\n")

    def _print_component(self, f, comp: IbisComponent, ibis_ver: str) -> None:
        self._print_header(f, comp.component, "Component")
        self._print_keyword(f, "[Component]", comp.component)
        self._print_keyword(f, "[Manufacturer]", comp.manufacturer)

        # Print [Package]
        f.write("[Package]\n")
        self._print_typ_min_max_header(f)
        self._print_keyword(f, "R_pkg", self._fmt_tmm(comp.pinParasitics.R_pkg, "Ohm"))
        self._print_keyword(f, "L_pkg", self._fmt_tmm(comp.pinParasitics.L_pkg, "H"))
        self._print_keyword(f, "C_pkg", self._fmt_tmm(comp.pinParasitics.C_pkg, "F"))
        f.write("\n")

        if comp.pList:
            reversed_pins = comp.pList[::-1]
            f.write("[Pin]  signal_name          model_name           R_pin     L_pin     C_pin\n")
            for pin in reversed_pins:
                self._print_pin(f, pin)
            f.write("\n")

        if getattr(comp, 'hasPinMapping', False) and getattr(comp, 'pmList', None):
            f.write("[Pin Mapping]  pulldown_ref    pullup_ref      gnd_clamp_ref   power_clamp_ref\n")
            for pm in comp.pmList:
                self._print_pin_map(f, pm)
            f.write("\n")

        if getattr(comp, 'dpList', None):
            f.write("[Diff Pin]  inv_pin  vdiff  tdelay_typ  tdelay_min  tdelay_max\n")
            for dp in comp.dpList:
                self._print_diff_pin(f, dp)
            f.write("\n")

        self._print_footer(f, "Component")

    def _print_model(self, f, model: IbisModel, ibis_ver: str) -> None:
        self._print_header(f, model.modelName, "Model")
        self._print_keyword(f, "[Model]", model.modelName)
        self._print_keyword(f, "Model_type", str(model.modelType))
        polarity_str = getattr(model, 'polarity', 'Non-Inverting')
        self._print_keyword(f, "Polarity", polarity_str)
        enable_str = getattr(model, 'enable', 'Active-High')
        self._print_keyword(f, "Enable", enable_str)

        if hasattr(model, 'c_comp'):
            self._print_keyword(f, "C_comp", self._fmt_tmm(model.c_comp, "F"))

        if hasattr(model, 'tempRange') and not math.isnan(getattr(model.tempRange, 'typ', float('nan'))):
            tr = model.tempRange
            tr_str = f"{tr.typ:.4f} {tr.min:.4f} {tr.max:.4f}"
            self._print_keyword(f, "[Temperature Range]", tr_str)

        self._print_vi_table(f, "[Pulldown]", getattr(model, 'pulldown', None))
        self._print_vi_table(f, "[Pullup]", getattr(model, 'pullup', None))

        for wave in getattr(model, 'risingWaveList', []) or []:
            self._print_waveform(f, wave, "Rising")
        for wave in getattr(model, 'fallingWaveList', []) or []:
            self._print_waveform(f, wave, "Falling")

        self._print_footer(f, "Model")

    # Helper printing functions (simplified)
    def _print_keyword(self, f, key: str, value: Optional[str]) -> None:
        if value is None:
            return
        f.write(f"{key} {value}\n")

    def _print_multiline(self, f, key: str, value: Optional[str]) -> None:
        if not value:
            return
        for line in str(value).splitlines():
            f.write(f"{key} {line}\n")

    def _print_typ_min_max_header(self, f) -> None:
        f.write("|  typ     min     max\n")

    def _fmt_tmm(self, tmm: IbisTypMinMax, unit: str = "") -> str:
        if tmm is None:
            return "NA"
        return f"{getattr(tmm, 'typ', 'NA')} {getattr(tmm, 'min', 'NA')} {getattr(tmm, 'max', 'NA')} {unit}"

    def _print_vi_table(self, f, keyword: str, table) -> None:
        if not table or not getattr(table, 'VIs', None):
            return
        f.write(f"{keyword}\n")
        f.write("| Voltage     I(typ)        I(min)        I(max)\n")
        for entry in table.VIs:
            f.write(f"{self._fmt_float(entry.v):>8}  {self._fmt_float(entry.i.typ):>12}  {self._fmt_float(entry.i.min):>12}  {self._fmt_float(entry.i.max):>12}\n")
        f.write("\n")

    def _fmt_float(self, v: float) -> str:
        try:
            return f"{v:.6g}"
        except Exception:
            return str(v)

    def _print_pin(self, f, pin: IbisPin) -> None:
        f.write(f"{pin.pinName:>4}  {getattr(pin,'signalName',''):>20}  {getattr(pin,'modelName',''):>20}  {getattr(pin,'R_pin',''):>8}  {getattr(pin,'L_pin',''):>8}  {getattr(pin,'C_pin',''):>8}\n")

    def _print_pin_map(self, f, pm) -> None:
        f.write(" ")

    def _print_diff_pin(self, f, dp: IbisDiffPin) -> None:
        f.write(f"{dp.invPin} {dp.vdiff.typ} {dp.tdelay_typ} {dp.tdelay_min} {dp.tdelay_max}\n")

    def _print_waveform(self, f, wave: IbisWaveTable, kind: str) -> None:
        f.write(f"[{kind} Waveform]\n")
        for e in wave.waveData:
            f.write(f"{e.t} {e.v.typ} {e.v.min} {e.v.max}\n")

    def _print_header(self, f, name: str, section: str) -> None:
        f.write(f"[{section}] {name}\n")

    def _print_footer(self, f, section: str) -> None:
        f.write(f"[End {section}]\n\n")
