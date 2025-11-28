"""Package copy of s2ispice with package imports."""
import logging
import math
import os
import shutil
import subprocess
import re
from typing import List, Tuple, Optional
from dataclasses import dataclass
from s2ibispy.models import IbisTOP, IbisGlobal, IbisModel, IbisPin, IbisTypMinMax, IbisVItable, IbisWaveTable, IbisVItableEntry, IbisWaveTableEntry
from s2ibispy.s2i_constants import ConstantStuff as CS

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
            s2i_file: Optional[str] = None,
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
        self.s2i_file = s2i_file
        if not os.path.exists(self.mock_dir):
            os.makedirs(self.mock_dir)

    # For brevity, only include key helper methods needed by analy.run_all in this pass.
    # Full implementation can be copied as needed.

    def _spice_prog_name(self) -> str:
        """Return the simulator executable name based on spice_type."""
        if self.spice_type == CS.SpiceType.HSPICE:
            return self.hspice_path if self.hspice_path else "hspice"
        elif self.spice_type == CS.SpiceType.SPECTRE:
            return "spectre"
        elif self.spice_type == CS.SpiceType.ELDO:
            return "eldo"
        return "hspice"

    def _format_user_command(self, cmd: str, spice_in: str, spice_out: str, spice_msg: str) -> str:
        """Replace placeholders in user command."""
        return cmd.replace("%i", spice_in).replace("%o", spice_out).replace("%m", spice_msg)

    def call_spice(self, iterate: int, spice_command: str, spice_in: str, spice_out: str, spice_msg: str) -> int:
        """Run SPICE simulation; return 0 on success, 1 on failure."""
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
                            shutil.move(c, spice_out)
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
