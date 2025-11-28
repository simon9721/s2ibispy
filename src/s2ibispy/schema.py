# schema.py 
from __future__ import annotations
from dataclasses import dataclass, field
from enum import IntEnum
from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field, validator
from s2ibispy.models import (
    IbisTypMinMax, IbisComponent, IbisPin, IbisModel,
    IbisPinParasitics, IbisWaveTable
)
from s2ibispy.s2i_constants import ConstantStuff as CS


# Accept both int and str like "hspice"
class SpiceType(IntEnum):
    HSPICE = 0
    PSPICE = 1
    SPICE2 = 2
    SPICE3 = 3
    SPECTRE = 4
    ELDO = 5

    @classmethod
    def _missing_(cls, value):
        if isinstance(value, str):
            value = value.lower()
            mapping = {
                "hspice": cls.HSPICE,
                "pspice": cls.PSPICE,
                "spice2": cls.SPICE2,
                "spice3": cls.SPICE3,
                "spectre": cls.SPECTRE,
                "eldo": cls.ELDO,
            }
            return mapping.get(value, cls.HSPICE)
        return cls.HSPICE


@dataclass
class PinConfig:
    pinName: str
    signalName: str
    modelName: str
    R_pin: Optional[float] = None
    L_pin: Optional[float] = None
    C_pin: Optional[float] = None
    pullupRef: Optional[str] = None
    pulldownRef: Optional[str] = None
    powerClampRef: Optional[str] = None
    gndClampRef: Optional[str] = None
    inputPin: Optional[str] = None
    enablePin: Optional[str] = None


@dataclass
class ComponentConfig:
    component: str
    manufacturer: str = "Unknown"
    spiceFile: Optional[str] = None
    seriesSpiceFile: Optional[str] = None
    pinParasitics: Optional[IbisPinParasitics] = None
    pList: List[PinConfig] = field(default_factory=list)


class ModelConfig(BaseModel):
    name: str
    type: Literal[
        "Input", "Output", "I/O", "3-state",
        "Open_drain", "Open_sink", "Open_source",
        "I/O_Open_drain", "I/O_Open_sink", "I/O_Open_source",
        "Series", "Series_switch", "Terminator",
        "Input_ECL", "Output_ECL", "I/O_ECL"
    ] = "I/O"
    polarity: Literal["Non-Inverting", "Inverting"] = "Non-Inverting"
    enable: Optional[str] = None
    enable_polarity: Optional[str] = None  # "Active-High" or "Active-Low"
    nomodel: bool = False

    vinl: float = 0.8
    vinh: float = 2.0
    vmeas: Optional[float] = None
    cref: Optional[float] = None
    rref: Optional[float] = None
    vref: Optional[float] = None

    c_comp: IbisTypMinMax = Field(
        default_factory=lambda: IbisTypMinMax(typ=1.2e-12, min=1.0e-12, max=1.4e-12)
    )

    spice_file: Optional[str] = None
    modelFile: Optional[str] = None
    modelFileMin: Optional[str] = None
    modelFileMax: Optional[str] = None
    ext_spice_cmd_file: Optional[str] = None

    temp_range: Optional[IbisTypMinMax] = None
    voltage_range: Optional[IbisTypMinMax] = None
    pullup_ref: Optional[IbisTypMinMax] = None
    pulldown_ref: Optional[IbisTypMinMax] = None
    power_clamp_ref: Optional[IbisTypMinMax] = None
    gnd_clamp_ref: Optional[IbisTypMinMax] = None
    vil: Optional[IbisTypMinMax] = None
    vih: Optional[IbisTypMinMax] = None
    tr: Optional[IbisTypMinMax] = None
    tf: Optional[IbisTypMinMax] = None
    r_load: Optional[float] = None
    sim_time: Optional[float] = None
    derate_vi_pct: Optional[float] = None
    derate_ramp_pct: Optional[float] = None
    clamp_tol: Optional[float] = None

    rising_waveforms: List[Dict[str, Any]] = field(default_factory=list)
    falling_waveforms: List[Dict[str, Any]] = field(default_factory=list)

    enable_isso_tables: bool = False   # new flag


@dataclass
class GlobalDefaults:
    temp_range: IbisTypMinMax = field(default_factory=lambda: IbisTypMinMax(27, 100, 0))
    voltage_range: IbisTypMinMax = field(default_factory=lambda: IbisTypMinMax(3.3, 3.0, 3.6))
    pullup_ref: IbisTypMinMax = field(default_factory=lambda: IbisTypMinMax(3.3, 3.0, 3.6))
    pulldown_ref: IbisTypMinMax = field(default_factory=lambda: IbisTypMinMax(0, 0, 0))
    power_clamp_ref: IbisTypMinMax = field(default_factory=lambda: IbisTypMinMax(3.3, 3.0, 3.6))
    gnd_clamp_ref: IbisTypMinMax = field(default_factory=lambda: IbisTypMinMax(0, 0, 0))
    vil: IbisTypMinMax = field(default_factory=lambda: IbisTypMinMax(0.8, 0.7, 0.9))
    vih: IbisTypMinMax = field(default_factory=lambda: IbisTypMinMax(2.0, 1.8, 2.2))
    tr: IbisTypMinMax = field(default_factory=lambda: IbisTypMinMax(1e-9, 0.8e-9, 1.2e-9))
    tf: IbisTypMinMax = field(default_factory=lambda: IbisTypMinMax(1e-9, 0.8e-9, 1.2e-9))
    c_comp: IbisTypMinMax = field(default_factory=lambda: IbisTypMinMax(1.2e-12, 1.0e-12, 1.4e-12))
    r_load: float = 50.0
    sim_time: float = 10e-9
    derate_vi_pct: float = 0.0
    derate_ramp_pct: float = 0.0
    clamp_tol: float = 0.0
    pin_parasitics: IbisPinParasitics = field(default_factory=IbisPinParasitics)
    spice_file: Optional[str] = None


class ConfigSchema(BaseModel):
    ibis_version: Optional[str] = "3.2"
    file_name: Optional[str] = None
    file_rev: Optional[str] = "1.0"
    date: Optional[str] = None
    source: Optional[str] = None
    notes: Optional[str] = None
    disclaimer: Optional[str] = None
    copyright: Optional[str] = None

    spice_type: SpiceType = SpiceType.HSPICE  # accepts "hspice" or 0
    spice_command: Optional[str] = None
    iterate: int = 0
    cleanup: int = 0

    global_defaults: GlobalDefaults = field(default_factory=GlobalDefaults)
    components: List[ComponentConfig] = field(default_factory=list)
    models: List[ModelConfig] = field(default_factory=list)
