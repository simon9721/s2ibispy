# models.py
import math
from dataclasses import dataclass, field
from typing import List, Optional, Union
from s2i_constants import ConstantStuff as CS


@dataclass
class IbisTypMinMax:
    typ: float = float('nan')
    min: float = float('nan')
    max: float = float('nan')


# Factory function
def tmm_factory():
    return IbisTypMinMax()

@dataclass
class IbisPinParasitics:
    R_pkg: IbisTypMinMax = field(default_factory=tmm_factory)
    L_pkg: IbisTypMinMax = field(default_factory=tmm_factory)
    C_pkg: IbisTypMinMax = field(default_factory=tmm_factory)


@dataclass
class IbisVItableEntry:
    v: float = 0.0
    i: IbisTypMinMax = field(default_factory=IbisTypMinMax)


@dataclass
class IbisVItable:
    VIs: List[IbisVItableEntry] = field(default_factory=list)
    size: int = 0

    def add_point(self, v: float, i_typ: Optional[float] = None, i_min: Optional[float] = None, i_max: Optional[float] = None) -> None:
        entry = IbisVItableEntry(v=v)
        if i_typ is not None:
            entry.i.typ = i_typ
        if i_min is not None:
            entry.i.min = i_min
        if i_max is not None:
            entry.i.max = i_max
        self.VIs.append(entry)

    def finalize_size(self) -> None:
        self.size = len(self.VIs)


@dataclass
class IbisWaveTableEntry:
    t: float = 0.0
    v: IbisTypMinMax = field(default_factory=IbisTypMinMax)


@dataclass
class IbisWaveTable:
    waveData: List[IbisWaveTableEntry] = field(default_factory=list)
    size: int = 0
    R_fixture: float = 0.0
    V_fixture: float = 0.0
    V_fixture_min: float = float('nan')
    V_fixture_max: float = float('nan')
    L_dut: float = float('nan')
    R_dut: float = float('nan')
    C_dut: float = float('nan')
    L_fixture: float = float('nan')
    C_fixture: float = float('nan')

    def add_point(self, t: float, v_typ: Optional[float] = None, v_min: Optional[float] = None, v_max: Optional[float] = None) -> None:
        entry = IbisWaveTableEntry(t=t)
        if v_typ is not None:
            entry.v.typ = v_typ
        if v_min is not None:
            entry.v.min = v_min
        if v_max is not None:
            entry.v.max = v_max
        self.waveData.append(entry)

    def finalize_size(self) -> None:
        self.size = len(self.waveData)


@dataclass
class IbisRamp:
    dv_r: IbisTypMinMax = field(default_factory=IbisTypMinMax)
    dt_r: IbisTypMinMax = field(default_factory=IbisTypMinMax)
    dv_f: IbisTypMinMax = field(default_factory=IbisTypMinMax)
    dt_f: IbisTypMinMax = field(default_factory=IbisTypMinMax)
    derateRampPct: float = 0.0


@dataclass
class SeriesModel:
    OnState: bool = False
    OffState: bool = True
    RSeriesOff: IbisTypMinMax = field(default_factory=lambda: IbisTypMinMax(CS.R_SERIES_DEFAULT, CS.R_SERIES_DEFAULT, CS.R_SERIES_DEFAULT))
    vdslist: List[float] = field(default_factory=list)


@dataclass
class IbisDiffPin:
    pinName: str = ""
    invPin: str = ""
    vdiff: IbisTypMinMax = field(default_factory=IbisTypMinMax)  # typ/min/max
    tdelay_typ: float = 0.0
    tdelay_min: Optional[float] = None
    tdelay_max: Optional[float] = None


@dataclass
class IbisSeriesPin:
    pin1: str = ""
    pin2: str = ""
    modelName: str = ""
    fnTableGp: str = ""               # optional function_table_group (manual)


@dataclass
class IbisSeriesSwitchGroup:
    pins: List[str] = field(default_factory=list)


