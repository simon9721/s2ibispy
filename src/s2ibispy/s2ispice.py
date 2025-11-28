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
