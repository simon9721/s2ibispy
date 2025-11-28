#!/usr/bin/env python3
# cli.py — Packaged entrypoint (moved from main.py)
import argparse
import logging
import os
import sys
import subprocess
from typing import Optional, Any
from pathlib import Path

from s2ibispy.legacy.parser import S2IParser
from s2ibispy.s2ianaly import S2IAnaly
from s2ibispy.s2ioutput import IbisWriter as S2IOutput

try:
    from s2ibispy.loader import load_yaml_config
    YAML_SUPPORT = True
except Exception:
    YAML_SUPPORT = False

import re
from typing import Dict

from s2ibispy.correlation import generate_and_run_correlation


def run_ibischk(ibis_file: str, ibischk: str) -> Dict[str, object]:
    try:
        logging.info("Running ibischk7 on %s", ibis_file)
        result = subprocess.run(
            [ibischk, ibis_file],
            text=True,
            capture_output=True,
            check=False,
        )

        full_output = result.stdout + result.stderr

        chk = {
            "returncode": result.returncode,
            "output": full_output,
            "errors": [],
            "warnings": [],
            "notes": [],
        }

        ERROR_RE = re.compile(r"^ERROR\b|^FATAL\b", re.IGNORECASE)
        WARNING_RE = re.compile(r"^WARNING\b", re.IGNORECASE)
        NOTE_RE = re.compile(r"^NOTE\b", re.IGNORECASE)

        for raw_line in full_output.splitlines():
            line = raw_line.rstrip()
            if not line.strip():
                continue

            lower = line.lower()

            if any(phrase in lower for phrase in [
                "ibischk", "checking ", "for ibis ", "compatibility",
                "errors  :", "warnings:", "file passed", "file failed",
                "processed successfully"
            ]):
                continue

            if ERROR_RE.search(line):
                chk["errors"].append(line)
            elif WARNING_RE.search(line):
                chk["warnings"].append(line)
            elif NOTE_RE.search(line):
                chk["notes"].append(line)

        chk["errors"] = [e for e in chk["errors"] if "0 error" not in e.lower()]
        chk["warnings"] = [w for w in chk["warnings"] if "0 warning" not in w.lower()]

        if chk["errors"]:
            logging.error("ibischk7 found %d REAL ERROR(S) → IBIS model is INVALID!", len(chk["errors"]))
            for e in chk["errors"][:10]:
                logging.error("  ERR → %s", e)
        else:
            logging.info("ibischk7: No errors — model passed syntax check")

        if chk["warnings"]:
            logging.warning("ibischk7 found %d warning(s)", len(chk["warnings"]))

        logging.info("ibischk7 issued %d note(s)", len(chk["notes"]))
        return chk

    except FileNotFoundError:
        logging.warning("ibischk7 executable not found at '%s' — skipping validation", ibischk)
        return {"returncode": 0, "output": "", "errors": [], "warnings": [], "notes": []}


def run_correlation_for_models(mList, ibis, outdir, s2i_spice, gui=None):
    if s2i_spice is None:
        logging.error("Cannot run correlation: SPICE engine not available (simulations probably failed)")
        return 0

    success = 0
    for model in mList:
        if getattr(model, "noModel", False):
            continue
        try:
            result = generate_and_run_correlation(
                model=model,
                ibis=ibis,
                outdir=outdir,
                s2ispice=s2i_spice,
            )
            deck_path, rc_corr = result if result is not None else (None, 0)

            if rc_corr == 0:
                if deck_path:
                    success += 1
                    msg = f"Correlation SUCCESS → {Path(deck_path).name}"
                else:
                    msg = f"Correlation skipped for {model.modelName}"
                logging.info(msg)
                if gui:
                    gui.log(msg, "INFO")
            else:
                msg = f"Correlation FAILED for {model.modelName}"
                logging.error(msg)
                if gui:
                    gui.log(msg, "ERROR")
        except Exception as e:
            msg = f"Correlation crashed for {model.modelName}: {e}"
            logging.error(msg)
            if gui:
                gui.log(msg, "ERROR")
    logging.info(f"Correlation complete — {success} successful run(s)")
    return success