@dataclass
class IbisModel:
    modelName: str = ""
    modelType: Union[CS.ModelType, int, str] = ""  # normalize in __post_init__
    noModel: int = 0  # ← ADD THIS LINE
    polarity: Union[int, str] = CS.MODEL_POLARITY_NON_INVERTING
    enable: Union[int, str] = CS.MODEL_ENABLE_ACTIVE_LOW

    # Model file references and external SPICE setup
    modelFile: str = ""
    modelFileMin: str = ""
    modelFileMax: str = ""
    spice_file: str = ""
    ext_spice_cmd_file: str = ""

    # Stimulus thresholds/timing — now IbisTypMinMax for IBIS compatibility
    Vinl: IbisTypMinMax = field(default_factory=lambda: IbisTypMinMax(CS.USE_NA, CS.USE_NA, CS.USE_NA))
    Vinh: IbisTypMinMax = field(default_factory=lambda: IbisTypMinMax(CS.USE_NA, CS.USE_NA, CS.USE_NA))
    Vmeas: IbisTypMinMax = field(default_factory=lambda: IbisTypMinMax(CS.USE_NA, CS.USE_NA, CS.USE_NA))
    Cref: IbisTypMinMax = field(default_factory=lambda: IbisTypMinMax(CS.USE_NA, CS.USE_NA, CS.USE_NA))
    Rref: IbisTypMinMax = field(default_factory=lambda: IbisTypMinMax(CS.USE_NA, CS.USE_NA, CS.USE_NA))
    Vref: IbisTypMinMax = field(default_factory=lambda: IbisTypMinMax(CS.USE_NA, CS.USE_NA, CS.USE_NA))

    # IBIS-style TMM fields (allow overrides at model scope)
    vil: IbisTypMinMax = field(default_factory=IbisTypMinMax)
    vih: IbisTypMinMax = field(default_factory=IbisTypMinMax)
    tr: IbisTypMinMax = field(default_factory=IbisTypMinMax)
    tf: IbisTypMinMax = field(default_factory=IbisTypMinMax)

    # Analysis knobs
    simTime: float = 0.0
    Rload: float = 0.0
    #c_comp: IbisTypMinMax = field(default_factory=IbisTypMinMax)
    c_comp: IbisTypMinMax = field(
        default_factory=lambda: IbisTypMinMax(typ=5.0e-12, min=5.0e-12, max=5.0e-12)
    )
    clampTol: float = 0.0
    derateVIPct: float = 0.0
    derateRampPct: float = 0.0

    # Terminator-only (present for completeness; enforce validity elsewhere)
    Rgnd: IbisTypMinMax = field(default_factory=IbisTypMinMax)
    Rpower: IbisTypMinMax = field(default_factory=IbisTypMinMax)
    Rac: IbisTypMinMax = field(default_factory=IbisTypMinMax)
    Cac: IbisTypMinMax = field(default_factory=IbisTypMinMax)

    # Data / results
    #ramp: Optional[IbisRamp] = None
    ramp: IbisRamp = field(default_factory=IbisRamp)  # ← CORRECT
    pullupData: Optional[IbisVItable] = None
    pulldownData: Optional[IbisVItable] = None
    powerClampData: Optional[IbisVItable] = None
    gndClampData: Optional[IbisVItable] = None

    # --- NEW: final (IBIS-ready) tables after sorting/normalization ---
    pullup: Optional[IbisVItable] = None
    pulldown: Optional[IbisVItable] = None
    power_clamp: Optional[IbisVItable] = None
    gnd_clamp: Optional[IbisVItable] = None

    risingWaveList: List[IbisWaveTable] = field(default_factory=list)
    fallingWaveList: List[IbisWaveTable] = field(default_factory=list)
    seriesModel: Optional[SeriesModel] = None
    seriesVITables: List[IbisVItable] = field(default_factory=list)

    # Scope overrides
    tempRange: IbisTypMinMax = field(default_factory=IbisTypMinMax)
    voltageRange: IbisTypMinMax = field(default_factory=IbisTypMinMax)
    pullupRef: IbisTypMinMax = field(default_factory=IbisTypMinMax)
    pulldownRef: IbisTypMinMax = field(default_factory=IbisTypMinMax)
    powerClampRef: IbisTypMinMax = field(default_factory=IbisTypMinMax)
    gndClampRef: IbisTypMinMax = field(default_factory=IbisTypMinMax)

    # in class IbisModel (near other *Data fields)
    pullupDisabledData: Optional[IbisVItable] = None
    pulldownDisabledData: Optional[IbisVItable] = None

    hasBeenAnalyzed: int = 0

    @staticmethod
    def _map_polarity_string(s: str) -> int:
        s = s.strip().lower()
        if s in ("inverting", "invert", "inv"):
            return CS.MODEL_POLARITY_INVERTING
        if s in ("non_inverting", "non-inverting", "noninv", "noninvert", "non inverting"):
            return CS.MODEL_POLARITY_NON_INVERTING
        # default
        return CS.MODEL_POLARITY_NON_INVERTING

    @staticmethod
    def _map_enable_string(s: str) -> int:
        s = s.strip().lower()
        if s in ("active_low", "active-low", "low", "al"):
            return CS.MODEL_ENABLE_ACTIVE_LOW
        if s in ("active_high", "active-high", "high", "ah"):
            return CS.MODEL_ENABLE_ACTIVE_HIGH
        # default
        return CS.MODEL_ENABLE_ACTIVE_LOW

    # Optional: if you want non-digit string names for modelType supported too

    @staticmethod
    def _map_modeltype_string(s: str):
        s = s.strip().lower()
        # extend as needed
        mapping = {
            "open_drain": CS.ModelType.OPEN_DRAIN,
            "open_sink": CS.ModelType.OPEN_DRAIN,
            "io_open_drain": CS.ModelType.IO_OPEN_DRAIN,
            "io_open_sink": CS.ModelType.IO_OPEN_SINK,
            "open_source": CS.ModelType.OPEN_SOURCE,
            "io_open_source": CS.ModelType.IO_OPEN_SOURCE,
            "ecl": CS.ModelType.OUTPUT_ECL,
            "io_ecl": CS.ModelType.IO_ECL,
            "input": CS.ModelType.INPUT,
            "output": CS.ModelType.OUTPUT,
            "i/o": CS.ModelType.I_O,  # if present in your enum
        }
        return mapping.get(s)

    def __post_init__(self):
        # Normalize modelType to CS.ModelType where possible
        if isinstance(self.modelType, str):
            if self.modelType.isdigit():
                try:
                    self.modelType = CS.ModelType(int(self.modelType))
                except ValueError:
                    pass
        elif isinstance(self.modelType, int):
            try:
                self.modelType = CS.ModelType(self.modelType)
            except ValueError:
                pass
            # --- NEW: normalize polarity to int constants ---
        if isinstance(self.polarity, str):
            self.polarity = self._map_polarity_string(self.polarity)

            # --- NEW: normalize enable to int constants ---
        if isinstance(self.enable, str):
            self.enable = self._map_enable_string(self.enable)

        # Ensure lists are always present
        if self.risingWaveList is None:
            self.risingWaveList = []
        if self.fallingWaveList is None:
            self.fallingWaveList = []
        if self.seriesVITables is None:
            self.seriesVITables = []

        # Ensure ramp exists so code can rely on it
        #if self.ramp is None:
        #    self.ramp = IbisRamp()

        # Normalize scalar inputs to .typ only
        for field in ['Vinl', 'Vinh', 'Vmeas', 'Cref', 'Rref', 'Vref']:
            val = getattr(self, field)
            if isinstance(val, (int, float)) and not math.isnan(val):
                getattr(self, field).typ = val

    def is_open_drain_family(self) -> bool:
        try:
            mt = self.modelType if isinstance(self.modelType, CS.ModelType) else CS.ModelType(self.modelType)
        except Exception:
            return False
        return mt in (CS.ModelType.OPEN_DRAIN, CS.ModelType.OPEN_SINK, CS.ModelType.IO_OPEN_DRAIN, CS.ModelType.IO_OPEN_SINK)

    def is_open_source_family(self) -> bool:
        try:
            mt = self.modelType if isinstance(self.modelType, CS.ModelType) else CS.ModelType(self.modelType)
        except Exception:
            return False
        return mt in (CS.ModelType.OPEN_SOURCE, CS.ModelType.IO_OPEN_SOURCE)


