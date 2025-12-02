"""Package loader to load YAML configs into package models."""
import yaml
import logging
from pathlib import Path
from datetime import datetime
from s2ibispy.schema import ConfigSchema, GlobalDefaults
from s2ibispy.models import (
    IbisTOP, IbisGlobal, IbisModel, IbisComponent, IbisPin,
    IbisTypMinMax, IbisPinParasitics, IbisWaveTable
)
from s2ibispy.s2i_constants import ConstantStuff as CS


def _to_tmm(val) -> IbisTypMinMax:
    if isinstance(val, dict):
        return IbisTypMinMax(
            typ=val.get("typ", float("nan")),
            min=val.get("min", float("nan")),
            max=val.get("max", float("nan")),
        )
    elif isinstance(val, (int, float)):
        return IbisTypMinMax(typ=float(val))
    return IbisTypMinMax()


def load_yaml_config(path: str | Path) -> tuple[IbisTOP, IbisGlobal, list[IbisModel]]:
    path = Path(path)
    raw = yaml.safe_load(path.read_text())
    config = ConfigSchema(**raw)

    ibis = IbisTOP(
        ibisVersion=config.ibis_version or "3.2",
        thisFileName=config.file_name or path.with_suffix(".ibs").name,
        fileRev=config.file_rev or "1.0",
        date=config.date or datetime.now().strftime("A %b %d %Y %H:%M:%S"),
        source=config.source or "",
        notes=config.notes or "",
        disclaimer=config.disclaimer or "",
        copyright=config.copyright or "",
        cList=[],
        mList=[],
        spiceType=getattr(config, 'spice_type', None) and getattr(config.spice_type,'value', None) or 0,
        spiceCommand=config.spice_command or "",
        iterate=config.iterate,
        cleanup=config.cleanup,
    )

    gd = config.global_defaults
    # Capture raw YAML keys to distinguish between explicitly provided vs omitted optional refs.
    try:
        # 'raw' still available from earlier yaml.safe_load
        gd_raw = raw.get('global_defaults', {}) if isinstance(raw, dict) else {}
    except Exception:
        gd_raw = {}

    def tmm(val, default_typ):
        """Required TMM: apply default typ only if entire block absent."""
        if val is None:
            return IbisTypMinMax(typ=default_typ, min=float("nan"), max=float("nan"))
        return IbisTypMinMax(
            typ=getattr(val, "typ", float("nan")),
            min=getattr(val, "min", float("nan")),
            max=getattr(val, "max", float("nan")),
        )

    def tmm_optional(val):
        """Optional reference/clamp TMM: keep all NaN if absent so writer suppresses keyword."""
        if val is None:
            return IbisTypMinMax(typ=float("nan"), min=float("nan"), max=float("nan"))
        return IbisTypMinMax(
            typ=getattr(val, "typ", float("nan")),
            min=getattr(val, "min", float("nan")),
            max=getattr(val, "max", float("nan")),
        )

    global_ = IbisGlobal()
    global_.tempRange = tmm(gd.temp_range, 27)
    global_.voltageRange = tmm(gd.voltage_range, 3.3)
    # Optional references: no default injection; remain NaN if not provided
    global_.pullupRef = tmm_optional(gd.pullup_ref if 'pullup_ref' in gd_raw else None)
    global_.pulldownRef = tmm_optional(gd.pulldown_ref if 'pulldown_ref' in gd_raw else None)
    global_.powerClampRef = tmm_optional(gd.power_clamp_ref if 'power_clamp_ref' in gd_raw else None)
    global_.gndClampRef = tmm_optional(gd.gnd_clamp_ref if 'gnd_clamp_ref' in gd_raw else None)
    global_.vil = tmm(gd.vil, 0.8)
    global_.vih = tmm(gd.vih, 2.0)
    global_.c_comp = tmm(getattr(gd,'c_comp', None), 1.2e-12)
    global_.Rload = getattr(gd, "r_load", 50.0)
    global_.simTime = getattr(gd, "sim_time", 10e-9)
    global_.pinParasitics = getattr(gd, "pin_parasitics", IbisPinParasitics())
    global_.derateVIPct = getattr(gd, "derate_vi_pct", 0.0)
    global_.derateRampPct = getattr(gd, "derate_ramp_pct", 0.0)
    global_.clampTol = getattr(gd, "clamp_tol", 0.0)
    # Optional global subcircuit name from YAML (captured from [Spice Subckt])
    if hasattr(config, "spice_subckt") and getattr(config, "spice_subckt"):
        try:
            setattr(global_, "spice_subckt", config.spice_subckt)
        except Exception:
            pass

    mList = []
    for mcfg in config.models:
        model = IbisModel(
            modelName=mcfg.name,
            modelType=getattr(CS.ModelType, mcfg.type.upper().replace("/", "_").replace("-", "_")),
            polarity=mcfg.polarity,
            enable=mcfg.enable or "",
            Vinl=IbisTypMinMax(typ=mcfg.vinl),
            Vinh=IbisTypMinMax(typ=mcfg.vinh),
            Vmeas=IbisTypMinMax(typ=mcfg.vmeas) if mcfg.vmeas else IbisTypMinMax(),
            Cref=IbisTypMinMax(typ=mcfg.cref) if mcfg.cref else IbisTypMinMax(),
            Rref=IbisTypMinMax(typ=mcfg.rref) if mcfg.rref else IbisTypMinMax(),
            Vref=IbisTypMinMax(typ=mcfg.vref) if mcfg.vref else IbisTypMinMax(),
            c_comp=mcfg.c_comp,
            tempRange=mcfg.temp_range or global_.tempRange,
            voltageRange=mcfg.voltage_range or global_.voltageRange,
            pullupRef=mcfg.pullup_ref or global_.pullupRef,
            pulldownRef=mcfg.pulldown_ref or global_.pulldownRef,
            powerClampRef=mcfg.power_clamp_ref or global_.powerClampRef,
            gndClampRef=mcfg.gnd_clamp_ref or global_.gndClampRef,
            vil=mcfg.vil or global_.vil,
            vih=mcfg.vih or global_.vih,
            tr=mcfg.tr or getattr(global_, 'tr', None),
            tf=mcfg.tf or getattr(global_, 'tf', None),
            Rload=mcfg.r_load or global_.Rload,
            simTime=mcfg.sim_time or global_.simTime,
            derateVIPct=mcfg.derate_vi_pct or global_.derateVIPct,
            derateRampPct=mcfg.derate_ramp_pct or global_.derateRampPct,
            clampTol=mcfg.clamp_tol or global_.clampTol,
            spice_file=mcfg.spice_file or "",
            modelFile=mcfg.modelFile or "",
            modelFileMin=mcfg.modelFileMin or "",
            modelFileMax=mcfg.modelFileMax or "",
            ext_spice_cmd_file=mcfg.ext_spice_cmd_file or "",
            risingWaveList=[IbisWaveTable(**w) for w in mcfg.rising_waveforms],
            fallingWaveList=[IbisWaveTable(**w) for w in mcfg.falling_waveforms],
            noModel=mcfg.nomodel,
        )

        if mcfg.polarity:
            p = mcfg.polarity.upper().replace("-", "_")
            if p == "INVERTING":
                model.polarity = CS.MODEL_POLARITY_INVERTING
            else:
                model.polarity = CS.MODEL_POLARITY_NON_INVERTING
        else:
            model.polarity = CS.MODEL_POLARITY_NON_INVERTING

        # Enable polarity: prefer explicit enable_polarity, else accept legacy 'enable'
        if mcfg.enable_polarity:
            ep = mcfg.enable_polarity.upper().replace("-", "_")
            if ep == "ACTIVE_LOW" or ep == "ACTIVE-LOW":
                model.enable = CS.MODEL_ENABLE_ACTIVE_LOW
            else:
                model.enable = CS.MODEL_ENABLE_ACTIVE_HIGH
        elif getattr(mcfg, "enable", None):
            e = str(mcfg.enable).upper().replace("-", "_")
            if e == "ACTIVE_LOW" or e == "ACTIVE-LOW":
                model.enable = CS.MODEL_ENABLE_ACTIVE_LOW
            else:
                model.enable = CS.MODEL_ENABLE_ACTIVE_HIGH
        else:
            model.enable = CS.MODEL_ENABLE_ACTIVE_HIGH

        model.hasBeenAnalyzed = 0
        mList.append(model)

    for ccfg in config.components:
        pins = []
        for p in ccfg.pList:
            pin = IbisPin(
                pinName=p.pinName,
                signalName=p.signalName,
                modelName=p.modelName,
                spiceNodeName=getattr(p, "spiceNodeName", None) or "",
                R_pin=p.R_pin if p.R_pin is not None else CS.NOT_USED,
                L_pin=p.L_pin if p.L_pin is not None else CS.NOT_USED,
                C_pin=p.C_pin if p.C_pin is not None else CS.NOT_USED,
                pullupRef=p.pullupRef or "NC",
                pulldownRef=p.pulldownRef or "NC",
                powerClampRef=p.powerClampRef or "NC",
                gndClampRef=p.gndClampRef or "NC",
                inputPin=p.inputPin or "",
                enablePin=p.enablePin or "",
            )
            pins.append(pin)

        comp = IbisComponent(
            component=ccfg.component,
            # Default manufacturer if missing (IBIS requires it)
            manufacturer=ccfg.manufacturer or "yourcompany",
            spiceFile=ccfg.spiceFile,
            seriesSpiceFile=ccfg.seriesSpiceFile,
            pinParasitics=ccfg.pinParasitics,
            pList=pins,
        )

        comp.spiceFile = ccfg.spiceFile
        comp.seriesSpiceFile = ccfg.seriesSpiceFile

        if comp.pinParasitics is None:
            comp.pinParasitics = IbisPinParasitics(
                R_pkg=IbisTypMinMax(typ=0.0),
                L_pkg=IbisTypMinMax(typ=0.0),
                C_pkg=IbisTypMinMax(typ=0.0),
            )
            logging.debug("YAML loader: Created default pinParasitics for component %s", comp.component)

        ibis.cList.append(comp)

    for comp in ibis.cList:
        if not getattr(comp, "spiceFile", None):
            continue
        used_model_names = {
            pin.modelName for pin in comp.pList
            if hasattr(pin, "modelName") and pin.modelName
        }
        for model_name in used_model_names:
            model = next((m for m in mList if m.modelName == model_name), None)
            if model and not getattr(model, "spice_file", None):
                model.spice_file = comp.spiceFile
                logging.debug(f"YAML loader: Set model.{model.modelName}.spice_file = {comp.spiceFile}")

    ibis.mList = mList
    if ibis.cList and ibis.cList[0].spiceFile:
        global_.spice_file = ibis.cList[0].spiceFile
        logging.debug("YAML loader: Set global_.spice_file = %s", global_.spice_file)

    model_dict = {m.modelName.lower(): m for m in mList}
    for comp in ibis.cList:
        for pin in comp.pList:
            if pin.modelName and pin.modelName.lower() in model_dict:
                pin.model = model_dict[pin.modelName.lower()]
                logging.debug("YAML loader: Linked pin %s → model %s", pin.pinName, pin.model.modelName)

    return ibis, global_, mList
