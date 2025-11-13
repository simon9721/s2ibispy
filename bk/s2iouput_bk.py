# s2ioutput.py
import logging
import math
import os
import sys
from typing import List, Optional

from models import (
    IbisTOP, IbisGlobal, IbisComponent, IbisModel, IbisPin, IbisDiffPin,
    IbisSeriesPin, IbisSeriesSwitchGroup, IbisWaveTable, IbisTypMinMax,
)
from s2i_constants import ConstantStuff as CS

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class S2IOutput:
    def __init__(self) -> None:
        pass

    # -----------------------
    # Public API
    # -----------------------
    def write_ibis_file(self, ibis: IbisTOP, global_: IbisGlobal, mList: List[IbisModel], output_file: str) -> None:
        """Write an IBIS file from completed data structures."""
        logging.info(f"Writing IBIS file to {output_file}")
        try:
            with open(output_file, "w") as f:
                self.write_header(ibis, f)
                self.write_global_params(global_, f)

                # Components (pins, mappings, etc.)
                for component in ibis.cList or []:
                    self.write_component(component, f)

                # Models (type, VI tables, ramp, waveforms)
                for model in mList or []:
                    self.write_model(model, f)

            logging.info(f"IBIS file written successfully: {output_file}")
        except Exception as e:
            logging.error(f"Failed to write IBIS file {output_file}: {e}")
            raise

    # -----------------------
    # Sections
    # -----------------------
    def write_header(self, ibis: IbisTOP, f) -> None:
        """[Header] — spec-compliant header lines."""
        f.write(f"[IBIS Ver] {ibis.ibisVersion or '3.2'}\n")
        if ibis.thisFileName:
            f.write(f"[File Name] {ibis.thisFileName}\n")
        if ibis.fileRev:
            f.write(f"[File Rev] {ibis.fileRev}\n")
        if ibis.date:
            f.write(f"[Date] {ibis.date}\n")
        if ibis.source:
            f.write(f"[Source] {ibis.source}\n")
        if ibis.notes:
            f.write(f"[Notes] {ibis.notes}\n")
        if ibis.disclaimer:
            f.write(f"[Disclaimer] {ibis.disclaimer}\n")
        if ibis.copyright:
            f.write(f"[Copyright] {ibis.copyright}\n")
        f.write("\n")

    def write_global_params(self, global_: IbisGlobal, f) -> None:
        """Global keywords allowed in the root (not per-model)."""
        f.write(f"[Temperature Range] {self.format_typ_min_max(global_.tempRange)}\n")
        f.write(f"[Voltage Range] {self.format_typ_min_max(global_.voltageRange)}\n")
        if not self.is_na_tmm(global_.pullupRef):
            f.write(f"[Pullup Reference] {self.format_typ_min_max(global_.pullupRef)}\n")
        if not self.is_na_tmm(global_.pulldownRef):
            f.write(f"[Pulldown Reference] {self.format_typ_min_max(global_.pulldownRef)}\n")
        if not self.is_na_tmm(global_.powerClampRef):
            f.write(f"[Power Clamp Reference] {self.format_typ_min_max(global_.powerClampRef)}\n")
        if not self.is_na_tmm(global_.gndClampRef):
            f.write(f"[GND Clamp Reference] {self.format_typ_min_max(global_.gndClampRef)}\n")

        # Project-level sim helpers (not standard IBIS keywords, but keeping if you store them)
        if not self.is_na(global_.Rload):
            f.write(f"| Rload (tool hint) {self.n(global_.Rload)}\n")
        if not self.is_na(global_.simTime):
            f.write(f"| SimTime (tool hint) {self.n(global_.simTime)}\n")

        # Package parasitics
        f.write(f"[R_pkg] {self.format_typ_min_max(global_.pinParasitics.R_pkg)}\n")
        f.write(f"[L_pkg] {self.format_typ_min_max(global_.pinParasitics.L_pkg)}\n")
        f.write(f"[C_pkg] {self.format_typ_min_max(global_.pinParasitics.C_pkg)}\n")
        f.write("\n")

    def write_component(self, comp: IbisComponent, f) -> None:
        """[Component] and its sub-sections."""
        f.write(f"[Component] {comp.component}\n")
        f.write(f"[Manufacturer] {comp.manufacturer}\n")
        f.write("\n")

        # [Pin]
        f.write("[Pin]\n")
        f.write("| pin_name  signal_name   model_name\n")
        for p in comp.pList or []:
            f.write(f"{(p.pinName or ''):<10} {(p.signalName or ''):<14} {p.modelName or 'NC'}\n")
        f.write("\n")

        # [Pin Mapping]
        if getattr(comp, "pmList", None):
            f.write("[Pin Mapping]\n")
            for mapping in comp.pmList:
                f.write(" ".join(mapping) + "\n")
            f.write("\n")

        # [Diff Pin]
        if getattr(comp, "dpList", None):
            f.write("[Diff Pin]\n")
            f.write("| inv_pin  vdiff(typ/min/max)               tdelay(typ/min/max)\n")
            for dp in comp.dpList:
                f.write(
                    f"{(dp.invPin or ''):<9} "
                    f"{self.format_typ_min_max(dp.vdiff)}  "
                    f"{self.format_typ_min_max(dp.tdelay)}\n"
                )
            f.write("\n")

        # [Series Pin Mapping]
        if getattr(comp, "spList", None):
            f.write("[Series Pin Mapping]\n")
            f.write("| pin_1    pin_2     model_name\n")
            for sp in comp.spList:
                f.write(f"{(sp.pin1 or ''):<9} {(sp.pin2 or ''):<9} {sp.modelName or ''}\n")
            f.write("\n")

        # [Series Switch Groups]
        if getattr(comp, "ssgList", None):
            f.write("[Series Switch Groups]\n")
            for ssg in comp.ssgList:
                f.write(" ".join(ssg.pins or []) + "\n")
            f.write("\n")

    def write_model(self, model: IbisModel, f) -> None:
        """[Model] block + model-level tables."""
        name = model.modelName or "UNNAMED"
        f.write(f"[Model] {name}\n")
        f.write(f"Model_type {self.map_model_type(model.modelType)}\n")
        if getattr(model, "polarity", None):
            f.write(f"Polarity {model.polarity}\n")
        if getattr(model, "enable", None):
            f.write(f"Enable {model.enable}\n")
        if hasattr(model, "vil") and hasattr(model, "vih"):
            if model.vil and not self.is_na(model.vil.typ):
                f.write(f"VIL {self.n(model.vil.typ)}\n")
            if model.vih and not self.is_na(model.vih.typ):
                f.write(f"VIH {self.n(model.vih.typ)}\n")
        if hasattr(model, "c_comp") and not self.is_na_tmm(model.c_comp):
            f.write(f"C_comp {self.format_typ_min_max(model.c_comp)}\n")
        if getattr(model, "seriesModel", None):
            sm = model.seriesModel
            if sm.OnState:
                f.write("On\n")
            if sm.OffState:
                f.write("Off\n")
                if getattr(sm, "RSeriesOff", None):
                    f.write(f"R Series {self.format_typ_min_max(sm.RSeriesOff)}\n")
            if getattr(sm, "vdslist", None):
                f.write("Series MOSFET\n")
                for vds in sm.vdslist:
                    f.write(f"Vds {self.n(vds)}\n")
        # Use sorted tables
        self.write_vi_table(f, "Pullup", getattr(model, "pullup", None))
        self.write_vi_table(f, "Pulldown", getattr(model, "pulldown", None))
        self.write_vi_table(f, "POWER_CLAMP", getattr(model, "power_clamp", None))
        self.write_vi_table(f, "GND_CLAMP", getattr(model, "gnd_clamp", None))
        # Add series VI tables
        for idx, vi_table in enumerate(getattr(model, "seriesVITables", []) or []):
            self.write_vi_table(f, f"Series Current {idx}", vi_table)
        if hasattr(model, "ramp") and model.ramp:
            r = model.ramp
            vr_typ = self.safe_ratio(r.dv_r.typ, r.dt_r.typ)
            vr_min = self.safe_ratio(r.dv_r.min, r.dt_r.min)
            vr_max = self.safe_ratio(r.dv_r.max, r.dt_r.max)
            vf_typ = self.safe_ratio(r.dv_f.typ, r.dt_f.typ)
            vf_min = self.safe_ratio(r.dv_f.min, r.dt_f.min)
            vf_max = self.safe_ratio(r.dv_f.max, r.dt_f.max)
            f.write("Ramp dV/dt_r dV/dt_f\n")
            f.write(f"{vr_typ} {vr_min} {vr_max}  {vf_typ} {vf_min} {vf_max}\n")
        self.write_wave_block(f, "Rising Waveform", getattr(model, "risingWaveList", None))
        self.write_wave_block(f, "Falling Waveform", getattr(model, "fallingWaveList", None))
        f.write("\n")

    # -----------------------
    # Helpers
    # -----------------------
    def write_vi_table(self, f, title: str, table) -> None:
        """Emit a VI table block when present."""
        if not table or not getattr(table, "VIs", None):
            return
        f.write(f"[{title}]\n")
        f.write("| V        I_typ          I_min          I_max\n")
        for row in table.VIs:
            v = self.n(row.v)
            i_typ = self.n(getattr(row.i, "typ", float("nan")))
            i_min = self.n(getattr(row.i, "min", float("nan")))
            i_max = self.n(getattr(row.i, "max", float("nan")))
            f.write(f"{v:<10} {i_typ:<14} {i_min:<14} {i_max}\n")
        f.write("\n")

    def write_wave_block(self, f, title: str, waves: Optional[List[IbisWaveTable]]) -> None:
        """Emit waveform header + time/V table in IBIS format."""
        if not waves:
            return
        for w in waves:
            # Header on the same line as keyword (spec requirement)
            header = [self.n(w.R_fixture), self.n(w.V_fixture)]
            opt = [
                self.n(getattr(w, "V_fixture_min", CS.USE_NA)),
                self.n(getattr(w, "V_fixture_max", CS.USE_NA)),
                self.n(getattr(w, "L_fixture", CS.USE_NA)),
                self.n(getattr(w, "C_fixture", CS.USE_NA)),
                self.n(getattr(w, "R_dut", CS.USE_NA)),
                self.n(getattr(w, "L_dut", CS.USE_NA)),
                self.n(getattr(w, "C_dut", CS.USE_NA)),
            ]
            # Trim trailing NA
            while opt and opt[-1] == "NA":
                opt.pop()
            f.write(f"[{title}] {' '.join(header + opt)}\n")
            f.write("| time     V_typ          V_min          V_max\n")
            for e in (w.waveData or []):
                t = self.n(getattr(e, "t", float("nan")))
                v_typ = self.n(getattr(e.v, "typ", float("nan")))
                v_min = self.n(getattr(e.v, "min", float("nan")))
                v_max = self.n(getattr(e.v, "max", float("nan")))
                f.write(f"{t:<10} {v_typ:<14} {v_min:<14} {v_max}\n")
            f.write("\n")

    def map_model_type(self, mt) -> str:
        """Map internal enum/int/string to IBIS Model_type."""
        # If already a readable string (e.g., "Output"), keep it.
        if isinstance(mt, str) and not mt.isdigit():
            return mt

        try:
            val = int(mt)
        except (TypeError, ValueError):
            return "Output"

        return {
            CS.ModelType.INPUT: "Input",
            CS.ModelType.OUTPUT: "Output",
            CS.ModelType.IO: "I/O",
            CS.ModelType.SERIES: "Series",
            CS.ModelType.SERIES_SWITCH: "Series_switch",
            CS.ModelType.TERMINATOR: "Terminator",
            CS.ModelType.IO_OPEN_DRAIN: "I/O_Open_drain",
            CS.ModelType.IO_OPEN_SINK: "I/O_Open_sink",
            CS.ModelType.OPEN_DRAIN: "Open_drain",
            CS.ModelType.OPEN_SINK: "Open_sink",
            CS.ModelType.OPEN_SOURCE: "Open_source",
            CS.ModelType.IO_OPEN_SOURCE: "I/O_Open_source",
            CS.ModelType.OUTPUT_ECL: "Output_ECL",
            CS.ModelType.IO_ECL: "I/O_ECL",
        }.get(val, "Output")

    # Number formatting helpers
    def n(self, x) -> str:
        if self.is_na(x):
            return "NA"
        return f"{float(x):.10g}"

    def is_na(self, x) -> bool:
        return (
            x is None
            or (isinstance(x, float) and (math.isnan(x) or x == CS.USE_NA))
            or x == CS.USE_NA
        )

    def is_na_tmm(self, tmm: Optional[IbisTypMinMax]) -> bool:
        if tmm is None:
            return True
        return self.is_na(tmm.typ) and self.is_na(tmm.min) and self.is_na(tmm.max)

    def format_typ_min_max(self, tmm: Optional[IbisTypMinMax]) -> str:
        if tmm is None:
            return "NA NA NA"
        typ = "NA" if self.is_na(tmm.typ) else f"{tmm.typ:.10g}"
        min_val = "NA" if self.is_na(tmm.min) else f"{tmm.min:.10g}"
        max_val = "NA" if self.is_na(tmm.max) else f"{tmm.max:.10g}"
        return f"{typ} {min_val} {max_val}"

    def safe_ratio(self, dv, dt) -> str:
        if self.is_na(dv) or self.is_na(dt) or not dt:
            return "NA"
        try:
            return f"{(dv/dt):.10g}"
        except Exception:
            return "NA"


# -----------------------
# CLI
# -----------------------
if __name__ == "__main__":
    from parser import S2IParser  # your parser module
    # optional: from s2iutil import S2IUtil

    PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

    if len(sys.argv) < 2:
        print("Usage: python s2ioutput.py <input_s2i_file>")
        sys.exit(1)

    input_file = os.path.abspath(sys.argv[1])

    parser = S2IParser()
    try:
        ibis, global_, mList = parser.parse(input_file)
    except FileNotFoundError:
        logging.error(f"Input file {input_file} not found")
        sys.exit(1)

    # If you have a post-pass to link pins->models etc., call it here.
    # util = S2IUtil(mList)
    # util.complete_data_structures(ibis, global_)

    out_dir = os.path.join(PROJECT_ROOT, "tests")
    os.makedirs(out_dir, exist_ok=True)
    output_file = os.path.join(out_dir, os.path.splitext(os.path.basename(input_file))[0] + ".ibs")

    writer = S2IOutput()
    writer.write_ibis_file(ibis, global_, mList, output_file)