@dataclass
class IbisPin:
    pinName: str = ""
    signalName: str = ""
    modelName: str = ""
    model: Optional[IbisModel] = None
    pParasitics: Optional[IbisPinParasitics] = None
    enablePin: str = ""
    inputPin: str = ""
    spiceNodeName: str = ""
    seriesPin2name: str = ""

    # --- NEW: pin-map references used by findSupplyPins ---
    pullupRef: str = "NC"
    pulldownRef: str = "NC"
    powerClampRef: str = "NC"
    gndClampRef: str = "NC"

    # Per-pin parasitics from [Pin] optional cols (manual)
    R_pin: float = CS.NOT_USED
    L_pin: float = CS.NOT_USED
    C_pin: float = CS.NOT_USED


@dataclass
class IbisComponent:
    component: str = ""
    manufacturer: str = ""
    spiceFile: str = ""
    seriesSpiceFile: str = ""
    hasPinMapping: bool = False

    # Scope overrides available at component level (manual)
    tempRange: IbisTypMinMax = field(default_factory=IbisTypMinMax)
    voltageRange: IbisTypMinMax = field(default_factory=IbisTypMinMax)
    pullupRef: IbisTypMinMax = field(default_factory=IbisTypMinMax)
    pulldownRef: IbisTypMinMax = field(default_factory=IbisTypMinMax)
    powerClampRef: IbisTypMinMax = field(default_factory=IbisTypMinMax)
    gndClampRef: IbisTypMinMax = field(default_factory=IbisTypMinMax)
    vil: IbisTypMinMax = field(default_factory=IbisTypMinMax)
    vih: IbisTypMinMax = field(default_factory=IbisTypMinMax)
    tr: IbisTypMinMax = field(default_factory=IbisTypMinMax)
    tf: IbisTypMinMax = field(default_factory=IbisTypMinMax)
    c_comp: IbisTypMinMax = field(default_factory=IbisTypMinMax)
    Rload: float = 0.0
    simTime: float = 0.0
    derateVIPct: float = 0.0
    derateRampPct: float = 0.0
    clampTol: float = 0.0
    #pinParasitics: IbisPinParasitics = field(default_factory=IbisPinParasitics)
    pinParasitics: Optional[IbisPinParasitics] = None

    # Collections
    pList: List[IbisPin] = field(default_factory=list)
    pmList: List[List[str]] = field(default_factory=list)
    dpList: List[IbisDiffPin] = field(default_factory=list)
    spList: List[IbisSeriesPin] = field(default_factory=list)
    ssgList: List[IbisSeriesSwitchGroup] = field(default_factory=list)


