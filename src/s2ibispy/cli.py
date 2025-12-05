#!/usr/bin/env python3
# cli.py — Packaged entrypoint (moved from main.py)
import argparse
import logging
import os
import sys
import subprocess
import shutil
from typing import Optional, Any
from pathlib import Path

from s2ibispy.s2ianaly import S2IAnaly
from s2ibispy.s2ioutput import IbisWriter as S2IOutput
from s2ibispy.s2i_to_yaml import convert_s2i_to_yaml

_YAML_IMPORT_ERROR = None
try:
    from s2ibispy.loader import load_yaml_config
    YAML_SUPPORT = True
except Exception as e:
    # Record the import error so we can explain later why a .yaml file was
    # treated as legacy .s2i. Previously we silently fell back which was
    # confusing to users.
    _YAML_IMPORT_ERROR = e
    YAML_SUPPORT = False

import re
from typing import Dict
import yaml

from s2ibispy.correlation import generate_and_run_correlation


def _validate_and_fix_paths(yaml_path: Path) -> None:
    """Validate and resolve model file and spice file paths (like GUI does)."""
    yaml_dir = yaml_path.parent.absolute()
    cwd = Path.cwd()
    
    def resolve_file_path(file_path: str, file_type: str) -> tuple[str, bool]:
        """Try to resolve a file path. Returns (resolved_path, was_modified)."""
        if not file_path:
            return None, False
        
        file_path_obj = Path(file_path)
        
        # Already absolute and exists
        if file_path_obj.is_absolute() and file_path_obj.exists():
            logging.debug(f"✓ {file_type}: {file_path}")
            return file_path, False
        
        # Try to resolve relative path
        search_dirs = [yaml_dir, cwd, yaml_dir.parent]
        
        for base_dir in search_dirs:
            test_path = base_dir / file_path
            if test_path.exists():
                resolved_path = str(test_path.absolute())
                logging.info(f"✓ Resolved {file_type}: {file_path} → {resolved_path}")
                return resolved_path, True
        
        logging.warning(f"⚠ {file_type} not found: {file_path}")
        return None, False
    
    # Load YAML
    try:
        with open(yaml_path, 'r') as f:
            data = yaml.safe_load(f)
    except Exception as e:
        logging.error(f"Failed to read YAML for path validation: {e}")
        return
    
    modified = False
    
    # Check model files
    models = data.get("models", [])
    for model in models:
        for field in ["modelFile", "modelFileMin", "modelFileMax"]:
            model_file = model.get(field, "")
            if model_file:
                resolved_path, was_resolved = resolve_file_path(model_file, f"Model {field}")
                if was_resolved and resolved_path:
                    model[field] = resolved_path
                    modified = True
    
    # Check spice files
    components = data.get("components", [])
    for comp in components:
        spice_file = comp.get("spiceFile", "")
        if spice_file:
            resolved_path, was_resolved = resolve_file_path(spice_file, "Spice file")
            if was_resolved and resolved_path:
                comp["spiceFile"] = resolved_path
                modified = True
    
    # Save if modified
    if modified:
        try:
            with open(yaml_path, 'w') as f:
                yaml.dump(data, f, default_flow_style=False, sort_keys=False)
            logging.info("Auto-saved YAML with resolved paths")
        except Exception as e:
            logging.error(f"Failed to save YAML with resolved paths: {e}")


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


