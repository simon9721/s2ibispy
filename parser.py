# parser.py
import re
#import sys
import os
from datetime import datetime
import logging
from typing import Tuple, List
from models import (
    IbisTOP, IbisGlobal, IbisComponent, IbisPin, IbisModel, IbisWaveTable,
    IbisDiffPin, IbisSeriesPin, IbisSeriesSwitchGroup, SeriesModel, IbisTypMinMax, IbisRamp, IbisPinParasitics
)
from s2i_constants import ConstantStuff as CS

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class S2IParser:
    def __init__(self):
        self.ibis = IbisTOP(
            ibisVersion="3.2",
            thisFileName="",
            fileRev="0",
            date=datetime.now().strftime("%A %b %d %Y %H:%M:%S"),
            source="",
            notes="",
            disclaimer="",
            copyright="",
            cList=[]
        )
        self.global_ = IbisGlobal(
            tempRange=IbisTypMinMax(),
            voltageRange=IbisTypMinMax(),
            pullupRef=IbisTypMinMax(),
            pulldownRef=IbisTypMinMax(),
            powerClampRef=IbisTypMinMax(),
            gndClampRef=IbisTypMinMax(),
            vil=IbisTypMinMax(),
            vih=IbisTypMinMax(),
            Rload=50.0,
            simTime=0.0,
            pinParasitics=IbisPinParasitics(
                R_pkg=IbisTypMinMax(),
                L_pkg=IbisTypMinMax(),
                C_pkg=IbisTypMinMax()
            )
        )

        self.pList: List[IbisPin] = []
        self.mList: List[IbisModel] = []
        self.risingWaveList: List[IbisWaveTable] = []
        self.fallingWaveList: List[IbisWaveTable] = []
        self.pmList: List[List[str]] = []
        self.dpList: List[IbisDiffPin] = []
        self.spList: List[IbisSeriesPin] = []
        self.ssgList: List[IbisSeriesSwitchGroup] = []

        self.tempPin = IbisPin()
        self.tempModel = IbisModel(modelName="", modelType="", risingWaveList=[], fallingWaveList=[])
        self.tempComponent = IbisComponent(component="", manufacturer="", pList=[])
        self.tempWaveTable = IbisWaveTable(waveData=[])
        self.tempDiffPin = IbisDiffPin(
            invPin="",
            vdiff=IbisTypMinMax(),
            tdelay_typ=0.0,
            tdelay_min=None,
            tdelay_max=None
        )
        self.tempSeriesPin = IbisSeriesPin(pin1="", pin2="", modelName="")
        self.tempSeriesSwitchGp = IbisSeriesSwitchGroup(pins=[])
        self.tempVdsList: List[float] = []

        self.compCount = 0
        self.modelCount = 0
        self.modelProc = False
        self.componentProc = False
        self.globalProc = False
        self.seriesMosfetMode = False
        self.pendingSeriesModel: SeriesModel | None = None

    # ---------------------------
    # Helpers for scope handling
    # ---------------------------
    def _scope_is_global(self) -> bool:
        return (not self.componentProc) and (not self.modelProc)

    def _apply_tmm(self, target, attr: str, args: str, line_num: int):
        setattr(target, attr, self.typ_min_max(args, line_num))

    def _apply_num(self, target, attr: str, args: str, line_num: int):
        setattr(target, attr, self.match_num(args, line_num))

    # ---------------------------

    def parse(self, in_file: str) -> Tuple[IbisTOP, IbisGlobal, List[IbisModel]]:
        # Read file with includes
        physical_lines = self._read_with_includes(in_file)

        file_name = os.path.basename(in_file).split(".")[0][:CS.MAX_FILENAME_BASE_LENGTH] + "." + CS.FILENAME_EXTENSION
        self.ibis.thisFileName = file_name
        self.ibis.date = datetime.now().strftime("%A %b %d %Y %H:%M:%S")
        logging.info(f"Parsing file: {self.ibis.thisFileName}")
        logging.info(f"Date: {self.ibis.date}")

        # Build logical lines: handle inline comments and '+' continuations
        logical_lines: List[Tuple[int, str]] = []
        carry = ""
        carry_line_num = None

        for idx, raw in enumerate(physical_lines, start=1):
            stripped = self._strip_inline_comment(raw).strip()
            if not stripped:
                continue

            if stripped.startswith('+'):
                # Continuation: append to previous logical line
                frag = stripped[1:].lstrip()
                if carry == "":
                    # No previous line to continue — treat as fresh (robustness)
                    carry = frag
                    carry_line_num = idx
                else:
                    carry += " " + frag
                continue

            # If we had a carried line, flush it before starting a new one
            if carry:
                logical_lines.append((carry_line_num, carry))
                carry, carry_line_num = "", None

            carry = stripped
            carry_line_num = idx

        if carry:
            logical_lines.append((carry_line_num, carry))

        # Main pass
        current_section = ""  # ← empty string = no section
        for line_num, line in logical_lines:
            m = re.match(r"\[(.*?)]\s*(.*)", line, re.IGNORECASE)
            if m:
                keyword, args = m.groups()
                self.process_key(keyword, args, line_num)
                current_section = keyword.lower()
            else:
                self.process_data(line, current_section, line_num)

        # Close any open component
        if self.componentProc:
            # Flip hasPinMapping if any pin carries explicit mapping refs
            if self.pList:
                self.tempComponent.hasPinMapping = (
                    self.tempComponent.hasPinMapping or any(
                        getattr(p, "pullupRef", "NC") != "NC"
                        or getattr(p, "pulldownRef", "NC") != "NC"
                        or getattr(p, "powerClampRef", "NC") != "NC"
                        or getattr(p, "gndClampRef", "NC") != "NC"
                        for p in self.pList
                    )
                )
            self.tempComponent.pList = self.pList
            self.tempComponent.pmList = self.pmList
            self.tempComponent.spList = self.spList
            self.tempComponent.ssgList = self.ssgList
            self.tempComponent.dpList = self.dpList
            self.ibis.cList.append(self.tempComponent)
            self.compCount += 1
            self.componentProc = False

        # Close any open model
        if self.modelProc:
            if self.pendingSeriesModel and self.tempModel.modelType in [str(CS.ModelType.SERIES), str(CS.ModelType.SERIES_SWITCH)]:
                self.tempModel.seriesModel = self.pendingSeriesModel
            self.mList.append(self.tempModel)
            self.modelCount += 1
            self.modelProc = False
            self.seriesMosfetMode = False
            self.pendingSeriesModel = None

        return self.ibis, self.global_, self.mList

    def process_key(self, key: str, args: str, line_num: int):
        key = key.lower()
        args = args.strip() if args else ""

        # ---------------------------
        # Header / global keywords
        # ---------------------------
        if key == "ibis ver":
            if self.compCount > 0 or self.modelCount > 0:
                logging.error(f"Line {line_num}: [IBIS Ver] must be first")
                return
            self.ibis.ibisVersion = args if args in ["1.1", "2.1", "3.2"] else "3.2"
            self.globalProc = True
            return

        if key == "file name":
            if args:
                # DOS-style name still allowed; just enforce overall length limit
                self.ibis.thisFileName = args[: CS.MAX_FILENAME_BASE_LENGTH + len(CS.FILENAME_EXTENSION) + 1]
            return

        if key == "file rev":
            self.ibis.fileRev = args[: CS.MAX_FILE_REV_LENGTH]
            return

        if key == "date":
            self.ibis.date = args or self.ibis.date
            return

        if key == "source":
            self.ibis.source = args[: CS.MAX_IBIS_STRING_LENGTH]
            return

        if key == "notes":
            self.ibis.notes = args[: CS.MAX_IBIS_STRING_LENGTH]
            return

        if key == "disclaimer":
            #self.ibis.disclaimer = args[: CS.MAX_IBIS_STRING_LENGTH]
            self.ibis.disclaimer += args + "\n"  # Append line
            return

        if key == "copyright":
            self.ibis.copyright = args[: CS.MAX_IBIS_STRING_LENGTH]
            return

        # parser.py  (inside process_key)
        if key == "spice type":
            types = {
                "hspice": CS.SpiceType.HSPICE,
                "pspice": CS.SpiceType.PSPICE,
                "spice2": CS.SpiceType.SPICE2,
                "spice3": CS.SpiceType.SPICE3,
                "spectre": CS.SpiceType.SPECTRE,
                "eldo": CS.SpiceType.ELDO,
            }
            self.ibis.spiceType = types.get(args.lower(), CS.SpiceType.HSPICE)
            return

        if key == "spice command":
            # Optional explicit simulator command
            self.ibis.spiceCommand = args
            return

        if key == "iterate":
            self.ibis.iterate = 1
            return

        if key == "cleanup":
            self.ibis.cleanup = 1
            return

        # ----------------------------------
        # Component start / close & headers
        # ----------------------------------
        if key == "component":
            self.globalProc = False
            if self.componentProc:
                # Flip hasPinMapping if any pin carries explicit refs
                if self.pList:
                    self.tempComponent.hasPinMapping = (
                        self.tempComponent.hasPinMapping or any(
                            getattr(p, "pullupRef", "NC") != "NC"
                            or getattr(p, "pulldownRef", "NC") != "NC"
                            or getattr(p, "powerClampRef", "NC") != "NC"
                            or getattr(p, "gndClampRef", "NC") != "NC"
                            for p in self.pList
                        )
                    )
                self.tempComponent.pList = self.pList
                self.tempComponent.pmList = self.pmList
                self.tempComponent.spList = self.spList
                self.tempComponent.ssgList = self.ssgList
                self.tempComponent.dpList = self.dpList
                self.ibis.cList.append(self.tempComponent)
                self.compCount += 1

            self.tempComponent = IbisComponent(component=args[: CS.MAX_COMPONENT_NAME_LENGTH], manufacturer="", pList=[])
            self.pList = []
            self.pmList = []
            self.spList = []
            self.ssgList = []
            self.dpList = []
            self.componentProc = True
            return

        # Scope-aware shared knobs (Header / Component / Model)
        # Temperature / Voltage ranges
        if key == "temperature range":
            if self.modelProc:
                self._apply_tmm(self.tempModel, "tempRange", args, line_num)
            elif self.componentProc:
                self._apply_tmm(self.tempComponent, "tempRange", args, line_num)
            else:
                self._apply_tmm(self.global_, "tempRange", args, line_num)
            return

        if key == "voltage range":
            if self.modelProc:
                self._apply_tmm(self.tempModel, "voltageRange", args, line_num)
            elif self.componentProc:
                self._apply_tmm(self.tempComponent, "voltageRange", args, line_num)
            else:
                self._apply_tmm(self.global_, "voltageRange", args, line_num)
            return

        # Supply references
        if key == "pullup reference":
            if self.modelProc:
                self._apply_tmm(self.tempModel, "pullupRef", args, line_num)
            elif self.componentProc:
                self._apply_tmm(self.tempComponent, "pullupRef", args, line_num)
            else:
                self._apply_tmm(self.global_, "pullupRef", args, line_num)
            return

        if key == "pulldown reference":
            if self.modelProc:
                self._apply_tmm(self.tempModel, "pulldownRef", args, line_num)
            elif self.componentProc:
                self._apply_tmm(self.tempComponent, "pulldownRef", args, line_num)
            else:
                self._apply_tmm(self.global_, "pulldownRef", args, line_num)
            return

        if key == "power clamp reference":
            if self.modelProc:
                self._apply_tmm(self.tempModel, "powerClampRef", args, line_num)
            elif self.componentProc:
                self._apply_tmm(self.tempComponent, "powerClampRef", args, line_num)
            else:
                self._apply_tmm(self.global_, "powerClampRef", args, line_num)
            return

        if key == "gnd clamp reference":
            if self.modelProc:
                self._apply_tmm(self.tempModel, "gndClampRef", args, line_num)
            elif self.componentProc:
                self._apply_tmm(self.tempComponent, "gndClampRef", args, line_num)
            else:
                self._apply_tmm(self.global_, "gndClampRef", args, line_num)
            return

        # Package parasitics (global / component)
        if key == "r_pkg":
            tgt = self.tempComponent if self.componentProc else self.global_
            self._apply_tmm(tgt.pinParasitics, "R_pkg", args, line_num)
            return

        if key == "l_pkg":
            tgt = self.tempComponent if self.componentProc else self.global_
            self._apply_tmm(tgt.pinParasitics, "L_pkg", args, line_num)
            return

        if key == "c_pkg":
            tgt = self.tempComponent if self.componentProc else self.global_
            self._apply_tmm(tgt.pinParasitics, "C_pkg", args, line_num)
            return

        # Stimulus & analysis knobs
        if key == "c_comp":
            if self.modelProc:
                self._apply_tmm(self.tempModel, "c_comp", args, line_num)
            elif self.componentProc:
                self._apply_tmm(self.tempComponent, "c_comp", args, line_num)
            else:
                self._apply_tmm(self.global_, "c_comp", args, line_num)
            return

        if key == "vil":
            if self.modelProc:
                self._apply_tmm(self.tempModel, "vil", args, line_num)
            elif self.componentProc:
                self._apply_tmm(self.tempComponent, "vil", args, line_num)
            else:
                self._apply_tmm(self.global_, "vil", args, line_num)
            return

        if key == "vih":
            if self.modelProc:
                self._apply_tmm(self.tempModel, "vih", args, line_num)
            elif self.componentProc:
                self._apply_tmm(self.tempComponent, "vih", args, line_num)
            else:
                self._apply_tmm(self.global_, "vih", args, line_num)
            return

        if key == "tr":
            if self.modelProc:
                self._apply_tmm(self.tempModel, "tr", args, line_num)
            elif self.componentProc:
                self._apply_tmm(self.tempComponent, "tr", args, line_num)
            else:
                self._apply_tmm(self.global_, "tr", args, line_num)
            return

        if key == "tf":
            if self.modelProc:
                self._apply_tmm(self.tempModel, "tf", args, line_num)
            elif self.componentProc:
                self._apply_tmm(self.tempComponent, "tf", args, line_num)
            else:
                self._apply_tmm(self.global_, "tf", args, line_num)
            return

        if key == "rload":
            if self.modelProc:
                self._apply_num(self.tempModel, "Rload", args, line_num)
            elif self.componentProc:
                self._apply_num(self.tempComponent, "Rload", args, line_num)
            else:
                self._apply_num(self.global_, "Rload", args, line_num)
            return

        if key == "sim time":
            if self.modelProc:
                self._apply_num(self.tempModel, "simTime", args, line_num)
            elif self.componentProc:
                self._apply_num(self.tempComponent, "simTime", args, line_num)
            else:
                self._apply_num(self.global_, "simTime", args, line_num)
            return

        if key == "clamp tolerance":
            if self.modelProc:
                self._apply_num(self.tempModel, "clampTol", args, line_num)
            elif self.componentProc:
                self._apply_num(self.tempComponent, "clampTol", args, line_num)
            else:
                self._apply_num(self.global_, "clampTol", args, line_num)
            return

        if key == "derate vi":
            val = self.match_num(args, line_num)
            if self.modelProc:
                self.tempModel.derateVIPct = val
            elif self.componentProc:
                self.tempComponent.derateVIPct = val
            else:
                self.global_.derateVIPct = val
            return

        if key == "derate ramp":
            val = self.match_num(args, line_num)
            if self.modelProc:
                self.tempModel.derateRampPct = val
            elif self.componentProc:
                self.tempComponent.derateRampPct = val
            else:
                self.global_.derateRampPct = val
            return

        # Component-only
        if key == "manufacturer" and self.componentProc:
            self.tempComponent.manufacturer = args[: CS.MAX_COMPONENT_NAME_LENGTH]
            return

        if key == "package model" and self.componentProc:
            if hasattr(self.tempComponent, "packageModel"):
                self.tempComponent.packageModel = args[: CS.MAX_PACKAGE_MODEL_NAME_LENGTH]
            return

        if key == "spice file" and self.componentProc:
            self.tempComponent.spiceFile = args
            return

        if key == "series spice file" and self.componentProc:
            if hasattr(self.tempComponent, "seriesSpiceFile"):
                self.tempComponent.seriesSpiceFile = args
            return

        # Section switches inside component
        if key == "pin" and self.componentProc:
            return

        if key == "diff pin" and self.componentProc:
            return

        if key == "series pin mapping" and self.componentProc:
            return

        if key == "pin mapping" and self.componentProc:
            self.tempComponent.hasPinMapping = True
            return

        if key == "series switch groups" and self.componentProc:
            return

        # ---------------------------
        # Model start / options
        # ---------------------------
        if key == "model":
            if self.modelProc:
                if self.pendingSeriesModel and self.tempModel.modelType in [str(CS.ModelType.SERIES), str(CS.ModelType.SERIES_SWITCH)]:
                    self.tempModel.seriesModel = self.pendingSeriesModel
                self.mList.append(self.tempModel)
                self.modelCount += 1
            self.tempModel = IbisModel(modelName=args[: CS.MAX_MODEL_NAME_LENGTH], modelType="", risingWaveList=[], fallingWaveList=[])
            self.risingWaveList = []
            self.fallingWaveList = []
            self.tempModel.risingWaveList = self.risingWaveList
            self.tempModel.fallingWaveList = self.fallingWaveList
            self.modelProc = True
            self.seriesMosfetMode = False
            return

        if key == "model type" and self.modelProc:
            low = args.strip().lower()
            # normalize separators to underscores
            low_norm = re.sub(r'[\s/+-]+', '_', low)  # "i/o open drain" -> "i_o_open_drain", "3-state"->"3_state"

            lookup = {
                "input": str(CS.ModelType.INPUT),
                "output": str(CS.ModelType.OUTPUT),
                "io": str(CS.ModelType.IO),
                "3_state": str(CS.ModelType.THREE_STATE),  # <- support 3-state
                "three_state": str(CS.ModelType.THREE_STATE),
                "open_drain": str(CS.ModelType.OPEN_DRAIN),
                "open_sink": str(CS.ModelType.OPEN_SINK),
                "open_source": str(CS.ModelType.OPEN_SOURCE),
                "io_open_drain": str(CS.ModelType.IO_OPEN_DRAIN),
                "i_o_open_drain": str(CS.ModelType.IO_OPEN_DRAIN),
                "io_open_sink": str(CS.ModelType.IO_OPEN_SINK),
                "i_o_open_sink": str(CS.ModelType.IO_OPEN_SINK),
                "io_open_source": str(CS.ModelType.IO_OPEN_SOURCE),
                "i_o_open_source": str(CS.ModelType.IO_OPEN_SOURCE),
                "terminator": str(CS.ModelType.TERMINATOR),
                "series": str(CS.ModelType.SERIES),
                "series_switch": str(CS.ModelType.SERIES_SWITCH),
                "input_ecl": str(CS.ModelType.INPUT_ECL),  # <- add
                "output_ecl": str(CS.ModelType.OUTPUT_ECL),
                "io_ecl": str(CS.ModelType.IO_ECL),
                "i_o_ecl": str(CS.ModelType.IO_ECL),
            }

            if low_norm.isdigit():
                self.tempModel.modelType = low_norm
            else:
                self.tempModel.modelType = lookup.get(low_norm, low_norm)
            # ADD THIS LINE
            if low_norm == "nomodel":
                self.tempModel.noModel = True
            if self.pendingSeriesModel and self.tempModel.modelType in [str(CS.ModelType.SERIES), str(CS.ModelType.SERIES_SWITCH)]:
                self.tempModel.seriesModel = self.pendingSeriesModel
                self.pendingSeriesModel = None
                self.seriesMosfetMode = False
            return

        if key == "polarity" and self.modelProc:
            self.tempModel.polarity = args.lower()
            return

        if key == "enable" and self.modelProc:
            self.tempModel.enable = args.lower()
            return

        if key == "nomodel" and self.modelProc:
            self.tempModel.modelType = "nomodel"
            self.tempModel.noModel = True  # ← ADD
            return

        if key == "vinl" and self.modelProc:
            self.tempModel.Vinl.typ = self.match_num(args, line_num)
            return

        if key == "vinh" and self.modelProc:
            self.tempModel.Vinh.typ = self.match_num(args, line_num)
            return

        if key == "vmeas" and self.modelProc:
            self.tempModel.Vmeas.typ = self.match_num(args, line_num)
            return

        if key == "cref" and self.modelProc:
            self.tempModel.Cref.typ = self.match_num(args, line_num)
            return

        if key == "rref" and self.modelProc:
            self.tempModel.Rref.typ = self.match_num(args, line_num)
            return

        if key == "vref" and self.modelProc:
            self.tempModel.Vref.typ = self.match_num(args, line_num)
            return

        # Terminator-only (we still store them; enforcement can happen later)
        if key == "rgnd" and self.modelProc:
            self._apply_tmm(self.tempModel, "Rgnd", args, line_num)
            return

        if key == "rpower" and self.modelProc:
            self._apply_tmm(self.tempModel, "Rpower", args, line_num)
            return

        if key == "rac" and self.modelProc:
            self._apply_tmm(self.tempModel, "Rac", args, line_num)
            return

        if key == "cac" and self.modelProc:
            self._apply_tmm(self.tempModel, "Cac", args, line_num)
            return

        if key == "model file" and self.modelProc:
            files = args.split()
            if files:
                self.tempModel.modelFile = files[0]
                if len(files) > 1:
                    self.tempModel.modelFileMin = files[1]
                if len(files) > 2:
                    self.tempModel.modelFileMax = files[2]
            return

        if key == "extspicecmd" and self.modelProc:
            self.tempModel.ext_spice_cmd_file = args
            return

        if key == "rising waveform" and self.modelProc:
            params = args.split()
            if len(params) >= 2:
                self.tempWaveTable = IbisWaveTable(
                    waveData=[],
                    size=0,
                    R_fixture=self.match_num(params[0], line_num),
                    V_fixture=self.match_num(params[1], line_num),
                    V_fixture_min=self.match_num(params[2], line_num) if len(params) > 2 else CS.USE_NA,
                    V_fixture_max=self.match_num(params[3], line_num) if len(params) > 3 else CS.USE_NA,
                    L_fixture=self.match_num(params[4], line_num) if len(params) > 4 else CS.USE_NA,
                    C_fixture=self.match_num(params[5], line_num) if len(params) > 5 else CS.USE_NA,
                    R_dut=self.match_num(params[6], line_num) if len(params) > 6 else CS.USE_NA,
                    L_dut=self.match_num(params[7], line_num) if len(params) > 7 else CS.USE_NA,
                    C_dut=self.match_num(params[8], line_num) if len(params) > 8 else CS.USE_NA
                )
                self.tempModel.risingWaveList.append(self.tempWaveTable)
            return

        if key == "falling waveform" and self.modelProc:
            params = args.split()
            if len(params) >= 2:
                self.tempWaveTable = IbisWaveTable(
                    waveData=[],
                    size=0,
                    R_fixture=self.match_num(params[0], line_num),
                    V_fixture=self.match_num(params[1], line_num),
                    V_fixture_min=self.match_num(params[2], line_num) if len(params) > 2 else CS.USE_NA,
                    V_fixture_max=self.match_num(params[3], line_num) if len(params) > 3 else CS.USE_NA,
                    L_fixture=self.match_num(params[4], line_num) if len(params) > 4 else CS.USE_NA,
                    C_fixture=self.match_num(params[5], line_num) if len(params) > 5 else CS.USE_NA,
                    R_dut=self.match_num(params[6], line_num) if len(params) > 6 else CS.USE_NA,
                    L_dut=self.match_num(params[7], line_num) if len(params) > 7 else CS.USE_NA,
                    C_dut=self.match_num(params[8], line_num) if len(params) > 8 else CS.USE_NA
                )
                self.tempModel.fallingWaveList.append(self.tempWaveTable)
            return

        # Series MOSFET / series switch blocks
        if key == "series mosfet":
            self.tempVdsList = []
            self.pendingSeriesModel = SeriesModel()
            self.seriesMosfetMode = True
            return

        if key == "vds" and self.seriesMosfetMode:
            if args:
                self.tempVdsList.append(self.match_num(args, line_num))
                if self.pendingSeriesModel:
                    self.pendingSeriesModel.vdslist = self.tempVdsList
            return

        if key == "on" and self.seriesMosfetMode:
            if self.pendingSeriesModel is None:
                self.pendingSeriesModel = SeriesModel()
            self.pendingSeriesModel.OnState = True
            return

        if key == "off" and self.seriesMosfetMode:
            if self.pendingSeriesModel is None:
                self.pendingSeriesModel = SeriesModel()
            self.pendingSeriesModel.OffState = True
            self.pendingSeriesModel.RSeriesOff = IbisTypMinMax(
                typ=CS.R_SERIES_DEFAULT, min=CS.R_SERIES_DEFAULT, max=CS.R_SERIES_DEFAULT
            )
            self.pendingSeriesModel.vdslist = self.tempVdsList
            self.seriesMosfetMode = False
            return

        if key == "r series" and self.seriesMosfetMode:
            if args:
                if self.pendingSeriesModel is None:
                    self.pendingSeriesModel = SeriesModel()
                self.pendingSeriesModel.RSeriesOff = self.typ_min_max(args, line_num)
            return

        logging.warning(f"Line {line_num}: Unhandled keyword: {key}")

    def process_data(self, line: str, current_section: str, line_num: int):
        if not line:
            return

        # [Pin] section — s2ibis3 format:
        # pin_name  spice_node  signal_name  model_name  [R_pin L_pin C_pin]
        # [pullupRef pulldownRef powerClampRef gndClampRef] [inputPin enablePin]
        # or on a following line:  "-> inputPin [enablePin]"
        if current_section == "pin":
            if line.startswith("->"):
                parts = line[2:].strip().split()
                if not self.pList:
                    logging.warning(f"Line {line_num}: '->' with no preceding pin")
                    return
                if len(parts) >= 1:
                    self.pList[-1].inputPin = parts[0][: CS.MAX_PIN_NAME_LENGTH]
                if len(parts) >= 2:
                    self.pList[-1].enablePin = parts[1][: CS.MAX_PIN_NAME_LENGTH]
                if len(parts) > 2:
                    logging.warning(f"Line {line_num}: extra tokens after enable pin ignored: {' '.join(parts[2:])}")
                return

            cols = line.split()
            if len(cols) < 4:
                logging.warning(f"Line {line_num}: Invalid [Pin] row, need at least 4 columns: {line}")
                return

            pin_name, spice_node, signal_name, model_name = cols[:4]
            idx = 4

            # Optional per-pin parasitics R/L/C
            r_pin = l_pin = c_pin = None
            if idx + 2 < len(cols):
                try:
                    r_pin = self.match_num(cols[idx], line_num)
                    l_pin = self.match_num(cols[idx + 1], line_num)
                    c_pin = self.match_num(cols[idx + 2], line_num)
                    idx += 3
                except Exception:
                    r_pin = l_pin = c_pin = None  # leave idx unchanged

            # Optional per-pin mapping refs (strings). Default "NC".
            pullupRef = pulldownRef = powerClampRef = gndClampRef = "NC"
            #pullupRef = pulldownRef = powerClampRef = gndClampRef = IbisTypMinMax()  # ← TMM, not string
            if idx + 3 < len(cols):
                pullupRef, pulldownRef, powerClampRef, gndClampRef = (
                    cols[idx], cols[idx + 1], cols[idx + 2], cols[idx + 3]
                )
                idx += 4

            # Optional inline input/enable after refs (input then enable)
            inputPin = cols[idx][: CS.MAX_PIN_NAME_LENGTH] if idx < len(cols) else ""
            idx += 1 if idx < len(cols) else 0
            enablePin = cols[idx][: CS.MAX_PIN_NAME_LENGTH] if idx < len(cols) else ""

            # Build the pin ONCE
            self.tempPin = IbisPin(
                pinName=pin_name[: CS.MAX_PIN_NAME_LENGTH],
                signalName=signal_name[: CS.MAX_SIGNAL_NAME_LENGTH],
                modelName=model_name[: CS.MAX_MODEL_NAME_LENGTH],
                model=None,
            )
            if hasattr(self.tempPin, "spiceNodeName"):
                self.tempPin.spiceNodeName = spice_node

            # Optional R/L/C
            if (r_pin is not None) and hasattr(self.tempPin, "R_pin"):
                self.tempPin.R_pin = r_pin
                if hasattr(self.tempPin, "L_pin"):
                    self.tempPin.L_pin = l_pin if l_pin is not None else CS.NOT_USED
                if hasattr(self.tempPin, "C_pin"):
                    self.tempPin.C_pin = c_pin if c_pin is not None else CS.NOT_USED

            # Optional mapping refs (requires fields added in models.IbisPin)
            if hasattr(self.tempPin, "pullupRef"):     self.tempPin.pullupRef = pullupRef
            if hasattr(self.tempPin, "pulldownRef"):   self.tempPin.pulldownRef = pulldownRef
            if hasattr(self.tempPin, "powerClampRef"): self.tempPin.powerClampRef = powerClampRef
            if hasattr(self.tempPin, "gndClampRef"):   self.tempPin.gndClampRef = gndClampRef

            # Optional inline input/enable
            if inputPin:  self.tempPin.inputPin = inputPin
            if enablePin: self.tempPin.enablePin = enablePin

            self.pList.append(self.tempPin)
            return

        # [Diff pin] — 4 or 6 columns:
        # pin_name inv_pin vdiff tdelay_typ  [tdelay_min tdelay_max]
        elif current_section == "diff pin":
            cols = line.split()
            if len(cols) not in (4, 6):
                logging.warning(f"Line {line_num}: Invalid [Diff pin] row (need 4 or 6 cols): {line}")
                return

            pin_name = cols[0][: CS.MAX_PIN_NAME_LENGTH]
            inv_pin = cols[1][: CS.MAX_PIN_NAME_LENGTH]
            vdiff = self.typ_min_max(cols[2], line_num)  # allow single or tmm
            tdelay_typ = self.match_num(cols[3], line_num)
            tdelay_min = tdelay_max = CS.USE_NA
            if len(cols) == 6:
                tdelay_min = self.match_num(cols[4], line_num)
                tdelay_max = self.match_num(cols[5], line_num)

            self.tempDiffPin = IbisDiffPin(
                pinName=pin_name,
                invPin=inv_pin,
                vdiff=vdiff,
                tdelay_typ=tdelay_typ,
                tdelay_min=tdelay_min if tdelay_min != CS.USE_NA else None,
                tdelay_max=tdelay_max if tdelay_max != CS.USE_NA else None
            )
            if hasattr(self.tempDiffPin, "pinName"):
                self.tempDiffPin.pinName = pin_name

            self.dpList.append(self.tempDiffPin)

        # [Series Pin Mapping] — 3 or 4 columns:
        # pin_1 pin_2 model_name [function_table_group]
        elif current_section == "series pin mapping":
            cols = line.split()
            if len(cols) not in (3, 4):
                logging.warning(f"Line {line_num}: Invalid [Series Pin Mapping] row: {line}")
                return
            self.tempSeriesPin = IbisSeriesPin(
                pin1=cols[0][: CS.MAX_PIN_NAME_LENGTH],
                pin2=cols[1][: CS.MAX_PIN_NAME_LENGTH],
                modelName=cols[2][: CS.MAX_MODEL_NAME_LENGTH]
            )
            if len(cols) == 4 and hasattr(self.tempSeriesPin, "fnTableGp"):
                self.tempSeriesPin.fnTableGp = cols[3][: CS.MAX_PIN_MAPPING_NAME_LENGTH]
            self.spList.append(self.tempSeriesPin)

        # [Pin Mapping] — 3 or 5 columns (we just store the tokens)
        elif current_section == "pin mapping":
            cols = line.split()
            if len(cols) in (3, 5):
                self.pmList.append(cols)
            else:
                logging.warning(f"Line {line_num}: Invalid [Pin Mapping] row: {line}")

        # [Series Switch Groups] — free-form names on each line
        elif current_section == "series switch groups":
            names = line.split()
            if names:
                self.tempSeriesSwitchGp = IbisSeriesSwitchGroup(pins=names)
                self.ssgList.append(self.tempSeriesSwitchGp)
            else:
                logging.warning(f"Line {line_num}: Invalid series switch group data: {line}")

    def typ_min_max(self, args: str, line_num: int) -> IbisTypMinMax:
        tokens = args.split()
        tmm = IbisTypMinMax()
        if len(tokens) > 0:
            tmm.typ = self.match_num(tokens[0], line_num)
        if len(tokens) > 1:
            tmm.min = self.match_num(tokens[1], line_num)
        if len(tokens) > 2:
            tmm.max = self.match_num(tokens[2], line_num)
        return tmm

    def match_num(self, s: str, line_num: int) -> float:
        text = s.strip()
        if not text:
            logging.error(f"Line {line_num}: empty numeric field")
            raise ValueError("empty number")

        # NA / NaN handling
        if text.upper() in {"NA", "N/A", "NAN"}:
            return CS.USE_NA

        text = re.sub(r'\s*(ohms?|Ω|[Vv]|[Hh]|[Ff]|[Ss]|[Aa]|[Hh][Zz])\s*$', '', text)

        # SI-suffixed float (single-letter SI before any unit we stripped)
        m = re.match(
            r'^\s*([+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?)([TGMkmunpfa])?\s*$',
            text
        )
        if m:
            base = float(m.group(1))
            suffix = m.group(2)
            if not suffix:
                return base
            scale = {"T": 1e12, "G": 1e9, "M": 1e6, "k": 1e3, "m": 1e-3,
                     "u": 1e-6, "n": 1e-9, "p": 1e-12, "f": 1e-15, "a": 1e-18}[suffix]
            return base * scale

        # Fallback
        try:
            return float(text)
        except ValueError:
            logging.error(f"Line {line_num}: Invalid number format: {s}")
            raise

    def _strip_inline_comment(self, line: str) -> str:
        # Strip anything after the first '|' (IBIS uses '|' for comments)
        return line.split('|', 1)[0].rstrip()

    def _read_with_includes(self, path: str, seen=None) -> List[str]:
        """
        Read file with simple [Include] support. Returns a flat list of raw lines.
        Prevent recursive include loops via 'seen'.
        """
        if seen is None:
            seen = set()
        apath = os.path.abspath(path)
        if apath in seen:
            logging.warning(f"Include loop detected, skipping: {path}")
            return []
        seen.add(apath)

        try:
            with open(apath, 'r') as f:
                raw = f.readlines()
        except FileNotFoundError:
            logging.error(f"Include not found: {path}")
            return []

        out: List[str] = []
        base_dir = os.path.dirname(apath)
        for raw_line in raw:
            line = raw_line.rstrip('\r\n')
            # Detect section header of [Include] <relative/or/absolute/path>
            m = re.match(r'^\s*\[(?i:include)]\s*(.+)?$', line)
            if m:
                inc_arg = (m.group(1) or '').strip()
                if inc_arg:
                    inc_path = inc_arg if os.path.isabs(inc_arg) else os.path.join(base_dir, inc_arg)
                    out.extend(self._read_with_includes(inc_path, seen))
                else:
                    logging.warning(f"[Include] without path ignored in {path}")
                continue
            out.append(line)
        return out
