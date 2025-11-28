"""Package copy of correlation.py with package imports."""
import os
import logging
from datetime import datetime
from jinja2 import Environment, FileSystemLoader, TemplateNotFound
try:
    from jinja2 import PackageLoader, ChoiceLoader
except Exception:  # older jinja2 fallback
    PackageLoader = None
    ChoiceLoader = None
from importlib.resources import files, as_file
from typing import Optional, Dict, Any
from s2ibispy.models import IbisModel, IbisTOP
from s2ibispy.s2ispice import S2ISpice
from s2ibispy.s2i_constants import ConstantStuff as CS
from s2ibispy.s2ianaly import FindSupplyPins


def find_model_for_correlation(
    ibis: IbisTOP,
    requested_name: Optional[str] = None
) -> Optional[IbisModel]:
    if not ibis.mList:
        logging.info("No models found in IBIS file — skipping correlation")
        return None

    if requested_name:
        requested = requested_name.strip().lower()
        for m in ibis.mList:
            if m.modelName.lower() == requested:
                logging.info(f"Correlation: Using requested model '{m.modelName}'")
                return m
        logging.warning(f"Requested model '{requested_name}' not found — skipping correlation")
        return None

    for m in ibis.mList:
        if getattr(m, "noModel", False):
            continue
        mt = str(m.modelType).upper()
        if mt not in {"POWER", "GND", "NC", "NOMODEL", "DUMMY"}:
            logging.info(f"Correlation: Auto-selected model '{m.modelName}' (first real buffer)")
            return m

    logging.info(f"Correlation: Using first model '{ibis.mList[0].modelName}' (fallback)")
    return ibis.mList[0]


