#!/usr/bin/env python3
# main.py — End-to-end driver: SPICE -> IBIS
import argparse
import logging
import os
import sys
#import shutil
import subprocess
from typing import Optional

from parser import S2IParser
from s2iutil import S2IUtil
from s2ianaly import S2IAnaly
#from s2ioutput import S2IOutput
from s2ioutput import IbisWriter as S2IOutput  # ← Alias!


def run_ibischk(ibis_file: str, ibischk: str) -> int:
    """Run ibischk if available; return the process return code."""
    try:
        logging.info("Running ibischk on %s", ibis_file)
        result = subprocess.run([ibischk, ibis_file], text=True)
        return result.returncode
    except FileNotFoundError:
        logging.warning("ibischk not found at '%s' — skipping.", ibischk)
        return 0

def main(argv: Optional[list[str]] = None) -> int:
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
        global_=global_,  # Pass global_ to S2IAnaly
        outdir=outdir,
    )
    rc = analy.run_all(ibis=ibis, global_=global_)
    if rc != 0:
        logging.error("Analysis failed with code %d", rc)
        return rc

    # 4) Write the .ibs
    out_file = os.path.join(outdir, os.path.splitext(os.path.basename(input_file))[0] + ".ibs")
    logging.info("Writing IBIS to %s", out_file)
    writer = S2IOutput(ibis_head=ibis)  # ← Pass ibis_head
    writer.write_ibis_file(str(out_file))  # ← Only filename

    # 5) Optionally run ibischk
    if args.ibischk:
        rc_chk = run_ibischk(str(out_file), args.ibischk)
        if rc_chk != 0:
            logging.warning("ibischk returned %d (see output above)", rc_chk)

    logging.info("Done.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
