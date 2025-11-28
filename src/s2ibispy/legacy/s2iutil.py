"""Package copy of legacy s2iutil with package imports."""
import logging
import math
from typing import List, Optional, Dict
from s2ibispy.models import (
    IbisTOP, IbisGlobal, IbisComponent, IbisPin, IbisModel,
    IbisTypMinMax, IbisRamp, IbisPinParasitics
)
from s2ibispy.s2i_constants import ConstantStuff as CS

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def _is_nan_tmm(tmm: Optional[IbisTypMinMax]) -> bool:
    return (tmm is None) or math.isnan(tmm.typ)


class S2IUtil:
    """
    Utilities to complete data structures after parsing.
    - propagate global defaults to models,
    - derive voltage range if only references were given,
    - link pins to models (and apply component overrides),
    - propagate pin parasitics,
    - lightly validate input/enable/diff/spec mappings.
    """

    def __init__(self, mList: List[IbisModel]):
        self.mList = mList or []
        # quick lookup by model name (lower-cased)
        self._model_idx: Dict[str, IbisModel] = {m.modelName.lower(): m for m in self.mList if m.modelName}

    def complete_data_structures(self, ibis: IbisTOP, global_: IbisGlobal) -> None:
        logging.info("Starting data completion")

        logging.info("=== GLOBAL pinParasitics AT START ===")
        if global_.pinParasitics:
            logging.info("  R_pkg: typ=%.6f", global_.pinParasitics.R_pkg.typ)

            if global_.pinParasitics:
                src = global_.pinParasitics
                for comp in ibis.cList or []:
                    if comp.pinParasitics is None:
                        comp.pinParasitics = IbisPinParasitics(
                            R_pkg=IbisTypMinMax(typ=src.R_pkg.typ, min=src.R_pkg.min, max=src.R_pkg.max),
                            L_pkg=IbisTypMinMax(typ=src.L_pkg.typ, min=src.L_pkg.min, max=src.L_pkg.max),
                            C_pkg=IbisTypMinMax(typ=src.C_pkg.typ, min=src.C_pkg.min, max=src.C_pkg.max),
                        )

        logging.info("=== comp.pinParasitics AFTER SAFE PROPAGATION ===")
        for comp in ibis.cList or []:
            if comp.pinParasitics:
                logging.info("  %s: R_pkg.typ=%.6f", comp.component, comp.pinParasitics.R_pkg.typ)

        if global_:
            self.copy_global_data_to_models(global_)
        self.link_pins_to_models(ibis)
        self.propagate_pin_parasitics_to_pins(ibis, global_)
        self.validate_pin_links(ibis)

        logging.info("=== GLOBAL pinParasitics AT END ===")
        if global_.pinParasitics:
            logging.info("  R_pkg: typ=%.6f", global_.pinParasitics.R_pkg.typ)

    @staticmethod
    def _is_use_na(x: float) -> bool:
        try:
            if isinstance(x, float) and math.isnan(x):
                return True
        except Exception:
            pass
        return x == CS.USE_NA

    def _inherit_tmm(self, dst: IbisTypMinMax, src: IbisTypMinMax) -> None:
        if dst is None or src is None:
            return
        if self._is_use_na(dst.typ) and not self._is_use_na(src.typ):
            dst.typ = src.typ
        if self._is_use_na(dst.min) and not self._is_use_na(src.min):
            dst.min = src.min
        if self._is_use_na(dst.max) and not self._is_use_na(src.max):
            dst.max = src.max

    def _inherit_num(self, obj, field: str, src_val: float) -> None:
        if not hasattr(obj, field):
            return
        cur = getattr(obj, field)
        if isinstance(cur, (int, float)) and (self._is_use_na(cur) or cur == 0.0):
            if not self._is_use_na(src_val) and src_val != 0.0:
                setattr(obj, field, src_val)

    def copy_global_data_to_models(self, global_: IbisGlobal) -> None:
        logging.info("Propagating global parameters to models")

        DEFAULT_SIM_TIME = 10.0e-9

        for model in self.mList:
            self._inherit_tmm(model.tempRange,     global_.tempRange)
            self._inherit_tmm(model.voltageRange,  global_.voltageRange)
            self._inherit_tmm(model.pullupRef,     global_.pullupRef)
            self._inherit_tmm(model.pulldownRef,   global_.pulldownRef)
            self._inherit_tmm(model.powerClampRef, global_.powerClampRef)
            self._inherit_tmm(model.gndClampRef,   global_.gndClampRef)
            self._inherit_tmm(model.vil,           global_.vil)
            self._inherit_tmm(model.vih,           global_.vih)
            self._inherit_tmm(model.tr,            getattr(global_, "tr", IbisTypMinMax()))
            self._inherit_tmm(model.tf,            getattr(global_, "tf", IbisTypMinMax()))
            self._inherit_tmm(model.c_comp,        getattr(global_, "c_comp", IbisTypMinMax()))

            self._derive_voltage_range_if_needed(model)

            if model.Rload == 0.0:
                if not self._is_use_na(global_.Rload) and global_.Rload != 0.0:
                    model.Rload = global_.Rload

            if model.simTime == 0.0:
                model.simTime = global_.simTime if (global_.simTime and global_.simTime > 0.0) else DEFAULT_SIM_TIME

            if model.ramp is None:
                model.ramp = IbisRamp(
                    dv_r=IbisTypMinMax(),
                    dt_r=IbisTypMinMax(),
                    dv_f=IbisTypMinMax(),
                    dt_f=IbisTypMinMax(),
                    derateRampPct=getattr(global_, "derateRampPct", 0.0),
                )
            else:
                if getattr(model.ramp, "derateRampPct", 0.0) == 0.0:
                    model.ramp.derateRampPct = getattr(global_, "derateRampPct", 0.0)

            self._inherit_num(model, "derateVIPct", getattr(global_, "derateVIPct", 0.0))
            self._inherit_num(model, "clampTol",    getattr(global_, "clampTol", 0.0))

            logging.debug(
                "Model %s defaults: Vrange=%s PullupRef=%s PulldownRef=%s SimTime=%s",
                model.modelName, model.voltageRange, model.pullupRef, model.pulldownRef, model.simTime
            )

    def _derive_voltage_range_if_needed(self, model: IbisModel) -> None:
        if not _is_nan_tmm(model.voltageRange):
            return

        pu = model.pullupRef
        pd = model.pulldownRef
        if _is_nan_tmm(pu) or _is_nan_tmm(pd):
            return

        def _safe_sub(a: float, b: float) -> float:
            if math.isnan(a) or math.isnan(b):
                return float('nan')
            return a - b

        model.voltageRange = IbisTypMinMax(
            typ=_safe_sub(pu.typ, pd.typ),
            min=_safe_sub(pu.min, pd.min),
            max=_safe_sub(pu.max, pd.max),
        )
        logging.debug("Derived VoltageRange for model %s from refs: %s", model.modelName, model.voltageRange)

    def link_pins_to_models(self, ibis: IbisTOP) -> None:
        logging.info("Linking pins to models and applying component overrides")

        self._model_idx = {m.modelName.lower(): m for m in self.mList if m.modelName}

        for comp in ibis.cList:
            comp_spice_file = getattr(comp, "spiceFile", "") or ""
            comp_series_spice = getattr(comp, "seriesSpiceFile", "") or ""

            used_models: Dict[str, IbisModel] = {}

            for pin in comp.pList:
                name = (pin.modelName or "").strip()
                if not name:
                    pin.model = None
                    continue

                up = name.upper()
                if up in {"POWER", "GND", "NC", "#"}:
                    pin.model = None
                    continue

                mdl = self._model_idx.get(name.lower())
                if mdl is None:
                    pin.model = None
                    continue

                pin.model = mdl
                used_models[mdl.modelName.lower()] = mdl

                if comp_spice_file and not mdl.spice_file:
                    mdl.spice_file = comp_spice_file
                if comp_series_spice and mdl.seriesModel and not mdl.ext_spice_cmd_file:
                    mdl.ext_spice_cmd_file = comp_series_spice

            self._apply_component_overrides_to_models(comp, used_models)

    def _apply_component_overrides_to_models(self, comp: IbisComponent, used_models: Dict[str, IbisModel]) -> None:
        for m in used_models.values():
            self._inherit_tmm(m.voltageRange,  comp.voltageRange)
            self._inherit_tmm(m.tempRange,     comp.tempRange)
            self._inherit_tmm(m.pullupRef,     comp.pullupRef)
            self._inherit_tmm(m.pulldownRef,   comp.pulldownRef)
            self._inherit_tmm(m.powerClampRef, comp.powerClampRef)
            self._inherit_tmm(m.gndClampRef,   comp.gndClampRef)
            self._inherit_tmm(m.tr,            comp.tr)
            self._inherit_tmm(m.tf,            comp.tf)
            self._inherit_tmm(m.vil,           comp.vil)
            self._inherit_tmm(m.vih,           comp.vih)
            self._inherit_tmm(m.c_comp,        comp.c_comp)

            self._inherit_num(m, "Rload",         comp.Rload)
            self._inherit_num(m, "derateVIPct",   comp.derateVIPct)
            self._inherit_num(m, "derateRampPct", comp.derateRampPct)
            self._inherit_num(m, "clampTol",      comp.clampTol)

    def propagate_pin_parasitics_to_pins(self, ibis: IbisTOP, global_: IbisGlobal) -> None:
        for comp in ibis.cList:
            for pin in comp.pList:
                if pin.pParasitics is None:
                    src = comp.pinParasitics or global_.pinParasitics
                    pin.pParasitics = IbisPinParasitics(
                        R_pkg=IbisTypMinMax(src.R_pkg.typ, src.R_pkg.min, src.R_pkg.max),
                        L_pkg=IbisTypMinMax(src.L_pkg.typ, src.L_pkg.min, src.L_pkg.max),
                        C_pkg=IbisTypMinMax(src.C_pkg.typ, src.C_pkg.min, src.C_pkg.max),
                    )
                else:
                    src = comp.pinParasitics or global_.pinParasitics
                    self._inherit_tmm(pin.pParasitics.R_pkg, src.R_pkg)
                    self._inherit_tmm(pin.pParasitics.L_pkg, src.L_pkg)
                    self._inherit_tmm(pin.pParasitics.C_pkg, src.C_pkg)

    def validate_pin_links(self, ibis: IbisTOP) -> None:
        for comp in ibis.cList:
            for pin in comp.pList:
                name = (pin.modelName or "").strip()
                if name and name.upper() not in {"POWER", "GND", "NC", "NOMODEL", "DUMMY", "#"}:
                    if pin.model is None:
                        logging.error("Component '%s': pin '%s' refers to unknown model '%s'",
                                      comp.component, pin.pinName, pin.modelName)

                if getattr(pin, "inputPin", ""):
                    if self.get_matching_pin(pin.inputPin, comp.pList) is None:
                        logging.error("Component '%s': pin '%s' references missing input pin '%s'",
                                      comp.component, pin.pinName, pin.inputPin)

                if getattr(pin, "enablePin", ""):
                    if self.get_matching_pin(pin.enablePin, comp.pList) is None:
                        logging.error("Component '%s': pin '%s' references missing enable pin '%s'",
                                      comp.component, pin.pinName, pin.enablePin)

            if getattr(comp, "dpList", None):
                for dp in comp.dpList:
                    if self.get_matching_pin(dp.invPin, comp.pList) is None:
                        logging.error("Component '%s': Diff pin '%s' not found",
                                      comp.component, dp.invPin)

    def get_matching_pin(self, search_name: str, pList: List[IbisPin]) -> Optional[IbisPin]:
        if not search_name:
            return None
        for pin in pList:
            if search_name.lower() == (pin.pinName or "").lower():
                return pin
        return None

    def get_matching_model(self, search_name: str, mList: List[IbisModel]) -> Optional[IbisModel]:
        if not search_name:
            return None
        if search_name.upper() in {"GND", "POWER", "NC", "NOMODEL", "DUMMY", "#"}:
            return None
        for model in mList:
            if search_name.lower() == (model.modelName or "").lower():
                return model
        logging.warning("Model %s not found", search_name)
        return None