def prepare_netlist_for_correlation(model: IbisModel, outdir: str) -> dict:
    original_path = model.spice_file
    if not original_path or not os.path.exists(original_path):
        raise FileNotFoundError(f"Spice file not found: {original_path}")

    with open(original_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    if any(line.strip().lower().startswith(".subckt") for line in content.splitlines()):
        for line in content.splitlines():
            if line.strip().lower().startswith(".subckt"):
                parts = line.split()
                name = parts[1].upper() if len(parts) > 1 else "IO_BUF"
                pins = parts[2:] if len(parts) > 2 else []
                break
        else:
            name = "IO_BUF"
            pins = []
        logging.info(f"Using existing subcircuit: {name}")
        return {
            "is_subcircuit": True,
            "subcircuit_name": name,
            "spice_include": f'.INCLUDE "{os.path.abspath(original_path)}"',
            "pin_list": pins,
        }

    logging.info("Flat netlist → creating subcircuit wrapper")
    wrapper_name = f"{model.modelName.upper()}_WRAPPER"

    nodes = set()
    for line in content.splitlines():
        l = line.lower()
        if l.strip() == "" or l.startswith(("*", ".", "$")):
            continue
        tokens = l.split()
        if not tokens:
            continue
        start = 1 if tokens[0][0] in "mcxMCX" else 0
        for t in tokens[start:]:
            t = t.split("=")[0]
            if t.isalpha() or (t[0].isalpha() and t[1:].replace("_", "").isalnum()):
                if t not in {"vdd", "vss", "gnd", "0", "pfet", "nfet", "w", "l", "m"}:
                    nodes.add(t)

    priority = ["in", "oe", "en", "enable", "out", "pad", "io", "in_sense", "sense"]
    pins = sorted(nodes, key=lambda p: (priority.index(p.lower()) if p.lower() in priority else 999, p.lower()))[:4]
    if "vdd" not in pins:
        pins.append("vdd")
    if "vss" not in pins:
        pins.append("vss")

    wrapper_path = os.path.join(outdir, f"{wrapper_name.lower()}.sp")
    with open(wrapper_path, "w", encoding="utf-8") as f:
        f.write(f"* Auto-generated subcircuit wrapper for {model.modelName}\n")
        f.write(f".subckt {wrapper_name} {' '.join(pins)}\n\n")
        if getattr(model, "modelFile", None) and model.modelFile != "NA":
            f.write(f".INCLUDE \"{os.path.abspath(model.modelFile)}\"\n\n")
        f.write(content.rstrip())
        if not content.strip().endswith("\n"):
            f.write("\n")
        f.write(f"\n.ends {wrapper_name}\n")

    logging.info(f"Wrapper created: {wrapper_path} → {wrapper_name} {' '.join(pins)}")

    return {
        "is_subcircuit": True,
        "subcircuit_name": wrapper_name,
        "spice_include": f'.INCLUDE "{os.path.abspath(wrapper_path)}"',
        "pin_list": pins,
    }


def generate_and_run_correlation(
    model: IbisModel,
    ibis: IbisTOP,
    outdir: str,
    s2ispice: S2ISpice,
    config: Dict[str, Any] = None,
):
    from s2ibispy.s2ioutput import IbisWriter
    writer = IbisWriter(ibis_head=None)
    mt_str = writer._model_type_str(getattr(model,'modelType', ''))

    if mt_str not in {"I/O", "3-state"}:
        logging.info(f"Skipping correlation for {model.modelName} — Model_type '{mt_str}' not supported")
        return None, 0

    if not getattr(model, "spice_file", None):
        logging.info(f"Skipping correlation for {model.modelName} — no SPICE netlist defined")
        return None, 0

    if model is None:
        model = find_model_for_correlation(ibis)
        if model is None:
            logging.error("No valid model found for correlation")
            return None, -1

    os.makedirs(outdir, exist_ok=True)

    try:
        netlist_info = prepare_netlist_for_correlation(model, outdir)
    except Exception as e:
        logging.error(f"Failed to prepare netlist: {e}")
        return None, -1

    subcircuit_name = netlist_info["subcircuit_name"]
    spice_include = netlist_info["spice_include"]
    pin_list = netlist_info["pin_list"]

    pullup_pin = pulldown_pin = None
    find_supply = FindSupplyPins()
    for component in ibis.cList:
        for pin in component.pList:
            if pin.model == model:
                supply_pins = find_supply.find_pins(pin, component.pList, component.hasPinMapping)
                pullup_pin = supply_pins.get("pullupPin")
                pulldown_pin = supply_pins.get("pulldownPin")
                if pullup_pin and pulldown_pin:
                    break
        if pullup_pin and pulldown_pin:
            break

    if not pullup_pin:
        vdd_name = next((p for p in pin_list if p.lower() in {"vdd", "vcc", "vddio"}), "vdd")
        pullup_pin = type('obj', (), {'pinName': vdd_name})()
        logging.info(f"Using fallback VDD pin: {vdd_name}")
    if not pulldown_pin:
        vss_name = next((p for p in pin_list if p.lower() in {"vss", "gnd", "0", "vssio"}), "vss")
        pulldown_pin = type('obj', (), {'pinName': vss_name})()
        logging.info(f"Using fallback VSS pin: {vss_name}")

    def make_instance(num: int, in_node: str, oe_node: str) -> str:
        nodes = ["0"] * len(pin_list)

        in_idx = next((i for i, p in enumerate(pin_list) if p.lower() in {"in", "data", "d", "a"}), 0)
        oe_idx = next((i for i, p in enumerate(pin_list) if p.lower() in {"oe", "en", "enable", "tri"}), 1)
        out_idx = next((i for i, p in enumerate(pin_list) if p.lower() in {"out", "pad", "io", "y", "q"}), 2)
        sense_idx = next((i for i, p in enumerate(pin_list) if "sense" in p.lower()), None)

        nodes[in_idx] = in_node
        nodes[oe_idx] = oe_node
        nodes[out_idx] = f"out{num}SPICE"
        if sense_idx is not None:
            nodes[sense_idx] = f"sense{num}"

        try:
            vdd_idx = pin_list.index(pullup_pin.pinName)
            nodes[vdd_idx] = pullup_pin.pinName
        except ValueError:
            pass
        try:
            vss_idx = pin_list.index(pulldown_pin.pinName)
            nodes[vss_idx] = pulldown_pin.pinName
        except ValueError:
            pass

        return f"X{num}SPICE {' '.join(nodes)} {subcircuit_name}"

    x_instances = "\n".join([
        make_instance(1, "in_spice", "oe1"),
        make_instance(2, pulldown_pin.pinName, "oe2"),
        make_instance(3, "in_spice", "oe3"),
    ])

    oe_stimuli = """
* Independent OE control
VENA1 oe1 0 DC 3.3
VENA2 oe2 0 DC 3.3   $ Quiet line — change to DC 0 for true high-Z
VENA3 oe3 0 DC 3.3
"""

    template_dir = None
    if isinstance(config, dict):
        template_dir = config.get("template_dir") or config.get("templates") or config.get("template_path")

    loaders = []
    if template_dir and os.path.isdir(template_dir):
        loaders.append(FileSystemLoader(template_dir))
    # packaged templates
    if PackageLoader is not None:
        try:
            loaders.append(PackageLoader("s2ibispy", "templates"))
        except Exception:
            pass
    # repo-relative fallback
    loaders.append(FileSystemLoader("templates"))
    loaders.append(FileSystemLoader(os.path.join(os.path.dirname(__file__), "..", "..", "templates")))

    if ChoiceLoader is not None and loaders:
        env = Environment(loader=ChoiceLoader(loaders))
    else:
        env = Environment(loader=loaders[0])

    try:
        template = env.get_template("compare_correlation.sp.j2")
    except TemplateNotFound:
        # last resort: direct filesystem
        fallback_env = Environment(loader=FileSystemLoader("templates"))
        template = fallback_env.get_template("compare_correlation.sp.j2")

    # packaged RLGC file path
    rlgc_path = None
    try:
        r = files("s2ibispy").joinpath("data").joinpath("Z50_406.lc3")
        with as_file(r) as p:
            rlgc_path = str(p)
    except Exception:
        rlgc_path = os.path.abspath(os.path.join(os.getcwd(), "Z50_406.lc3"))

    context = {
        "model": model,
        "ibis": ibis,
        "now": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "subcircuit_name": subcircuit_name,
        "spice_include": spice_include,
        "pin_list": pin_list,
        "x_instances": x_instances,
        "oe_stimuli": oe_stimuli,
        "pullup_pin": pullup_pin,
        "pulldown_pin": pulldown_pin,
        "ibis_fullpath": os.path.abspath(os.path.join(outdir, ibis.thisFileName)),
        "rlgc_path": rlgc_path,
    }

    out_path = os.path.join(outdir, f"correlate_{model.modelName}.sp")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(template.render(**context))

    logging.info(f"Correlation deck created: {out_path}")

    # Run the spice tool if provided
    if s2ispice is not None:
        try:
            out_base = os.path.join(outdir, f"correlate_{model.modelName}")
            msg_file = out_base + ".msg"
            # Note: For HSPICE, pass base name without .tr0 extension
            # HSPICE will create .tr0 file automatically
            rc = s2ispice.call_spice(
                iterate=ibis.iterate if hasattr(ibis, 'iterate') else 0,
                spice_command=ibis.spiceCommand if hasattr(ibis, 'spiceCommand') else "",
                spice_in=out_path,
                spice_out=out_base,  # No .tr0 extension - HSPICE adds it
                spice_msg=msg_file,
            )
            if rc == 0:
                logging.info(f"Correlation SPICE run succeeded for {model.modelName}")
            else:
                logging.error(f"Correlation SPICE run failed for {model.modelName} — see {msg_file}")
            return out_path, rc
        except Exception as e:
            logging.error(f"Correlation run failed: {e}")
            return out_path, -1

    return out_path, 0
