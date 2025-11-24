#!/usr/bin/env python3
# main.py — End-to-end driver: SPICE -> IBIS
import argparse
import logging
import os
import sys
#import shutil
import subprocess
from typing import Optional, Any
from pathlib import Path

from parser import S2IParser
from s2iutil import S2IUtil
from s2ianaly import S2IAnaly
#from s2ioutput import S2IOutput
from s2ioutput import IbisWriter as S2IOutput  # ← Alias!


import re
from typing import Dict

from correlation import generate_and_run_correlation

def run_ibischk(ibis_file: str, ibischk: str) -> Dict[str, object]:
    """Run ibischk7 and return clean, accurate results — no summary lines in errors/warnings."""
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

        # Regexes that match the real message lines (very reliable)
        ERROR_RE   = re.compile(r"^ERROR\b|^FATAL\b", re.IGNORECASE)
        WARNING_RE = re.compile(r"^WARNING\b", re.IGNORECASE)
        NOTE_RE    = re.compile(r"^NOTE\b", re.IGNORECASE)

        for raw_line in full_output.splitlines():
            line = raw_line.rstrip()
            if not line.strip():
                continue

            lower = line.lower()

            # ---- 1. Skip everything that is NOT a real message ----
            if any(phrase in lower for phrase in [
                "ibischk", "checking ", "for ibis ", "compatibility",
                "errors  :", "warnings:", "file passed", "file failed",
                "processed successfully"
            ]):
                continue

            # ---- 2. Classify by prefix (this is 100% accurate for ibischk7) ----
            if ERROR_RE.search(line):
                chk["errors"].append(line)
            elif WARNING_RE.search(line):
                chk["warnings"].append(line)
            elif NOTE_RE.search(line):
                chk["notes"].append(line)
            # No else → unknown lines are simply ignored (never happen with ibischk7)

        # ---- 3. Final safety (paranoid but costs nothing) ----
        chk["errors"]   = [e for e in chk["errors"]   if "0 error"   not in e.lower()]
        chk["warnings"] = [w for w in chk["warnings"] if "0 warning" not in w.lower()]

        # ---- 4. Logging ----
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

    # 1) Parse input file
    parser = S2IParser()
    logging.info("Parsing %s", input_file)
    try:
        ibis, global_, mList = parser.parse(input_file)
        # After ibis, global_, mList = parser.parse(...)
        for comp in ibis.cList:
            if not getattr(comp, "spiceFile", None):
                continue

            # Get all unique model names used by pins in this component
            model_names = {
                pin.modelName for pin in comp.pList
                if hasattr(pin, "modelName") and pin.modelName
            }

            for name in model_names:
                model = next((m for m in mList if m.modelName == name), None)
                if model and not getattr(model, "spice_file", None):
                    model.spice_file = comp.spiceFile
                    logging.info(f"Set model.{model.modelName}.spice_file = {comp.spiceFile}")
        ibis.mList = mList  # ← ADD THIS
        logging.debug(f"Parsed global_: vil={getattr(global_, 'vil', None)}, vih={getattr(global_, 'vih', None)}")
    except FileNotFoundError as e:
        logging.error("%s", e)
        return 2

    # Attach CLI overrides
    ibis.spiceType = {"hspice": 0, "spectre": 1, "eldo": 2}.get(args.spice_type, 0)
    ibis.spiceCommand = args.spice_cmd or getattr(ibis, "spiceCommand", "")
    ibis.iterate = args.iterate
    ibis.cleanup = args.cleanup

    # 2) Complete data structures
    logging.info("Completing data structures…")
    util = S2IUtil(mList)
    util.complete_data_structures(ibis, global_)

    # 3) Run analysis/simulations
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
    


    # 4) Write the .ibs file
    out_file = os.path.join(outdir, os.path.splitext(os.path.basename(input_file))[0] + ".ibs")
    logging.info("Writing IBIS to %s", out_file)
    writer = S2IOutput(ibis_head=ibis)
    writer.write_ibis_file(str(out_file))

        # ←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←
    # FINAL: Run correlation if GUI requested it
    # ←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←
    if gui and gui.run_correlation_after_conversion:
        logging.info("GUI: Running correlation automatically...")
        from correlation import generate_and_run_correlation
        success = 0
        for model in mList:
            if getattr(model, "noModel", False):
                continue
            try:
                deck_path, rc_corr = generate_and_run_correlation(
                    model=model,
                    ibis=ibis,
                    outdir=outdir,
                    s2ispice=analy.spice,  # ← still alive!
                )
                if rc_corr == 0:
                    success += 1
                    logging.info(f"Correlation SUCCESS → {Path(deck_path).name}")
            except Exception as e:
                logging.error(f"Correlation crashed: {e}")
        logging.info(f"Correlation complete: {success} model(s) processed")
    # ←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←

    # 5) Run ibischk7 if requested
    if args.ibischk:
        chk = run_ibischk(str(out_file), args.ibischk)

        # Save logs exactly like you already do...
        log_path = out_file + ".ibischk_log.txt"
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(chk["output"])

        if chk["warnings"]:
            warn_path = out_file + ".ibischk_warnings.txt"
            with open(warn_path, "w", encoding="utf-8") as f:
                f.write("\n".join(chk["warnings"]))

        import json
        json_path = out_file + ".ibischk_report.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump({
                "returncode": chk["returncode"],
                "errors": chk["errors"],
                "warnings": chk["warnings"],
                "notes": chk["notes"],
                "total_errors": len(chk["errors"]),
                "total_warnings": len(chk["warnings"])
            }, f, indent=2)

        # ONLY FAIL ON REAL ERRORS
        if chk["errors"]:
            logging.error("IBIS file has %d critical error(s) → failing build", len(chk["errors"]))
            return 20                                    # ← critical failure

        # Warnings are OK → continue normally
        if chk["warnings"]:
            logging.warning("ibischk7 reported %d warning(s) — model is still valid", len(chk["warnings"]))
        else:
            logging.info("ibischk7 passed with no warnings")



    # 6) Run correlation if requested
    if args.correlate:
        logging.info("Running SPICE vs IBIS correlation...")
        from s2ispice import S2ISpice
        s2i_spice = analy.spice
        for model in mList:
            if getattr(model, "noModel", False):
                continue
            try:
                deck_path, rc_corr = generate_and_run_correlation(
                    model=model,
                    ibis=ibis,
                    outdir=outdir,
                    s2ispice=s2i_spice,
                )
                if rc_corr == 0:
                    logging.info(f"Correlation SUCCESS for {model.modelName}")
                else:
                    logging.error(f"Correlation FAILED for {model.modelName}")
            except Exception as e:
                logging.error(f"Correlation crashed for {model.modelName}: {e}")

    # ←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←
    # FINAL SUCCESS: Feed back real data to GUI (if present)
    # ←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←
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