def _copy_spice_libraries(src_dir: Path, out_dir: Path, referenced_files: list[str] | None = None) -> int:
    """Copy common SPICE library files from src_dir to out_dir.

    - Copies files with typical library extensions: .lib, .mod, .inc, .mdl, .scs
    - Also ensures explicitly referenced model files are copied regardless of extension
    - Non-recursive (only the same directory as the input file)
    Returns number of files copied.
    """
    try:
        src_dir = src_dir.resolve()
        out_dir = out_dir.resolve()
    except Exception:
        # Fall back to string-based join if resolve fails
        pass

    if src_dir == out_dir:
        logging.debug("Source and output directories are the same → skipping library copy")
        return 0

    out_dir.mkdir(parents=True, exist_ok=True)

    # Allow override via env var (comma-separated globs)
    env_exts = os.getenv("S2IBISPY_LIB_COPY_EXTS", "").strip()
    if env_exts:
        patterns = [p.strip() for p in env_exts.split(",") if p.strip()]
    else:
        # Default common SPICE library patterns (non-recursive)
        patterns = ["*.lib", "*.mod", "*.inc", "*.mdl", "*.scs"]

    copied = 0

    def _safe_copy(src: Path, dst_dir: Path) -> None:
        nonlocal copied
        try:
            dst = dst_dir / src.name
            if not dst.exists():
                shutil.copy2(src, dst)
                copied += 1
                logging.debug("Copied library: %s → %s", src, dst)
            else:
                # Optionally update if size or mtime differ
                try:
                    if src.stat().st_mtime > dst.stat().st_mtime or src.stat().st_size != dst.stat().st_size:
                        shutil.copy2(src, dst)
                        copied += 1
                        logging.debug("Updated library: %s → %s", src, dst)
                except Exception:
                    # If stat fails, just skip to be safe
                    pass
        except Exception as e:
            logging.warning("Failed to copy '%s': %s", src, e)

    # Copy by patterns
    try:
        for pat in patterns:
            for f in src_dir.glob(pat):
                if f.is_file():
                    _safe_copy(f, out_dir)
    except Exception as e:
        logging.debug("Pattern copy encountered an issue: %s", e)

    # Copy explicitly referenced files (e.g., modelFile/Min/Max)
    if referenced_files:
        for rf in referenced_files:
            if not rf:
                continue
            try:
                p = Path(rf)
                if not p.is_absolute():
                    p = (src_dir / rf).resolve()
                if p.exists() and p.is_file():
                    _safe_copy(p, out_dir)
            except Exception as e:
                logging.debug("Skip copy for referenced '%s': %s", rf, e)

    if copied:
        logging.info("Copied %d SPICE library file(s) to output directory", copied)
    else:
        logging.debug("No SPICE library files needed copying")
    return copied


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

    # -------------------------------------------------------------
    # Preflight simulator executable availability BEFORE any parsing
    # -------------------------------------------------------------
    import shutil
    default_prog_map = {"hspice": "hspice", "spectre": "spectre", "eldo": "eldo"}
    requested_prog = args.spice_cmd.strip() or default_prog_map.get(args.spice_type, "hspice")
    prog_display = requested_prog
    # If user passed a path, test existence; else rely on PATH lookup.
    missing = False
    if os.path.sep in requested_prog or requested_prog.startswith("."):
        # Treat as explicit path
        if not os.path.exists(requested_prog):
            missing = True
        else:
            # Optional: could test executable bit on POSIX; on Windows existence is fine.
            pass
    else:
        if shutil.which(requested_prog) is None:
            missing = True

    if missing:
        logging.error(
            "SPICE simulator '%s' not found. Aborting before conversion.\n"
            "Resolution: Install the simulator or pass --spice-cmd <full path>.\n"
            "Examples:\n  --spice-cmd C:/Apps/HSPICE/hspice.exe\n  --spice-cmd C:/Cadence/SPECTRE/bin/spectre\n",
            prog_display,
        )
        # Distinct non-zero code for 'simulator missing'
        return 11

    input_file = os.path.abspath(args.input)
    outdir = os.path.abspath(args.outdir)
    os.makedirs(outdir, exist_ok=True)

    input_path = Path(input_file)
    if not input_path.exists():
        logging.error("Input file not found: %s", input_file)
        return 2

    # Convert .s2i to YAML first (just like GUI does)
    if input_path.suffix.lower() == ".s2i":
        if not YAML_SUPPORT:
            logging.error(
                "YAML support required for .s2i conversion but is disabled: %s\n"
                "Please install pydantic: pip install pydantic",
                _YAML_IMPORT_ERROR
            )
            return 2
        
        logging.info("Converting .s2i to YAML: %s", input_path.name)
        yaml_path = input_path.with_suffix('.yaml')
        try:
            convert_s2i_to_yaml(input_path, yaml_path)
            logging.info("Converted to: %s", yaml_path.name)
            
            # Validate and resolve file paths (like GUI does)
            _validate_and_fix_paths(yaml_path)
            
            input_path = yaml_path
        except Exception as e:
            logging.error("Failed to convert .s2i to YAML: %s", e)
            return 2

    # Now load the YAML file (whether original or converted)
    if YAML_SUPPORT and input_path.suffix.lower() == ".yaml":
        logging.info("Loading YAML config: %s", input_path.name)
        try:
            ibis, global_, mList = load_yaml_config(input_path)
        except Exception as e:
            logging.error("Failed to load YAML: %s", e)
            return 2
    else:
        logging.error("Unsupported file format: %s (expected .yaml or .s2i)", input_path.suffix)
        return 2

    # Copy SPICE library files from the config's directory to outdir (non-recursive)
    try:
        ref_files = []
        try:
            # Collect referenced model files if available on model objects
            for m in (mList or []):
                for attr in ("modelFile", "modelFileMin", "modelFileMax"):
                    val = getattr(m, attr, None)
                    if val:
                        ref_files.append(str(val))
        except Exception:
            pass
        _copy_spice_libraries(input_path.parent, Path(outdir), ref_files)
    except Exception as e:
        logging.debug("Library copy step skipped due to error: %s", e)

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
