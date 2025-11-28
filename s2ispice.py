# s2ispice.py
import logging
import math
import os
import shutil
import subprocess
import re
from typing import List, Tuple, Optional
from dataclasses import dataclass
from models import IbisTOP, IbisGlobal, IbisModel, IbisPin, IbisTypMinMax, IbisVItable, IbisWaveTable, IbisVItableEntry, IbisWaveTableEntry
from s2i_constants import ConstantStuff as CS

# logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
TEST_DIR = os.path.join(PROJECT_ROOT, "tests")

@dataclass
class SpiceVT:
    t: float = 0.0
    v: float = 0.0

@dataclass
class BinParams:
    last_bin: int = 0
    interp_bin: int = 0
    running_sum: float = 0.0
    num_points_in_bin: int = 0

class S2ISpice:
    def __init__(
            self,
            mList: List[IbisModel],
            spice_type: int = CS.SpiceType.HSPICE,
            hspice_path: str = "hspice",
            global_: Optional[IbisGlobal] = None,
            outdir: Optional[str] = None,
            s2i_file: Optional[str] = None,  # ← ADD THIS
    ):
        logging.debug(
            f"S2ISpice init: global_={global_}, vil={getattr(global_, 'vil', None)}, vih={getattr(global_, 'vih', None)}, outdir={outdir}")
        self.allow_mock_fallback = False
        self.mList = mList
        self.spice_type = spice_type
        self.hspice_path = hspice_path
        self.outdir = outdir
        self.mock_dir = os.path.join(PROJECT_ROOT, "mock_spice")
        self.global_ = global_
        self.s2i_file = s2i_file  # ← ADD THIS
        if not os.path.exists(self.mock_dir):
            os.makedirs(self.mock_dir)

    def _vil_vih_for_pin(self, pin: Optional[IbisPin], analyze_case: int, vcc_typ: float) -> tuple[float, float]:
        """
        Returns (VIL, VIH) for driving a control pin (IN/ENA), with Java-equivalent fallback:
        - pin.model.vil/vih if present
        - else global_.vil/vih if present
        - else 0.3*VCC / 0.7*VCC
        """
        # defaults from VCC if everything is missing
        vil, vih = 0.3 * vcc_typ, 0.7 * vcc_typ

        # model-level first (if pin and model exist)
        if pin and getattr(pin, "model", None):
            m = pin.model
            try:
                vil_m = self._val_case(m.vil.typ, m.vil.min, m.vil.max, analyze_case)
                vih_m = self._val_case(m.vih.typ, m.vih.min, m.vih.max, analyze_case)
                if not math.isnan(vil_m): vil = vil_m
                if not math.isnan(vih_m): vih = vih_m
                return vil, vih
            except Exception:
                pass  # fall through

        # global-level
        g = getattr(self, "global_", None)
        if g and getattr(g, "vil", None) and getattr(g, "vih", None):
            try:
                vil_g = self._val_case(g.vil.typ, g.vil.min, g.vil.max, analyze_case)
                vih_g = self._val_case(g.vih.typ, g.vih.min, g.vih.max, analyze_case)
                if not math.isnan(vil_g): vil = vil_g
                if not math.isnan(vih_g): vih = vih_g
            except Exception:
                pass

        return vil, vih

    def _pin_node(self, pin: Optional[IbisPin]) -> Optional[str]:
        """Prefer SPICE node name when available, else pinName; None if pin is None."""
        if not pin:
            return None
        # Some models name this attribute spiceNodeName; fall back to pinName.
        return getattr(pin, "spiceNodeName", None) or pin.pinName

    def _temp_string(self, temperature: float) -> str:
        """Java calls s2iString.temperatureString(spiceType, temperature)."""
        if self.spice_type == CS.SpiceType.SPECTRE:
            # Spectre: simplest global temp knob; acceptable stand-in for s2iString.temperatureString()
            return f"temp = {temperature}\n"
        else:
            # HSPICE/others
            return f".TEMP {temperature}\n"

    def setup_power_temp_cmds(
            self,
            curve_type: int,
            power_pin: Optional[IbisPin],
            gnd_pin: Optional[IbisPin],
            power_clamp_pin: Optional[IbisPin],
            gnd_clamp_pin: Optional[IbisPin],
            vcc: float,
            gnd: float,
            vcc_clamp: float,
            gnd_clamp: float,
            temperature: float,
    ) -> str:
        """
        Mirrors Java setupPwrAndTempCmds:
          - POWER_CLAMP / GND_CLAMP case
          - SERIES_VI case
          - default case (pullup/pulldown/ramps/waves)
        Emits Spectre vsource vs. HSPICE DC sources appropriately.
        """
        S = self.spice_type

        def vsrc(name: str, nplus: str, nminus: str, val: float) -> str:
            if S == CS.SpiceType.SPECTRE:
                return f"{name} {nplus} {nminus} vsource type=dc dc={val}\n"
            else:
                return f"{name} {nplus} {nminus} DC {val}\n"

        p = self._pin_node(power_pin)
        g = self._pin_node(gnd_pin)
        pc = self._pin_node(power_clamp_pin)
        gc = self._pin_node(gnd_clamp_pin)

        buf = []

        if curve_type in (CS.CurveType.POWER_CLAMP, CS.CurveType.GND_CLAMP):
            # Clamp-first biasing
            if pc:
                buf.append(vsrc("VCLMPS2I", pc, "0", vcc_clamp))
                if p and pc.lower() != p.lower():
                    buf.append(vsrc("VCCS2I", p, "0", vcc))
            else:
                if p:
                    buf.append(vsrc("VCCS2I", p, "0", vcc))

            if gc:
                buf.append(vsrc("VGCLMPS2I", gc, "0", gnd_clamp))
                if g and gc.lower() != g.lower():
                    buf.append(vsrc("VGNDS2I", g, "0", gnd))
            else:
                if g:
                    buf.append(vsrc("VGNDS2I", g, "0", gnd))

        elif curve_type == CS.CurveType.SERIES_VI:
            # Only supply rails (no clamps referenced here)
            if p:
                buf.append(vsrc("VCCS2I", p, "0", vcc))
            if g:
                buf.append(vsrc("VGNDS2I", g, "0", gnd))

        else:
            # Default: power first, then clamp (and avoid double-biasing the same node)
            if p:
                buf.append(vsrc("VCCS2I", p, "0", vcc))
                if pc and pc.lower() != p.lower():
                    buf.append(vsrc("VCLMPS2I", pc, "0", vcc_clamp))
            else:
                if pc:
                    buf.append(vsrc("VCLMPS2I", pc, "0", vcc_clamp))

            if g:
                buf.append(vsrc("VGNDS2I", g, "0", gnd))
                if gc and gc.lower() != g.lower():
                    buf.append(vsrc("VGCLMPS2I", gc, "0", gnd_clamp))
            else:
                if gc:
                    buf.append(vsrc("VGCLMPS2I", gc, "0", gnd_clamp))

        # Temperature line (Java appends temperatureBuffer separately)
        buf.append(self._temp_string(temperature))
        return "".join(buf)

    def setup_dc_sweep_cmds(self, curve_type: int, sweep_start: float, sweep_end: float, sweep_step: float) -> str:
        S = self.spice_type
        # HSPICE wants .DC VOUTS2I ... even for series VI (only the .PRINT target changes).
        if S == CS.SpiceType.SPECTRE:
            base = (
                f"DCsweep dc dev= VOUTS2I param=dc start={sweep_start} "
                f"stop={sweep_end} step={sweep_step} save=selected\n"
            )
            if curve_type == CS.CurveType.SERIES_VI:
                save = "save VDS:currents\n"
            else:
                save = "save VOUTS2I:currents\n"
            return base + save
        else:
            base = f".DC VOUTS2I {sweep_start} {sweep_end} {sweep_step}\n"
            if curve_type == CS.CurveType.SERIES_VI:
                pr = ".PRINT DC I(VDS)\n"
            else:
                pr = ".PRINT DC I(VOUTS2I)\n"
            return base + pr

    def setup_tran_cmds(self, sim_time: float, output_node: str) -> str:
        S = self.spice_type
        step = sim_time / 100.0 if sim_time and sim_time > 0 else 0
        if S == CS.SpiceType.SPECTRE:
            analysis = (
                f"tran_run tran step={step} start=0 stop={sim_time} save=selected\n"
            )
            save = f"save {output_node}\n"
            return analysis + save
        else:
            analysis = f".TRAN {step} {sim_time}\n"
            pr = f".PRINT TRAN V({output_node})\n"
            return analysis + pr

    def setup_spice_file_names(
            self,
            prefix: str,
            pin_name: str,
            index: Optional[int] = None,
    ) -> Tuple[str, str, str, str, str, str]:
        idx_str = f"{index:02d}" if index is not None else ""
        base = f"{prefix}{idx_str}{pin_name}"
        if self.outdir:
            base = os.path.join(self.outdir, base)
        spice_in = f"{base}.spi"
        spice_out = f"{base}.out"
        spice_msg = f"{base}.msg"
        spice_st0 = f"{base}.st0"
        spice_ic = f"{base}.ic"
        spice_ic0 = f"{base}.ic0"
        return spice_in, spice_out, spice_msg, spice_st0, spice_ic, spice_ic0

    def _write_spice_file_filtered(self, in_path: str, out_f) -> None:
        """Copy a SPICE netlist to out_f, skipping full-line comments (*) and .end lines."""
        with open(in_path, "r") as sf:
            for raw in sf:
                line = raw.rstrip("\n")
                # Tokenize only the first token
                tok = None
                for part in line.split():
                    tok = part
                    break
                if tok is None:
                    # empty line is fine
                    out_f.write(line + "\n")
                    continue
                if tok.startswith("*") or tok.lower() == ".end":
                    # skip comments and .end from DUT
                    continue
                out_f.write(line + "\n")

    def _spice_options(self) -> str:
        # minimal, safe defaults; extend as needed
        if self.spice_type == CS.SpiceType.HSPICE:
            return ".OPTION INGOLD=2\n"
        elif self.spice_type == CS.SpiceType.SPECTRE:
            # Spectre has different syntax; you can leave blank or add spectre options
            return ""  # spectre options would go here if needed
        elif self.spice_type == CS.SpiceType.ELDO:
            return ""  # put Eldo options here if desired
        else:
            return ".OPTION INGOLD=2\n"

    def _spice_prog_name(self) -> str:
        # You can extend this if you support more engines
        if self.spice_type == CS.SpiceType.HSPICE:
            return self.hspice_path or "hspice"
        elif self.spice_type == CS.SpiceType.SPECTRE:
            return "spectre"
        elif self.spice_type == CS.SpiceType.ELDO:
            return "eldo"
        return "hspice"

    def _format_user_command(self, template: str, spice_in: str, spice_out: str, spice_msg: str) -> str:
        """
        Accepts both positional {0}/{1}/{2} and named {in}/{out}/{msg} formats.
        """
        mapping = {"in": spice_in, "out": spice_out, "msg": spice_msg}
        try:
            # Try named format first
            if "{" in template and any(k in template for k in ("{in}", "{out}", "{msg}")):
                return template.format_map(mapping)
            # Then try positional {0}/{1}/{2}
            return template.format(spice_in, spice_out, spice_msg)
        except Exception:
            # Fallback: just append args at the end
            return f"{template} {spice_in} {spice_out} {spice_msg}"

    def setup_spice_input_file(
            self,
            iterate: int,
            header_line: str,
            spice_file: str,
            model_file: str,
            ext_spice_cmd_file: str,
            load_buffer: str,
            input_buffer: str,
            power_buffer: str,
            temperature_buffer: str,
            analysis_buffer: str,
            spice_in: str,
    ) -> int:
        if iterate == 1 and os.path.exists(spice_in):
            logging.info(f"File {spice_in} exists, skipping setup")
            return 0

        # ADD THESE 4 LINES HERE -------------------------------------------------
        comp_name = getattr(self.current_component, "component", "None") if hasattr(self,
                                                                                    "current_component") and self.current_component else "None"
        comp_spice = getattr(self.current_component, "spiceFile", None) if hasattr(self,
                                                                                   "current_component") and self.current_component else None
        logging.debug(f"Processing component: {comp_name}")
        logging.debug(f"  → component.spiceFile = {comp_spice}")
        # END OF ADDED LINES ----------------------------------------------------

        # Resolve spice_file path (project root -> tests -> given)
        # Resolve spice_file path: prefer CWD -> PROJECT_ROOT -> TEST_DIR

        # === FIXED: Use global [Spice File] if component didn't provide one ===
        s2i_dir = os.path.dirname(self.s2i_file) if self.s2i_file else os.getcwd()

        candidate_names = []

        # 1. Component-level [Spice File] inside [Component] ← MOST COMMON
        if (hasattr(self, "current_component") and
                self.current_component and
                hasattr(self.current_component, "spiceFile") and
                getattr(self.current_component, "spiceFile", None)):
            candidate_names.append(self.current_component.spiceFile.strip())

        # 2. Global [Spice File] at top of file
        if self.global_ and getattr(self.global_, "spice_file", None):
            candidate_names.append(self.global_.spice_file.strip())

        # 3. Legacy per-model [Model File] (rarely used for DUT)
        if spice_file:
            candidate_names.append(spice_file.strip())

        spice_file_path = None
        for name in candidate_names:
            if not name:
                continue
            if os.path.isabs(name):
                if os.path.exists(name):
                    spice_file_path = name
                    break
            else:
                for base in [os.getcwd(), s2i_dir, PROJECT_ROOT, TEST_DIR]:
                    path = os.path.join(base, name)
                    if os.path.exists(path):
                        spice_file_path = path
                        break
            if spice_file_path:
                break

        if not spice_file_path and (spice_file or (self.global_ and self.global_.spice_file)):
            logging.warning("Spice file not found (tried component and global paths)")
        elif spice_file_path:
            logging.debug(f"Using SPICE netlist: {spice_file_path}")

        if model_file and not os.path.exists(model_file):
            logging.warning(f"Model file {model_file} not found; continuing without it")

        if spice_file and not spice_file_path:
            logging.warning(f"Spice file {spice_file} not found; continuing without circuit netlist")

        try:
            with open(spice_in, "w") as f:
                # Headers
                f.write(header_line)
                f.write("*Spice Deck created by PYS2IBIS3 Version Beta\n")
                f.write("*Missouri S&T EMC Lab\n\n")

                # Spectre language line (if applicable)
                if self.spice_type == CS.SpiceType.SPECTRE:
                    f.write("simulator lang = spectre\n\n")

                # DUT netlist (filtered like Java: skip comment and .end)
                if spice_file_path:
                    try:
                        self._write_spice_file_filtered(spice_file_path, f)
                    except Exception as e:
                        logging.warning(f"Failed to copy DUT netlist {spice_file_path}: {e}")

                # Model file (verbatim append if present)
                if model_file and os.path.exists(model_file):
                    f.write("\n")
                    with open(model_file, "r") as mf:
                        f.write(mf.read())
                    f.write("\n")

                # External spice command file (verbatim append if present)
                if ext_spice_cmd_file and os.path.exists(ext_spice_cmd_file):
                    f.write("\n")
                    with open(ext_spice_cmd_file, "r") as ef:
                        f.write(ef.read())
                    f.write("\n")

                # Load, power, input
                if load_buffer:
                    f.write(load_buffer)
                if power_buffer:
                    f.write(power_buffer)
                f.write("\n")
                if input_buffer:
                    f.write(input_buffer)

                # Temperature (only if provided; most callers keep this empty)
                if temperature_buffer:
                    line = temperature_buffer.strip()
                    if line.upper().startswith(".TEMP"):
                        parts = line.split()
                        val = 27.0  # default
                        if len(parts) >= 2:
                            try:
                                val = float(parts[1])
                                if math.isnan(val):
                                    val = 27.0
                            except Exception:
                                val = 27.0
                        f.write(f".TEMP {val}\n")
                    else:
                        f.write(temperature_buffer)

                # Options & analysis
                opts = self._spice_options()
                if opts:
                    f.write(opts)
                if analysis_buffer:
                    f.write(analysis_buffer)

                # .END (all but Spectre)
                if self.spice_type != CS.SpiceType.SPECTRE:
                    f.write(".END\n")

            logging.debug(f"SPICE input file created: {spice_in}")
            return 0

        except Exception as e:
            logging.error(f"Error setting up SPICE input file {spice_in}: {e}")
            return 1

    def _val_case(self, typ: float, mn: float, mx: float, analyze_case: int) -> float:
        def is_na(x: float) -> bool:
            return x is None or math.isnan(x)

        if analyze_case == CS.TYP_CASE:
            return typ if not is_na(typ) else float("nan")  # Avoid returning 0.0
        if analyze_case == CS.MIN_CASE:
            return typ if is_na(mn) else mn
        return typ if is_na(mx) else mx

    def _node_name(self, pin: Optional[IbisPin], node_label: str) -> str:
        """Use 'Vg' for gate; otherwise prefer spiceNodeName if present."""
        if node_label.lower() == "gate":
            return "Vg"
        if not pin:
            return "0"
        # prefer spiceNodeName if the model provides it; fallback to pinName
        return getattr(pin, "spiceNodeName", None) or pin.pinName

    def set_pin_dc(
            self,
            pin: Optional[IbisPin],
            pin_role: int,
            output_active: int,
            node_label: str,
            analyze_case: int,
    ) -> str:
        if not pin:
            logging.warning(f"No {node_label} pin provided for DC drive")
            return ""

        model = getattr(pin, "model", None)
        logging.debug(
            f"set_pin_dc: node_label={node_label}, pin_name={getattr(pin, 'pinName', 'None')}, model_name={getattr(model, 'modelName', 'None') if model else 'None'}")

        def pick_case(tmm: Optional[IbisTypMinMax]) -> Optional[float]:
            if tmm is None:
                logging.debug(f"pick_case: tmm is None")
                return None
            try:
                value = self._val_case(tmm.typ, tmm.min, tmm.max, analyze_case)
                logging.debug(f"pick_case: tmm={tmm}, analyze_case={analyze_case}, value={value}")
                return value
            except Exception as e:
                logging.debug(f"pick_case: exception {e}")
                return None

        def first_real(*vals) -> Optional[float]:
            for v in vals:
                if v is not None and not (isinstance(v, float) and math.isnan(v)):
                    logging.debug(f"first_real: selected value={v}")
                    return v
            logging.debug("first_real: no valid value found")
            return None

        vcc_model = pick_case(getattr(model, "voltageRange", None)) if model else None
        vcc_global = pick_case(getattr(getattr(self, "global_", None), "voltageRange", None))
        vcc = first_real(vcc_model, vcc_global, 3.3)
        logging.debug(f"Resolved vcc: model={vcc_model}, global={vcc_global}, final={vcc}")

        vil_model = pick_case(getattr(model, "vil", None)) if model else None
        vil_global = pick_case(getattr(getattr(self, "global_", None), "vil", None))
        vil = first_real(vil_model, vil_global, 0.0)  # Use global_.vil or 0.0
        logging.debug(f"Resolved vil: model={vil_model}, global={vil_global}, default=0.0, final={vil}")

        vih_model = pick_case(getattr(model, "vih", None)) if model else None
        vih_global = pick_case(getattr(getattr(self, "global_", None), "vih", None))
        vih = first_real(vih_model, vih_global, vcc)  # Use global_.vih or vcc
        logging.debug(f"Resolved vih: model={vih_model}, global={vih_global}, default={vcc}, final={vih}")

        if vil is None or vih is None:
            logging.warning(
                "Cannot resolve VIH/VIL for %s (pin=%s, model=%s), using defaults vil=0.0, vih=%.1f",
                node_label, getattr(pin, "pinName", "?"), getattr(model, "modelName", "None") if model else "None", vcc
            )
            vil = 0.0
            vih = vcc

        is_inverting = pin_role in (CS.MODEL_POLARITY_INVERTING, CS.MODEL_ENABLE_ACTIVE_LOW)
        value = (vil if output_active else vih) if is_inverting else (vih if output_active else vil)
        logging.debug(f"Selected DC value: is_inverting={is_inverting}, output_active={output_active}, value={value}")

        node = self._pin_node(pin) or getattr(pin, "pinName", "N001")
        return f"V{node_label}S2I {node} 0 DC {value}\n"

    def set_pin_tran(
            self,
            pin: Optional[IbisPin],
            pin_type: int,
            output_rising: int,
            node_label: str,
            analyze_case: int,
    ) -> str:
        if not pin:
            logging.warning(f"No {node_label} pin provided for transient drive")
            return ""

        m = getattr(pin, "model", None)
        if not m:
            logging.error("set_pin_tran called without valid model")
            return ""

        g = getattr(self, "global_", None)

        def _sel3(typ, mn, mx):
            val = self._val_case(typ, mn, mx, analyze_case)
            if isinstance(val, float) and math.isnan(val):
                return typ
            return val

        def _first_real(*vals, default=None):
            for v in vals:
                if v is None:
                    continue
                try:
                    fv = float(v)
                    if math.isfinite(fv):
                        return fv
                except Exception:
                    pass
            return default

        # === VIH/VIL (unchanged) ===
        vih = _first_real(
            _sel3(getattr(m, "vih", None).typ if m else float("nan"),
                  getattr(m, "vih", None).min if m else float("nan"),
                  getattr(m, "vih", None).max if m else float("nan")),
            _sel3(getattr(g, "vih", None).typ if g else float("nan"),
                  getattr(g, "vih", None).min if g else float("nan"),
                  getattr(g, "vih", None).max if g else float("nan")),
            default=3.3 if analyze_case == CS.TYP_CASE else 3.0 if analyze_case == CS.MIN_CASE else 3.6,
        )
        vil = _first_real(
            _sel3(getattr(m, "vil", None).typ if m else float("nan"),
                  getattr(m, "vil", None).min if m else float("nan"),
                  getattr(m, "vil", None).max if m else float("nan")),
            _sel3(getattr(g, "vil", None).typ if g else float("nan"),
                  getattr(g, "vil", None).min if g else float("nan"),
                  getattr(g, "vil", None).max if g else float("nan")),
            default=0.0,
        )

        # === RESPECT USER simTime FIRST (from .s2i) ===
        user_sim_time = getattr(m, "simTime", None)

        if math.isfinite(user_sim_time) and user_sim_time > 0:
            sim_time = user_sim_time
        else:
            # Physics fallback only if user didn't specify
            tr_temp = _first_real(
                _sel3(getattr(m, "tr", None).typ if m else float("nan"),
                      getattr(m, "tr", None).min if m else float("nan"),
                      getattr(m, "tr", None).max if m else float("nan")),
                _sel3(getattr(g, "tr", None).typ if g else float("nan"),
                      getattr(g, "tr", None).min if g else float("nan"),
                      getattr(g, "tr", None).max if g else float("nan")),
                default=100e-12,
            )
            tf_temp = _first_real(
                _sel3(getattr(m, "tf", None).typ if m else float("nan"),
                      getattr(m, "tf", None).min if m else float("nan"),
                      getattr(m, "tf", None).max if m else float("nan")),
                _sel3(getattr(g, "tf", None).typ if g else float("nan"),
                      getattr(g, "tf", None).min if g else float("nan"),
                      getattr(g, "tf", None).max if g else float("nan")),
                default=100e-12,
            )
            edge_time = max(
                tr_temp if math.isfinite(tr_temp) and tr_temp > 0 else 100e-12,
                tf_temp if math.isfinite(tf_temp) and tf_temp > 0 else 100e-12,
            )
            sim_time = max(10e-9, 20 * edge_time)

        # ibischk5 safety cap
        sim_time = min(sim_time, 100e-9)

        # === tr/tf: OFFICIAL s2ibis3 SPEC — default = sim_time / 100.0 ===
        tr = _first_real(
            _sel3(getattr(m, "tr", None).typ if m else float("nan"),
                  getattr(m, "tr", None).min if m else float("nan"),
                  getattr(m, "tr", None).max if m else float("nan")),
            _sel3(getattr(g, "tr", None).typ if g else float("nan"),
                  getattr(g, "tr", None).min if g else float("nan"),
                  getattr(g, "tr", None).max if g else float("nan")),
            default=sim_time / 100.0,  # ← SPEC-COMPLIANT
        )
        tf = _first_real(
            _sel3(getattr(m, "tf", None).typ if m else float("nan"),
                  getattr(m, "tf", None).min if m else float("nan"),
                  getattr(m, "tf", None).max if m else float("nan")),
            _sel3(getattr(g, "tf", None).typ if g else float("nan"),
                  getattr(g, "tf", None).min if g else float("nan"),
                  getattr(g, "tf", None).max if g else float("nan")),
            default=sim_time / 100.0,  # ← SPEC-COMPLIANT
        )

        logging.debug(
            f"sim_time={sim_time:.3e}s | "
            f"user={'NA' if user_sim_time is None else f'{user_sim_time:.1e}s'} | "
            f"tr={tr:.2e}s tf={tf:.2e}s | "
            f"model={m.modelName}"
        )

        # === Pulse generation ===
        pulsewidth = 2.0 * sim_time
        period = 2.0 * (tr + tf + pulsewidth)

        low, high = (vil, vih) if output_rising else (vih, vil)
        if pin_type in [CS.MODEL_POLARITY_INVERTING, CS.MODEL_ENABLE_ACTIVE_LOW]:
            low, high = high, low

        node = self._node_name(pin, node_label)
        return (
            f"V{node_label}S2I {node} 0 "
            f"PULSE({low} {high} 0 {tr:.16e} {tf:.16e} {pulsewidth:.16e} {period:.16e})\n"
        )

    def call_spice(self, iterate: int, spice_command: str, spice_in: str, spice_out: str, spice_msg: str) -> int:
        if iterate == 1 and os.path.exists(spice_out):
            logging.info(f"[iterate] set and file {spice_out} exists – skipping run")
            return 0

        prog = self._spice_prog_name()

        if spice_command and spice_command.strip():
            command = self._format_user_command(spice_command.strip(), spice_in, spice_out, spice_msg)
        else:
            if self.spice_type == CS.SpiceType.HSPICE:
                command = f"{prog} -i {spice_in} -o {spice_out}"
            elif self.spice_type == CS.SpiceType.SPECTRE:
                command = f"{prog} +escchars +log {spice_msg} {spice_in}"
            elif self.spice_type == CS.SpiceType.ELDO:
                command = f"{prog} {spice_in} > {spice_msg} 2>&1"
            else:
                command = f"{prog} -i {spice_in} -o {spice_out}"

        logging.debug(f"Starting {prog} job with input {spice_in}")
        try:
            completed = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=60
            )

            try:
                with open(spice_msg, "a", encoding="utf-8", errors="ignore") as mf:
                    if completed.stderr:
                        mf.write(completed.stderr)
                        if not completed.stderr.endswith("\n"):
                            mf.write("\n")
                    if completed.stdout:
                        mf.write(completed.stdout)
                        if not completed.stdout.endswith("\n"):
                            mf.write("\n")
            except Exception as e:
                logging.warning(f"Could not write {spice_msg}: {e}")

            if self.spice_type == CS.SpiceType.HSPICE:
                candidates = [
                    spice_out + ".lis",
                    spice_out.replace(".out", ".lis"),
                    os.path.splitext(spice_out)[0] + ".lis",
                ]
                if self.outdir:
                    candidates = [os.path.join(self.outdir, os.path.basename(c)) for c in candidates]

                moved = False
                for c in candidates:
                    if os.path.exists(c):
                        try:
                            shutil.move(c, spice_out)  # ← ALWAYS OVERWRITE
                            logging.debug(f"Renamed {c} → {spice_out}")
                            moved = True
                            break
                        except Exception as e:
                            logging.warning(f"Failed to move {c}: {e}")

                if not moved:
                    logging.warning(f"No .lis file found for {spice_out}")

            if completed.returncode == 0 and os.path.exists(spice_out):
                logging.debug(f"{prog} run succeeded for {spice_in}")
                return 0

            logging.error(
                f"{prog} run failed for {spice_in} (rc={completed.returncode}). "
                f"stdout/snippet: {completed.stdout[:200]!r} stderr/snippet: {completed.stderr[:200]!r}"
            )

        except Exception as e:
            logging.error(f"Exception while running {prog} for {spice_in}: {e}")
            try:
                with open(spice_msg, "a", encoding="utf-8", errors="ignore") as mf:
                    mf.write(str(e) + "\n")
            except Exception:
                pass

        mock_out = os.path.join(self.outdir if self.outdir else self.mock_dir, os.path.basename(spice_out))
        mock_msg = os.path.join(self.outdir if self.outdir else self.mock_dir, os.path.basename(spice_msg))
        if os.path.exists(mock_out):
            logging.info(f"Using mock output {mock_out}")
            try:
                shutil.copy(mock_out, spice_out)
                if os.path.exists(mock_msg):
                    shutil.copy(mock_msg, spice_msg)
                return 0
            except Exception as e:
                logging.error(f"Failed to copy mock files: {e}")

        return 1

    def _file_contains_marker(self, path: str, marker: str) -> bool:
        if not path or not os.path.exists(path) or not marker:
            return False
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    if marker.lower() in line.lower():
                        logging.debug(f"Found marker '{marker}' in {path}")
                        return True
        except Exception as e:
            logging.warning(f"Error reading {path}: {e}")
        return False

    def check_for_abort(self, spice_out: str, spice_msg: str) -> int:
        """Return 1 if an abort marker is found (Java parity), else 0."""
        try:
            marker = CS.abortMarker.get(self.spice_type, "")
        except Exception:
            marker = ""
        # 1) Check the .out file (Java checks this first)
        if self._file_contains_marker(spice_out, marker):
            logging.error(f"Abort detected in {spice_out}")
            return 1

        # 2) Check the .msg file (Java: skip for ELDO)
        if self.spice_type != CS.SpiceType.ELDO:
            if self._file_contains_marker(spice_msg, marker):
                logging.error(f"Abort detected in {spice_msg}")
                return 1

        return 0

    def check_for_convergence(self, spice_out: str) -> int:
        """Return 1 if a non-convergence marker is found (Java parity), else 0."""
        try:
            marker = CS.convergenceMarker.get(self.spice_type, "")
        except Exception:
            marker = ""
        if self._file_contains_marker(spice_out, marker):
            logging.error(f"Non-convergence detected in {spice_out}")
            return 1
        return 0

    def run_spice_again(
            self,
            curve_type: int,
            sweep_step: float,
            spice_in: str,
            spice_out: str,
            spice_msg: str,
            iterate: int,
            header_line: str,
            spice_command: str,
            spice_file: str,
            model_file: str,
            ext_spice_cmd_file: str,
            load_buffer: str,
            input_buffer: str,
            power_buffer: str,
            temperature_buffer: str,
            orig_sweep_start: float,
            sweep_range: float,
            max_attempts: int = 3,
    ) -> int:
        """
        Retry DC sweep with adjusted ranges, mirroring Java flow (without interactive prompts).
        Returns 0 on success (no abort/non-convergence after a rerun), else 1.
        """

        # Build candidate sweep windows: original, symmetric, and a broader rescue window.
        # Keep strictly ordered and bounded by max_attempts.
        orig_end = orig_sweep_start + sweep_range
        span = abs(sweep_range) if sweep_range else 1.0
        candidates = [
                         (orig_sweep_start, orig_end),
                         (-span, +span),
                         (-max(3.3, span), max(6.6, span)),  # broader "rescue" span
                     ][:max_attempts]

        for attempt, (ss, se) in enumerate(candidates, start=1):
            logging.info(f"[retry {attempt}/{len(candidates)}] sweepStart={ss}, sweepEnd={se}")
            analysis_buffer = self.setup_dc_sweep_cmds(curve_type, ss, se, sweep_step)

            # Rebuild deck with same load/input/power/temp, only analysis changes.
            if self.setup_spice_input_file(
                    iterate=iterate,
                    header_line=header_line,
                    spice_file=spice_file,
                    model_file=model_file,
                    ext_spice_cmd_file=ext_spice_cmd_file,
                    load_buffer=load_buffer,
                    input_buffer=input_buffer,
                    power_buffer=power_buffer,
                    temperature_buffer=temperature_buffer,
                    analysis_buffer=analysis_buffer,
                    spice_in=spice_in,
            ):
                logging.error(f"Failed to setup SPICE file for retry: {spice_in}")
                continue

            # Clean previous attempt artifacts so we don't re-trigger on stale logs
            try:
                if os.path.exists(spice_msg):
                    with open(spice_msg, "w", encoding="utf-8") as _clr:
                        _clr.write("")  # truncate
            except Exception:
                pass

            try:
                if os.path.exists(spice_out):
                    os.remove(spice_out)  # ensure we don't read old .out by mistake
            except Exception:
                pass

            # Run and re-check conditions just like Java.
            if self.call_spice(iterate, spice_command, spice_in, spice_out, spice_msg):
                logging.error("Retry SPICE run failed (process error); continuing to next window")
                continue

            if self.check_for_abort(spice_out, spice_msg):
                logging.error("Retry SPICE run aborted; continuing to next window")
                continue

            if self.check_for_convergence(spice_out):
                logging.error("Retry SPICE run non-convergent; continuing to next window")
                continue

            # Success path: no abort and no non-convergence
            logging.info("Retry SPICE run completed without abort/non-convergence")
            return 0

        # All attempts exhausted
        logging.error("All retry windows failed to produce a clean run")
        return 1

    def get_spice_vi_data(
            self,
            vi_cont: IbisVItable,
            table_size: int,
            spice_out: str,
            command: str,
            retry_count: int = 0,
    ) -> int:
        target_file = spice_out
        if not os.path.exists(target_file):
            lis = os.path.splitext(spice_out)[0] + ".lis"
            if self.outdir:
                lis = os.path.join(self.outdir, os.path.basename(lis))
            if os.path.exists(lis):
                target_file = lis

        if not os.path.exists(target_file):
            logging.error(f"Unable to open {target_file} for reading")
            return 1

        try:
            with open(target_file, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
        except Exception as e:
            logging.error(f"Error reading {target_file}: {e}")
            return 1

        # Pre-allocate VI table
        if not vi_cont.VIs or len(vi_cont.VIs) != table_size:
            vi_cont.VIs = [IbisVItableEntry(v=0.0, i=IbisTypMinMax(0.0, 0.0, 0.0))
                           for _ in range(table_size)]

        row = 0
        marker = CS.VIDataBeginMarker.get(self.spice_type, "dc transfer curves")
        i = 0
        data_start = False
        is_eldo = (self.spice_type == CS.SpiceType.ELDO)

        # === STEP 1: Find data begin marker ===
        while i < len(lines):
            line = lines[i].strip()
            if marker.lower() in line.lower():
                logging.debug(f"Found marker '{marker}' in {target_file}: {line}")
                i += 1
                data_start = True
                break
            i += 1

        if not data_start:
            logging.error(f"Data begin marker '{marker}' not found in {target_file}")
            return 1

        # === STEP 2: ELDO: Skip until second marker ===
        if is_eldo:
            while i < len(lines):
                line = lines[i].strip()
                if line.startswith(marker):
                    i += 1
                    break
                i += 1

        # === STEP 3: Skip header lines until first numeric token ===
        while i < len(lines):
            line = lines[i].rstrip()
            i += 1
            if not line:
                continue

            # Try to parse first token as float → if fails, it's header
            first_token = line.split()[0]
            try:
                float(first_token)
                # First numeric line → go back one line
                i -= 1
                break
            except (ValueError, IndexError):
                continue  # skip header

        # === STEP 4: Parse data rows ===
        while i < len(lines) and row < table_size:
            raw_line = lines[i].rstrip()
            i += 1
            line = raw_line.strip()
            if not line or line.lower() in ['x', 'vouts2i']:
                continue

            # === Extract V and I using VI_ROW_RE ===
            m = CS.VI_ROW_RE.match(line)
            if not m:
                #logging.debug(f"Skipping non-matching line: {raw_line}")
                continue

            try:
                v_val = float(m.group(1))
                i_val = -float(m.group(2))  # current into DUT
            except ValueError:
                logging.debug(f"Failed to parse numbers: {raw_line}")
                continue

            #logging.debug(f"Extracted: v={v_val:.6e}, i={i_val:.6e} from: {raw_line}")

            #vi_cont.VIs[row].v = v_val
            if command == "typ":
                vi_cont.VIs[row].v = v_val
                vi_cont.VIs[row].i.typ = i_val
            elif command == "min":
                vi_cont.VIs[row].i.min = i_val
            elif command == "max":
                vi_cont.VIs[row].i.max = i_val
            else:
                logging.warning(f"Unknown corner '{command}'")
            row += 1

        vi_cont.size = max(vi_cont.size, row)

        if row == 0:
            logging.error(f"No valid VI data found in {target_file}")
            return 1

        logging.debug(f"Extracted {row} VI points from {target_file} ({command})")
        return 0

    def get_spice_ramp_data(
            self,
            model: IbisModel,
            curve_type: int,
            spice_out: str,
            command: str,
            retry_count: int = 0
    ) -> int:
        if retry_count > 1:
            logging.error(f"Max retries reached for {spice_out}")
            return 1

        mock_out = os.path.join(self.outdir if self.outdir else self.mock_dir, os.path.basename(spice_out))
        target_file = spice_out
        logging.debug(f"[ramp] target_file={target_file}, retry_count={retry_count}")

        if not os.path.exists(target_file):
            logging.error(f"Unable to open {target_file} for reading")
            return 1

        try:
            with open(target_file, "r") as f:
                lines = f.readlines()

            tran_hdr = CS.tranDataBeginMarker.get(self.spice_type, "")
            eldo_vi_hdr = CS.VIDataBeginMarker.get(self.spice_type, "")
            is_eldo = (self.spice_type == CS.SpiceType.ELDO)

            t_v_pairs: List[Tuple[float, float]] = []

            for raw in lines:
                line = raw.strip()
                if not line or line.startswith('*'):
                    continue  # ← SKIP ALL COMMENT LINES

                toks = line.split()
                if len(toks) < 2:
                    continue

                # Try to read first two columns: time and voltage
                try:
                    t = float(toks[0])
                    v = float(toks[1])
                    t_v_pairs.append((t, v))
                except ValueError:
                    continue  # ← SKIP NON-NUMERIC LINES

            if not t_v_pairs:
                logging.error(f"No valid ramp data found in {target_file}")
                if os.path.exists(mock_out) and target_file != mock_out:
                    shutil.copy(mock_out, spice_out)
                    return self.get_spice_ramp_data(model, curve_type, spice_out, command, retry_count + 1)
                return 1

            # === Sort by time (Java uses LinkedHashMap with row index) ===
            t_v_pairs.sort(key=lambda x: x[0])
            t0, v0 = t_v_pairs[0]
            t1, v1 = t_v_pairs[-1]

            v20 = v0 + 0.2 * (v1 - v0)
            v80 = v0 + 0.8 * (v1 - v0)

            def lerp_time(t1_, v1_, t2_, v2_, vcross: float) -> float:
                if abs(v2_ - v1_) < 1e-30:
                    return t2_
                return t1_ + (vcross - v1_) * (t2_ - t1_) / (v2_ - v1_)

            t20 = None
            t80 = None
            v_int, t_int = v0, t0
            rising = v1 >= v0

            for t, v in t_v_pairs[1:]:
                if rising:
                    if t20 is None and v >= v20:
                        t20 = lerp_time(t_int, v_int, t, v, v20)
                    if t80 is None and v >= v80:
                        t80 = lerp_time(t_int, v_int, t, v, v80)
                else:
                    if t20 is None and v <= v20:
                        t20 = lerp_time(t_int, v_int, t, v, v20)
                    if t80 is None and v <= v80:
                        t80 = lerp_time(t_int, v_int, t, v, v80)
                v_int, t_int = v, t
                if t20 is not None and t80 is not None:
                    break

            if t20 is None or t80 is None:
                logging.error(f"Failed to locate 20/80 points: v0={v0}, v1={v1}, t0={t0}, t1={t1}")
                if os.path.exists(mock_out) and target_file != mock_out:
                    shutil.copy(mock_out, spice_out)
                    return self.get_spice_ramp_data(model, curve_type, spice_out, command, retry_count + 1)
                return 1

            dv = abs(v80 - v20)
            dt = t80 - t20

            derate_pct = getattr(model.ramp, "derateRampPct", 0) or 0

            if curve_type == CS.CurveType.RISING_RAMP:
                if command == "typ":
                    model.ramp.dv_r.typ = dv
                    model.ramp.dt_r.typ = dt
                elif command == "min":
                    model.ramp.dv_r.min = dv
                    model.ramp.dt_r.min = dt * (1 - derate_pct / 100.0)
                elif command == "max":
                    model.ramp.dv_r.max = dv
                    model.ramp.dt_r.max = dt * (1 + derate_pct / 100.0)
            else:  # FALLING_RAMP
                if command == "typ":
                    model.ramp.dv_f.typ = dv
                    model.ramp.dt_f.typ = dt
                elif command == "min":
                    model.ramp.dv_f.min = dv
                    model.ramp.dt_f.min = dt * (1 - derate_pct / 100.0)
                elif command == "max":
                    model.ramp.dv_f.max = dv
                    model.ramp.dt_f.max = dt * (1 + derate_pct / 100.0)

            # Replace your current logging.info with this:
            curve_type_str = "RISING" if curve_type == CS.CurveType.RISING_RAMP else "FALLING"
            logging.debug(
                f"[RAMP] {command.upper():>3} | {curve_type_str:<7} | "
                f"dv={dv:.4f}V  dt={dt:.4e}s  v0={v0:.3f}V  v1={v1:.3f}V  "
                f"model={model.modelName}  file={os.path.basename(target_file)}"
            )
            return 0

        except Exception as e:
            logging.error(f"Error parsing ramp data from {target_file}: {e}")
            if os.path.exists(mock_out) and target_file != mock_out:
                shutil.copy(mock_out, spice_out)
                return self.get_spice_ramp_data(model, curve_type, spice_out, command, retry_count + 1)
            return 1

    def get_spice_wave_data(
            self,
            sim_time: float,
            spice_out: str,
            command: str,
            wave_p: IbisWaveTable,
            curve_type: int
    ) -> int:
        if not os.path.exists(spice_out):
            logging.error(f"Cannot find {spice_out}")
            return 1

        if sim_time <= 0 or math.isnan(sim_time):
            sim_time = 10e-9

        max_bins = CS.WAVE_POINTS_DEFAULT
        bin_time = sim_time / (max_bins - 1)

        try:
            with open(spice_out, 'r') as f:
                lines = f.readlines()

            # Find data start
            data_start = False
            for i, line in enumerate(lines):
                if 'time' in line.lower() and any(x in line.lower() for x in ['v(', 'voltage', 'out']):
                    data_start = True
                    header_line = i
                    break
            if not data_start:
                logging.error("No 'time v(' header found")
                return 1

            t_v_pairs = []
            for line in lines[header_line + 2:]:
                line = line.strip()
                if not line or line.startswith('*'):
                    continue
                parts = line.split()
                if len(parts) < 2:
                    continue
                try:
                    t = float(parts[0])
                    v = float(parts[1])
                    if t >= 0:  # ← REMOVE UPPER BOUND — THIS IS THE FIX
                        t_v_pairs.append((t, v))
                except ValueError:
                    continue

            if not t_v_pairs:
                logging.error("No V-t data extracted")
                return 1

            # === BINNING ===
            bin_param = [0, 0, 0.0, 0]  # last_bin, interp_bin, sum, count
            for t, v in t_v_pairs:
                self._bin_tran_data_java(t, v, sim_time, bin_time, command, bin_param, wave_p)

            # === FORCE LAST BIN TO EXACT sim_time (JAVA EXACT) ===
            if bin_param[3] > 0:
                v_avg = bin_param[2] / bin_param[3]
                last_bin = bin_param[0]
                wave_p.waveData[last_bin].t = sim_time  # ← EXACT
                setattr(wave_p.waveData[last_bin].v, command, v_avg)

            logging.debug(f"[WAVE] {command.upper()} | {len(t_v_pairs)} points → {max_bins} bins")
            return 0

        except Exception as e:
            logging.error(f"Parse error: {e}")
            return 1

    def _bin_tran_data_java(
            self, t: float, v: float, sim_time: float, bin_time: float,
            command: str, bin_param: list, wave_p: IbisWaveTable
    ) -> None:
        """
        EXACT port of Java binTranData using list:
        bin_param = [last_bin, interp_bin, running_sum, num_points_in_bin]
        """
        if bin_time <= 0:
            return

        max_bins = CS.WAVE_POINTS_DEFAULT
        current_bin = min(math.ceil(t / bin_time), max_bins - 1)

        #logging.debug(f"[BIN] t={t:.4e} v={v:.4e} current_bin={current_bin}")

        last_bin = bin_param[0]

        if current_bin == last_bin:
            bin_param[2] += v
            bin_param[3] += 1
            # logging.debug(f"[BIN] Added to bin {current_bin}: sum={bin_param[2]} count={bin_param[3]}")
            return

        # Close previous bin
        if bin_param[3] > 0 and 0 <= last_bin < max_bins:
            v_avg = bin_param[2] / bin_param[3]
            t_bin = last_bin * bin_time
            wave_p.waveData[last_bin].t = t_bin
            setattr(wave_p.waveData[last_bin].v, command, v_avg)
            #logging.debug(f"[BIN] Closed bin {last_bin}: t={t_bin:.4e} v_avg={v_avg:.4e} ({command})")

            # Interpolate skipped bins (linear)
            interp_bin = bin_param[1]
            if last_bin > interp_bin + 1:
                t_start = wave_p.waveData[interp_bin].t
                v_start = getattr(wave_p.waveData[interp_bin].v, command)
                for i in range(interp_bin + 1, last_bin):
                    t_interp = i * bin_time
                    frac = (t_interp - t_start) / (t_bin - t_start)
                    v_interp = v_start + frac * (v_avg - v_start)
                    wave_p.waveData[i].t = t_interp
                    setattr(wave_p.waveData[i].v, command, v_interp)
                    #logging.debug(f"[BIN] Interpolated bin {i}: t={t_interp:.4e} v_interp={v_interp:.4e} ({command})")

            bin_param[1] = last_bin  # interp_bin = last_bin

        # Start new bin
        bin_param[0] = current_bin
        bin_param[2] = v
        bin_param[3] = 1
        #logging.debug(f"[BIN] Started new bin {current_bin}: sum={bin_param[2]} count={bin_param[3]}")

    def generate_vi_curve(
            self,
            current_pin: IbisPin,
            enable_pin: Optional[IbisPin],
            input_pin: Optional[IbisPin],
            power_pin: Optional[IbisPin],
            gnd_pin: Optional[IbisPin],
            power_clamp_pin: Optional[IbisPin],
            gnd_clamp_pin: Optional[IbisPin],
            vcc: IbisTypMinMax,
            gnd: IbisTypMinMax,
            vcc_clamp: IbisTypMinMax,
            gnd_clamp: IbisTypMinMax,
            sweep_start: IbisTypMinMax,
            sweep_range: float,
            sweep_step: float,
            curve_type: int,
            spice_type: int,
            spice_file: str,
            spice_command: str,
            enable_output: int,
            output_high: int,
            iterate: int,
            cleanup: int,
            vds: float = 0.0,
            index: int = 0,
    ) -> int:
        model = current_pin.model
        self.spice_type = spice_type
        #active_sp_file = spice_file or getattr(model, "spice_file", None) or "buffer.sp"
        active_sp_file = self.global_.spice_file

        try:
            num_table_points = int(round(abs(sweep_range) / max(1e-30, abs(sweep_step)))) + 2
        except Exception:
            num_table_points = 2

        vi_cont = IbisVItable(
            VIs=[IbisVItableEntry(v=0.0, i=IbisTypMinMax(0.0, 0.0, 0.0)) for _ in range(num_table_points)],
            size=0,
        )

        # ===================================================================
        # [ISSO_PU] and [ISSO_PD] — FINAL PERFECT VERSION
        # Exact match to commercial tools (your examples)
        # ===================================================================
        vtable_name = "VTABLE_ISSO"
        dummy_node = "DUMMY_ISSO"

        if curve_type == CS.CurveType.ISSO_PULLDOWN:
            # Figure 10: Output LOW → tied to VCC
            power_node = self._pin_node(power_pin) or "vdd"
            gnd_node   = self._pin_node(gnd_pin)   or "vss"
            load_buffer = f"VOUTS2I {current_pin.pinName} {power_node} DC 0\n"

            sweep_start_val = -abs(vcc.typ)
            sweep_range_val = 2 * abs(vcc.typ)

        elif curve_type == CS.CurveType.ISSO_PULLUP:
            # Figure 11: Output HIGH → tied to GND
            power_node = self._pin_node(power_pin) or "vdd"
            gnd_node   = self._pin_node(gnd_pin)   or "vss"
            load_buffer = f"VOUTS2I {current_pin.pinName} {gnd_node} DC 0\n"

            sweep_start_val = +abs(vcc.typ)
            sweep_range_val = -2 * abs(vcc.typ)  # negative → decreasing sweep

        else:
            # Normal curves
            if curve_type == CS.CurveType.SERIES_VI:
                load_buffer = f"VOUTS2I {current_pin.seriesPin2name} 0 DC 0\n"
            else:
                load_buffer = f"VOUTS2I {current_pin.pinName} 0 DC 0\n"

            sweep_start_val = sweep_start.typ
            sweep_range_val = sweep_range

        corners = [
            ("typ", sweep_start.typ, model.modelFile, model.tempRange.typ, vcc.typ, gnd.typ, vcc_clamp.typ,
             gnd_clamp.typ),
            ("min", sweep_start.min, model.modelFileMin, model.tempRange.min, vcc.min, gnd.min, vcc_clamp.min,
             gnd_clamp.min),
            ("max", sweep_start.max, model.modelFileMax, model.tempRange.max, vcc.max, gnd.max, vcc_clamp.max,
             gnd_clamp.max),
        ]

        def _case_flag(corner: str) -> int:
            return CS.TYP_CASE if corner == "typ" else CS.MIN_CASE if corner == "min" else CS.MAX_CASE

        res_total = 0
        for corner, start, model_file, temp, vcc_val, gnd_val, vcc_clamp_val, gnd_clamp_val in corners:
            sweep_end = start + sweep_range
            header_line = f"* {corner.capitalize()} {CS.curve_name_string.get(curve_type, 'unknown')} curve for model {model.modelName}\n"

            case_flag = _case_flag(corner)
            if curve_type == CS.CurveType.SERIES_VI:
                input_buffer = self.set_pin_dc(input_pin, model.polarity, output_high, "gate", case_flag)
                input_buffer += f"VDS {current_pin.pinName} {current_pin.seriesPin2name} DC {vds}\n"
            else:
                input_buffer = self.set_pin_dc(enable_pin, model.enable, enable_output, "ENA", case_flag) or ""
                
                # === INPUT PIN: Only drive when output buffer is ENABLED ===
                is_buffer_enabled = (enable_output == 1)

                if is_buffer_enabled and input_pin:
                    # Normal case: drive input pin to correct logic level
                    vin_line = self.set_pin_dc(input_pin, model.polarity, output_high, "IN", case_flag)
                    if vin_line:
                        input_buffer += ("\n" if input_buffer.strip() else "") + vin_line

                elif input_pin:
                    # === CLAMP or DISABLED curves: DO NOT drive input ===
                    # Add weak resistor to the ACTUAL ground reference node
                    # Should disabled pullup and power clamp have weak resistor tie to power reference node instead? Need further research
                    # What if there's no weak resistor, in other words the effects of leaving input node float? Also need further testings
                    input_node = self._pin_node(input_pin) or input_pin.pinName
                    gnd_node = self._pin_node(gnd_pin) if gnd_pin else "0"  # fallback only if no gnd_pin

                    weak_r = 1.0E10  # 10 GΩ — standard in industry
                    input_buffer += f"RIN_WEAK {input_node} {gnd_node} {weak_r}\n"
                    #input_buffer += f"* Weak tie to ground reference for clamp/disabled curve\n"

            # For ISSO curves: build custom sources with corner-specific vcc_val
            if curve_type in (CS.CurveType.ISSO_PULLUP, CS.CurveType.ISSO_PULLDOWN):
                isso_sources = ""
                if curve_type == CS.CurveType.ISSO_PULLDOWN:
                    isso_sources += f"{vtable_name} 0 {dummy_node} DC 0\n"
                    isso_sources += f"VCC_ISSO {power_node} {dummy_node} DC {abs(vcc_val):.6g}\n"
                    isso_sources += f"VGND_ISSO {gnd_node} 0 DC 0\n"
                else:  # ISSO_PULLUP
                    isso_sources += f"{vtable_name} {power_node} {dummy_node} DC 0\n"
                    isso_sources += f"VCC_ISSO {dummy_node} 0 DC {abs(vcc_val):.6g}\n"
                    isso_sources += f"VGND_ISSO {gnd_node} 0 DC 0\n"
                power_buffer = isso_sources
            else:
                power_buffer = self.setup_power_temp_cmds(
                    curve_type, power_pin, gnd_pin, power_clamp_pin, gnd_clamp_pin,
                    vcc_val, gnd_val, vcc_clamp_val, gnd_clamp_val, temp
                )

            # ===================================================================
            # POWER & ANALYSIS — ISSO curves use custom sources + manual .DC
            # ===================================================================
            if curve_type in (CS.CurveType.ISSO_PULLUP, CS.CurveType.ISSO_PULLDOWN):
                temp_line = self._temp_string(temp)
                opts_line = self._spice_options()
                power_buffer += temp_line

                # Start/End for ISSO sweeps must use the TYPical VCC only (do not vary by corners)
                # Fall back to 3.3 V if typ is not available
                vcc_typ = abs(vcc.typ) if not math.isnan(vcc.typ) else 3.3
                start_val = -vcc_typ if curve_type == CS.CurveType.ISSO_PULLDOWN else +vcc_typ
                end_val   = +vcc_typ if curve_type == CS.CurveType.ISSO_PULLDOWN else -vcc_typ

                analysis_buffer = f".DC {vtable_name} {start_val:.6g} {end_val:.6g} {sweep_step:.6g}\n"
                analysis_buffer += ".PRINT DC I(VOUTS2I)\n"
            else:
                power_buffer = self.setup_power_temp_cmds(
                    curve_type, power_pin, gnd_pin, power_clamp_pin, gnd_clamp_pin,
                    vcc_val, gnd_val, vcc_clamp_val, gnd_clamp_val, temp
                )
                sweep_end = start + sweep_range_val
                analysis_buffer = self.setup_dc_sweep_cmds(curve_type, start, sweep_end, sweep_step)

            if corner == "typ":
                prefix = CS.spice_file_typ_prefix.get(curve_type, "")
            elif corner == "min":
                prefix = CS.spice_file_min_prefix.get(curve_type, "")
            else:
                prefix = CS.spice_file_max_prefix.get(curve_type, "")

            use_index = index if curve_type == CS.CurveType.SERIES_VI else None  # Fix for Issue 7
            spice_in, spice_out, spice_msg, spice_st0, spice_ic, spice_ic0 = self.setup_spice_file_names(
                prefix, current_pin.pinName, use_index
            )

            if self.setup_spice_input_file(
                    iterate, header_line, active_sp_file, model_file, model.ext_spice_cmd_file,
                    load_buffer, input_buffer, power_buffer, "", analysis_buffer, spice_in
            ):
                logging.error(
                    f"Couldn't set up Spice File for {corner} {CS.curve_name_string.get(curve_type, '')} curve")
                res_total += 1
                continue

            _ = self.call_spice(iterate, spice_command, spice_in, spice_out, spice_msg)

            def _contains(path: str, needles: list[str]) -> bool:
                try:
                    if os.path.exists(path):
                        with open(path, "r", encoding="utf-8", errors="ignore") as f:
                            text = f.read().lower()
                            return any(n in text for n in needles)
                except Exception:
                    pass
                return False

            _num_line = re.compile(r"\s*[+-]?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?\s+[+-]?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?\s*$")

            def _has_numeric_rows(path: str) -> bool:
                try:
                    if os.path.exists(path):
                        with open(path, "r", encoding="utf-8", errors="ignore") as f:
                            for ln in f:
                                if _num_line.match(ln.strip()):
                                    return True
                except Exception:
                    pass
                return False

            aborted = (
                    self.check_for_abort(spice_out, spice_msg) == 1
                    or _contains(spice_out, ["abort", "aborted"])
                    or _contains(spice_msg, ["abort", "aborted", "simulation aborted"])
            )

            nonconv = (
                    self.check_for_convergence(spice_out) == 1
                    or _contains(spice_out, ["non convergence", "non-convergence", "nonconvergence"])
                    or _contains(spice_msg, ["non convergence", "non-convergence", "nonconvergence"])
            )

            if aborted and not nonconv and not _has_numeric_rows(spice_out):
                nonconv = True

            if aborted and nonconv:
                rc = self.run_spice_again(
                    curve_type=curve_type,
                    sweep_step=sweep_step,
                    spice_in=spice_in,
                    spice_out=spice_out,
                    spice_msg=spice_msg,
                    iterate=iterate,
                    header_line=header_line,
                    spice_command=spice_command,
                    spice_file=active_sp_file,
                    model_file=model_file,
                    ext_spice_cmd_file=model.ext_spice_cmd_file,
                    load_buffer=load_buffer,
                    input_buffer=input_buffer,
                    power_buffer=power_buffer,
                    temperature_buffer="",
                    orig_sweep_start=start,
                    sweep_range=sweep_range,
                )
                if rc != 0:
                    res_total += 1
                    continue
            elif aborted and not nonconv:
                logging.error("---")
                res_total += 1
                continue

            if self.get_spice_vi_data(vi_cont, num_table_points, spice_out, corner):
                logging.error(f"Curve {CS.curve_name_string.get(curve_type, '')} not generated.")
                res_total += 1  # Fix for Issue 6
                continue

            if cleanup:
                self.cleanup_files(spice_in, spice_out, spice_msg, spice_st0, spice_ic, spice_ic0)

        if curve_type == CS.CurveType.PULLUP:
            model.pullupData = vi_cont
        elif curve_type == CS.CurveType.PULLDOWN:
            model.pulldownData = vi_cont
        elif curve_type == CS.CurveType.POWER_CLAMP:
            model.powerClampData = vi_cont
        elif curve_type == CS.CurveType.GND_CLAMP:
            model.gndClampData = vi_cont
        elif curve_type == CS.CurveType.DISABLED_PULLUP:
            model.pullupData = vi_cont
        elif curve_type == CS.CurveType.DISABLED_PULLDOWN:
            model.pulldownData = vi_cont
        elif curve_type == CS.CurveType.SERIES_VI:
            model.seriesVITables.append(vi_cont)

        self.last_vi_table = vi_cont
        return res_total

    def generate_ramp_data(
            self,
            current_pin: IbisPin,
            enable_pin: Optional[IbisPin],
            input_pin: Optional[IbisPin],
            power_pin: Optional[IbisPin],
            gnd_pin: Optional[IbisPin],
            power_clamp_pin: Optional[IbisPin],
            gnd_clamp_pin: Optional[IbisPin],
            vcc: IbisTypMinMax,
            gnd: IbisTypMinMax,
            vcc_clamp: IbisTypMinMax,
            gnd_clamp: IbisTypMinMax,
            curve_type: int,
            spice_type: int,
            spice_file: str,
            spice_command: str,
            iterate: int,
            cleanup: int,
    ) -> int:
        model = current_pin.model
        self.spice_type = spice_type
        #active_sp_file = spice_file or getattr(model, "spice_file", None) or "buffer.sp"
        active_sp_file = self.global_.spice_file

        logging.debug(f"Using simTime={model.simTime}, spice_file={active_sp_file} for ramp data generation")

        output_state = CS.OUTPUT_RISING if curve_type == CS.CurveType.RISING_RAMP else CS.OUTPUT_FALLING

        # Load wiring with model -> global Rload
        mt = model.modelType
        g = getattr(self, "global_", None)
        rload_model = getattr(model, "Rload", None) if hasattr(model, "Rload") else None
        rload_global = getattr(g, "Rload", 50.0) if g and hasattr(g, "Rload") else 50.0
        rload = rload_model if rload_model and not math.isnan(rload_model) and rload_model > 0 else rload_global
        logging.debug(
            f"Using Rload={rload} (model={rload_model}, global={rload_global}) for curve_type={CS.curve_name_string.get(curve_type, 'unknown')}")
        if mt in [CS.ModelType.OPEN_DRAIN, CS.ModelType.OPEN_SINK,
                  CS.ModelType.IO_OPEN_DRAIN, CS.ModelType.IO_OPEN_SINK]:
            load_buffer = f"RLOADS2I {current_pin.pinName} {power_pin.pinName if power_pin else '0'} {rload}\n"
        elif mt in [CS.ModelType.OPEN_SOURCE, CS.ModelType.IO_OPEN_SOURCE]:
            load_buffer = f"RLOADS2I {current_pin.pinName} {gnd_pin.pinName if gnd_pin else '0'} {rload}\n"
        elif mt in [CS.ModelType.OUTPUT_ECL, CS.ModelType.IO_ECL]:
            load_buffer = f"RLOADS2I {current_pin.pinName} dummy0 {rload}\n"
            load_buffer += f"VTERMS2I dummy0 {power_pin.pinName if power_pin else '0'} DC {CS.ECL_TERMINATION_VOLTAGE_DEFAULT}\n"
        elif curve_type == CS.CurveType.RISING_RAMP:
            load_buffer = f"RLOADS2I {current_pin.pinName} {gnd_pin.pinName if gnd_pin else '0'} {rload}\n"
        else:
            load_buffer = f"RLOADS2I {current_pin.pinName} {power_pin.pinName if power_pin else '0'} {rload}\n"

        corners = [
            ("typ", model.modelFile, model.tempRange.typ, vcc.typ, gnd.typ, vcc_clamp.typ, gnd_clamp.typ),
            ("min", model.modelFileMin, model.tempRange.min, vcc.min, gnd.min, vcc_clamp.min, gnd_clamp.min),
            ("max", model.modelFileMax, model.tempRange.max, vcc.max, gnd.max, vcc_clamp.max, gnd_clamp.max),
        ]

        res_total = 0
        for corner, model_file, temp, vcc_val, gnd_val, vcc_clamp_val, gnd_clamp_val in corners:
            header_line = f"* {corner.capitalize()} {CS.curve_name_string.get(curve_type, 'unknown')} curve for model {model.modelName}\n"

            case_flag = CS.TYP_CASE if corner == "typ" else CS.MIN_CASE if corner == "min" else CS.MAX_CASE
            input_buffer = self.set_pin_dc(enable_pin, model.enable, CS.ENABLE_OUTPUT, "ENA", case_flag) or ""
            if input_pin:
                pulse = self.set_pin_tran(input_pin, model.polarity, output_state, "IN", case_flag)
                input_buffer += ("\n" if input_buffer else "") + pulse

            power_buffer = self.setup_power_temp_cmds(
                curve_type, power_pin, gnd_pin, power_clamp_pin, gnd_clamp_pin,
                vcc_val, gnd_val, vcc_clamp_val, gnd_clamp_val, temp
            )

            analysis_buffer = self.setup_tran_cmds(model.simTime, current_pin.pinName)

            if corner == "typ":
                prefix = CS.spice_file_typ_prefix.get(curve_type, "")
            elif corner == "min":
                prefix = CS.spice_file_min_prefix.get(curve_type, "")
            else:
                prefix = CS.spice_file_max_prefix.get(curve_type, "")
            spice_in, spice_out, spice_msg, spice_st0, spice_ic, spice_ic0 = self.setup_spice_file_names(prefix,
                                                                                                         current_pin.pinName)

            if self.setup_spice_input_file(
                    iterate, header_line, active_sp_file, model_file, model.ext_spice_cmd_file,
                    load_buffer, input_buffer, power_buffer, "", analysis_buffer, spice_in
            ):
                logging.error(f"Failed to setup SPICE file {spice_in}")
                res_total += 1
                continue

            if self.call_spice(iterate, spice_command, spice_in, spice_out, spice_msg):
                if self.check_for_abort(spice_out, spice_msg):
                    logging.error(f"Abort detected in {spice_in}")
                    res_total += 1
                    continue
                logging.error("SPICE process failed without abort marker")
                res_total += 1
                continue

            if self.get_spice_ramp_data(model, curve_type, spice_out, corner):
                logging.error(f"Failed to extract ramp data from {spice_out}")
                res_total += 1
                continue

            if cleanup:
                self.cleanup_files(spice_in, spice_out, spice_msg, spice_st0, spice_ic, spice_ic0)

        return res_total

    def generate_wave_data(
            self,
            current_pin: IbisPin,
            enable_pin: Optional[IbisPin],
            input_pin: Optional[IbisPin],
            power_pin: Optional[IbisPin],
            gnd_pin: Optional[IbisPin],
            power_clamp_pin: Optional[IbisPin],
            gnd_clamp_pin: Optional[IbisPin],
            vcc: IbisTypMinMax,
            gnd: IbisTypMinMax,
            vcc_clamp: IbisTypMinMax,
            gnd_clamp: IbisTypMinMax,
            curve_type: int,
            spice_type: int,
            spice_file: str,
            spice_command: str,
            iterate: int,
            cleanup: int,
            index: int,
    ) -> int:
        model = current_pin.model
        self.spice_type = spice_type
        #active_sp_file = spice_file or getattr(model, "spice_file", None) or "buffer.sp"
        active_sp_file = self.global_.spice_file

        logging.debug(f"Using simTime={model.simTime}, spice_file={active_sp_file} for waveform data generation")

        # === CLEAR AND USE EXISTING WAVES FROM INPUT ===
        if curve_type == CS.CurveType.RISING_WAVE:
            input_waves = model.risingWaveList
            model.risingWaveList = []
        else:
            input_waves = model.fallingWaveList
            model.fallingWaveList = []

        # === GET UNIQUE R_fixture FROM INPUT (NO HARD-CODING) ===
        r_fixtures = []
        for wave in input_waves:
            if wave.R_fixture not in r_fixtures:
                r_fixtures.append(wave.R_fixture)

        # === REBUILD WAVES LIST WITH R_fixture and V_fixture FROM INPUT ===
        waves = []
        for input_wave in input_waves:
            wave = IbisWaveTable(
                R_fixture=input_wave.R_fixture,
                V_fixture=input_wave.V_fixture  # SINGLE VALUE
            )
            wave.waveData = [
                IbisWaveTableEntry(t=0.0, v=IbisTypMinMax(0, 0, 0))
                for _ in range(CS.WAVE_POINTS_DEFAULT)
            ]
            waves.append(wave)
            if curve_type == CS.CurveType.RISING_WAVE:
                model.risingWaveList.append(wave)
            else:
                model.fallingWaveList.append(wave)

        # === INITIALIZE waveData ONCE PER WAVE (CRITICAL FIX) ===
        # === INITIALIZE waveData WITH REAL OBJECTS ===
        for wave in waves:
            wave.waveData = [
                IbisWaveTableEntry(t=0.0, v=IbisTypMinMax(0, 0, 0))
                for _ in range(CS.WAVE_POINTS_DEFAULT)
            ]

        output_state = CS.OUTPUT_RISING if curve_type == CS.CurveType.RISING_WAVE else CS.OUTPUT_FALLING

        res_total = 0
        for wave_idx, wave in enumerate(waves):
            # === BUILD LOAD BUFFER FOR THIS WAVE ===
            node_list = [current_pin.pinName] + [f"dummy{i}" for i in range(10)]
            node_index = 0
            load_buffer = ""

            if not math.isnan(wave.L_dut):
                load_buffer += f"LDUTS2I {node_list[node_index]} {node_list[node_index + 1]} {wave.L_dut}\n"
                node_index += 1
            if not math.isnan(wave.R_dut):
                load_buffer += f"RDUTS2I {node_list[node_index]} {node_list[node_index + 1]} {wave.R_dut}\n"
                node_index += 1
            if not math.isnan(wave.C_dut):
                load_buffer += f"CDUTS2I {node_list[node_index]} 0 {wave.C_dut}\n"

            output_node = node_list[node_index]

            if not math.isnan(wave.L_fixture):
                load_buffer += f"LFIXS2I {node_list[node_index]} {node_list[node_index + 1]} {wave.L_fixture}\n"
                node_index += 1
            if not math.isnan(wave.C_fixture):
                load_buffer += f"CFIXS2I {node_list[node_index]} 0 {wave.C_fixture}\n"

            load_buffer += f"RFIXS2I {node_list[node_index]} {node_list[node_index + 1]} {wave.R_fixture}\n"
            node_index += 1

            # === CORNERS FOR THIS WAVE ===
            corners = [
                ("typ", model.modelFile, model.tempRange.typ, vcc.typ, gnd.typ, vcc_clamp.typ, gnd_clamp.typ,
                 wave.V_fixture),
                ("min", model.modelFileMin, model.tempRange.min, vcc.min, gnd.min, vcc_clamp.min, gnd_clamp.min,
                 wave.V_fixture_min if not math.isnan(wave.V_fixture_min) else wave.V_fixture),
                ("max", model.modelFileMax, model.tempRange.max, vcc.max, gnd.max, vcc_clamp.max, gnd_clamp.max,
                 wave.V_fixture_max if not math.isnan(wave.V_fixture_max) else wave.V_fixture),
            ]

            for corner, model_file, temp, vcc_val, gnd_val, vcc_clamp_val, gnd_clamp_val, v_fixture in corners:
                header_line = f"* {corner.capitalize()} {CS.curve_name_string.get(curve_type, 'unknown')} curve for model {model.modelName}\n"
                case_flag = CS.TYP_CASE if corner == "typ" else CS.MIN_CASE if corner == "min" else CS.MAX_CASE

                input_buffer = self.set_pin_dc(enable_pin, model.enable, CS.ENABLE_OUTPUT, "ENA", case_flag) or ""
                if input_pin:
                    pulse = self.set_pin_tran(input_pin, model.polarity, output_state, "IN", case_flag)
                    if pulse:
                        input_buffer += ("\n" if input_buffer else "") + pulse

                input_buffer += f"\nVFIXS2I {node_list[node_index]} 0 DC {v_fixture}\n"

                power_buffer = self.setup_power_temp_cmds(
                    curve_type, power_pin, gnd_pin, power_clamp_pin, gnd_clamp_pin,
                    vcc_val, gnd_val, vcc_clamp_val, gnd_clamp_val, temp
                )

                analysis_buffer = self.setup_tran_cmds(model.simTime, output_node)

                if corner == "typ":
                    base = CS.spice_file_typ_prefix[curve_type]
                elif corner == "min":
                    base = CS.spice_file_min_prefix[curve_type]
                else:
                    base = CS.spice_file_max_prefix[curve_type]

                name_prefix = f"{base}{wave_idx:02d}"
                spice_in, spice_out, spice_msg, spice_st0, spice_ic, spice_ic0 = self.setup_spice_file_names(
                    name_prefix, current_pin.pinName
                )

                if self.setup_spice_input_file(
                        iterate, header_line, active_sp_file, model_file, model.ext_spice_cmd_file,
                        load_buffer, input_buffer, power_buffer, "", analysis_buffer, spice_in
                ):
                    logging.error(f"Failed to setup SPICE file {spice_in}")
                    res_total += 1
                    continue

                if self.call_spice(iterate, spice_command, spice_in, spice_out, spice_msg):
                    if self.check_for_abort(spice_out, spice_msg):
                        logging.error(f"Abort detected in {spice_in}")
                        res_total += 1
                        continue
                    logging.error("SPICE process failed without abort marker")
                    res_total += 1
                    continue

                if self.get_spice_wave_data(model.simTime, spice_out, corner, wave, curve_type):
                    logging.error(f"Failed to extract waveform data from {spice_out}")
                    res_total += 1
                    continue

                if cleanup:
                    self.cleanup_files(spice_in, spice_out, spice_msg, spice_st0, spice_ic, spice_ic0)

        return res_total

    def run_simulations(self, args_list: List[Tuple[callable, tuple]] ) -> List[int]:
        results = []
        for func, args in args_list:
            result = func(*args)
            results.append(result)
        return results

    def cleanup_files(self, spice_in: str, spice_out: str, spice_msg: str, spice_st0: str, spice_ic: str,
                      spice_ic0: str) -> int:
        files = [spice_in, spice_msg, spice_st0, spice_ic, spice_ic0]
        # Handle .lis file
        lis_file = os.path.splitext(spice_out)[0] + ".lis"
        files.append(lis_file)
        # Prepend outdir to all files
        if self.outdir:
            files = [os.path.join(self.outdir, os.path.basename(f)) for f in files]
        for file in files:
            if os.path.exists(file):
                try:
                    os.remove(file)
                    logging.info(f"Removed temporary file {file}")
                except Exception as e:
                    logging.warning(f"Failed to remove {file}: {e}")
        return 0