@dataclass
class IbisGlobal:
    tempRange: IbisTypMinMax = field(default_factory=IbisTypMinMax)
    voltageRange: IbisTypMinMax = field(default_factory=IbisTypMinMax)
    pullupRef: IbisTypMinMax = field(default_factory=IbisTypMinMax)
    pulldownRef: IbisTypMinMax = field(default_factory=IbisTypMinMax)
    powerClampRef: IbisTypMinMax = field(default_factory=IbisTypMinMax)
    gndClampRef: IbisTypMinMax = field(default_factory=IbisTypMinMax)
    vil: IbisTypMinMax = field(default_factory=IbisTypMinMax)
    vih: IbisTypMinMax = field(default_factory=IbisTypMinMax)
    Rload: float = 50.0
    simTime: float = 0.0
    pinParasitics: IbisPinParasitics = field(default_factory=IbisPinParasitics)
    tr: IbisTypMinMax = field(default_factory=IbisTypMinMax)
    tf: IbisTypMinMax = field(default_factory=IbisTypMinMax)
    c_comp: IbisTypMinMax = field(default_factory=IbisTypMinMax)
    derateVIPct: float = 0.0
    derateRampPct: float = 0.0
    clampTol: float = 0.0
    commentChar: str = "|"


@dataclass
class IbisTOP:
    ibisVersion: str = ""
    thisFileName: str = ""
    fileRev: str = ""
    date: str = ""
    source: str = ""
    notes: str = ""
    disclaimer: str = ""
    copyright: str = ""
    cList: List[IbisComponent] = field(default_factory=list)
    mList: List[IbisModel] = field(default_factory=list)  # ← ADD THIS LINE
    spiceType: int = CS.SpiceType.HSPICE
    cleanup: int = 0
    iterate: int = 0
    summarize: int = 0
    spiceCommand: str = ""

    def __post_init__(self):
        self.thisFileName = str(self.thisFileName or "buffer.ibs")
        self.fileRev = str(self.fileRev or "0")
        self.ibisVersion = str(self.ibisVersion or "3.2")
        self.date = str(self.date or "Unknown")

@dataclass
class IbisPinMap:
    pinName: str = ""
    pulldownRef: str = ""
    pullupRef: str = ""
    gndClampRef: str = ""
    powerClampRef: str = ""

@dataclass
class seriesSwitchGroup:
    state: str = ""
    groupNames: List[str] = field(default_factory=list)