def main(argv: Optional[list[str]] = None, gui: Optional[Any] = None) -> int:
    p = argparse.ArgumentParser(description="Convert SPICE -> IBIS (s2ibis3-style pipeline).")
    p.add_argument("input", help="Input .s2i text file (your s2ibis recipe/config).")
    p.add_argument("-o", "--outdir", default="out", help="Output directory (default: ./out)")
    p.add_argument("--spice-type", default="hspice",
                   choices=["hspice", "spectre", "eldo"],
                   help="Simulator type (default: hspice)")
    p.add_argument("--spice-cmd", default="", help="Override simulator command line (optional)")
    p.add_argument("--iterate", type=int, default=0, help="Reuse existing SPICE outputs (0/1)")
    p.add_argument("--cleanup", type=int, default=0, help="Delete intermediate SPICE files (0/1)")
    p.add_argument("--ibischk", default="", help="Path to ibischk7_64.exe (optional)")
    p.add_argument("-v", "--verbose", action="store_true", help="Verbose logging")
    p.add_argument("--correlate", action="store_true",
               help="Run SPICE vs IBIS correlation after generation")
    args = p.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    logging.getLogger('').setLevel(logging.DEBUG if args.verbose else logging.INFO)
    logging.debug("Starting main with args: %s", argv)

    input_file = os.path.abspath(args.input)
    outdir = os.path.abspath(args.outdir)
    os.makedirs(outdir, exist_ok=True)

    input_path = Path(input_file)
    if not input_path.exists():
        logging.error("Input file not found: %s", input_file)
        return 2

    if YAML_SUPPORT and input_path.suffix.lower() == ".yaml":
        logging.info("Loading modern YAML config: %s", input_path.name)
        try:
            ibis, global_, mList = load_yaml_config(input_path)
        except Exception as e:
            logging.error("Failed to load YAML: %s", e)
            return 2
    else:
        parser = S2IParser()
        logging.info("Parsing legacy .s2i file: %s", input_path.name)
        try:
            ibis, global_, mList = parser.parse(input_file)
            for comp in ibis.cList:
                if not getattr(comp, "spiceFile", None):
                    continue
                model_names = {
                    pin.modelName for pin in comp.pList
                    if hasattr(pin, "modelName") and pin.modelName
                }
                for name in model_names:
                    model = next((m for m in mList if m.modelName == name), None)
                    if model and not getattr(model, "spice_file", None):
                        model.spice_file = comp.spiceFile
                        logging.info(f"Set model.{model.modelName}.spice_file = {comp.spiceFile}")
            ibis.mList = mList
            logging.debug(f"Parsed global_: vil={getattr(global_, 'vil', None)}, vih={getattr(global_, 'vih', None)}")
        except FileNotFoundError as e:
            logging.error("%s", e)
            return 2

    ibis.spiceType = {"hspice": 0, "spectre": 1, "eldo": 2}.get(args.spice_type, 0)
    ibis.spiceCommand = args.spice_cmd or getattr(ibis, "spiceCommand", "")
    ibis.iterate = args.iterate
    ibis.cleanup = args.cleanup

    logging.info("Running simulations/analysis…")
    analy = S2IAnaly(
        mList=mList,
        spice_type=ibis.spiceType,
        iterate=ibis.iterate,
        cleanup=ibis.cleanup,
        spice_command=ibis.spiceCommand,
        global_=global_,
        outdir=outdir,
        s2i_file=input_file,
    )
    rc = analy.run_all(ibis=ibis, global_=global_)
    if rc != 0:
        logging.error("Analysis failed with code %d", rc)
        return rc

    if getattr(ibis, "thisFileName", None):
        base_name = ibis.thisFileName.strip()
        if not base_name.lower().endswith(".ibs"):
            base_name += ".ibs"
        logging.debug("Using user-specified IBIS filename: %s", base_name)
    else:
        base_name = Path(input_file).stem + ".ibs"
        logging.info("No file_name specified → using input stem: %s", base_name)

    out_file = Path(outdir) / base_name
    out_file.parent.mkdir(parents=True, exist_ok=True)

    logging.info("Writing IBIS to %s", out_file)
    writer = S2IOutput(ibis_head=ibis)
    writer.write_ibis_file(str(out_file))

    if args.ibischk:
        chk = run_ibischk(str(out_file), args.ibischk)

        out_file_str = str(out_file)
        log_path = out_file_str + ".ibischk_log.txt"
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(chk["output"])

        if chk["warnings"]:
            warn_path = out_file_str + ".ibischk_warnings.txt"
            with open(warn_path, "w", encoding="utf-8") as f:
                f.write("\n".join(chk["warnings"]))

        import json
        json_path = out_file_str + ".ibischk_report.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump({
                "returncode": chk["returncode"],
                "errors": chk["errors"],
                "warnings": chk["warnings"],
                "notes": chk["notes"],
                "total_errors": len(chk["errors"]),
                "total_warnings": len(chk["warnings"])
            }, f, indent=2)

        if chk["errors"]:
            logging.error("IBIS file has %d critical error(s) → failing build", len(chk["errors"]))
            return 20

        if chk["warnings"]:
            logging.warning("ibischk7 reported %d warning(s) — model is still valid", len(chk["warnings"]))
        else:
            logging.info("ibischk7 passed with no warnings")

    if gui and getattr(gui, "run_correlation_after_conversion", False):
        logging.info("GUI requested automatic correlation")
        run_correlation_for_models(mList, ibis, outdir, analy.spice, gui=gui)

    if args.correlate:
        logging.info("Running SPICE vs IBIS correlation (--correlate)")
        run_correlation_for_models(mList, ibis, outdir, analy.spice)

    if gui is not None:
        actual_ibis_path = Path(out_file).resolve()
        gui.last_ibis_path = actual_ibis_path
        gui.analy = analy
        gui.ibis = ibis
        gui.log(f"IBIS generated: {actual_ibis_path.name}", "INFO")
        gui.log("Analysis engine attached → ready for plots & correlation", "INFO")

    logging.info("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
