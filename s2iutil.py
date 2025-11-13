# s2iutil.py
import logging
import math
from typing import List, Optional, Dict
from models import (
    IbisTOP, IbisGlobal, IbisComponent, IbisPin, IbisModel,
    IbisTypMinMax, IbisRamp, IbisPinParasitics
)
from s2i_constants import ConstantStuff as CS

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def _is_nan_tmm(tmm: Optional[IbisTypMinMax]) -> bool:
    return (tmm is None) or math.isnan(tmm.typ)


class S2IUtil:
    """
    Utilities to complete data structures after parsing:
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

    # -------------------------
    # Main entry point
    # -------------------------
    def complete_data_structures(self, ibis: IbisTOP, global_: IbisGlobal) -> None:
        logging.info("Starting data completion")

        # === LOG 1: GLOBAL AT START ===
        logging.info("=== GLOBAL pinParasitics AT START ===")
        if global_.pinParasitics:
            logging.info("  R_pkg: typ=%.6f", global_.pinParasitics.R_pkg.typ)

            # === PROPAGATE FIRST — MANUAL COPY (WORKS WITH nan) ===
            if global_.pinParasitics:
                src = global_.pinParasitics
                for comp in ibis.cList or []:
                    if comp.pinParasitics is None:
                        comp.pinParasitics = IbisPinParasitics(
                            R_pkg=IbisTypMinMax(typ=src.R_pkg.typ, min=src.R_pkg.min, max=src.R_pkg.max),
                            L_pkg=IbisTypMinMax(typ=src.L_pkg.typ, min=src.L_pkg.min, max=src.L_pkg.max),
                            C_pkg=IbisTypMinMax(typ=src.C_pkg.typ, min=src.C_pkg.min, max=src.C_pkg.max),
                        )

        # === LOG: AFTER SAFE PROPAGATION ===
        logging.info("=== comp.pinParasitics AFTER SAFE PROPAGATION ===")
        for comp in ibis.cList or []:
            if comp.pinParasitics:
                logging.info("  %s: R_pkg.typ=%.6f", comp.component, comp.pinParasitics.R_pkg.typ)

        # === NOW RUN EVERYTHING ELSE ===
        if global_:
            self.copy_global_data_to_models(global_)
        self.link_pins_to_models(ibis)
        self.propagate_pin_parasitics_to_pins(ibis, global_)
        self.validate_pin_links(ibis)

        # === LOG 2: GLOBAL AT END ===
        logging.info("=== GLOBAL pinParasitics AT END ===")
        if global_.pinParasitics:
            logging.info("  R_pkg: typ=%.6f", global_.pinParasitics.R_pkg.typ)

    # -------------------------
    # Helpers for inheritance
    # -------------------------
    @staticmethod
    def _is_use_na(x: float) -> bool:
        # Treat NaN or CS.USE_NA as "unset"
        try:
            if isinstance(x, float) and math.isnan(x):
                return True
        except Exception:
            pass
        return x == CS.USE_NA

    def _inherit_tmm(self, dst: IbisTypMinMax, src: IbisTypMinMax) -> None:
        """Copy any NA from src to dst (typ/min/max independently)."""
        if dst is None or src is None:
            return
        if self._is_use_na(dst.typ) and not self._is_use_na(src.typ):
            dst.typ = src.typ
        if self._is_use_na(dst.min) and not self._is_use_na(src.min):
            dst.min = src.min
        if self._is_use_na(dst.max) and not self._is_use_na(src.max):
            dst.max = src.max

    def _inherit_num(self, obj, field: str, src_val: float) -> None:
        """Copy a numeric field if NA/zero and src is set."""
        if not hasattr(obj, field):
            return
        cur = getattr(obj, field)
        if isinstance(cur, (int, float)) and (self._is_use_na(cur) or cur == 0.0):
            if not self._is_use_na(src_val) and src_val != 0.0:
                setattr(obj, field, src_val)

    # -------------------------
    # Globals → Models
    # -------------------------
    def copy_global_data_to_models(self, global_: IbisGlobal) -> None:
        """
        Propagate global parameters into individual models without overwriting
        values that are already set at the model level. Also try to derive
        [Voltage range] from references when it is missing.
        """
        logging.info("Propagating global parameters to models")

        DEFAULT_SIM_TIME = 10.0e-9  # used if nothing is set anywhere

        for model in self.mList:
            # ranges & references (TMM)
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

            # Derive voltage range from references if still missing
            self._derive_voltage_range_if_needed(model)

            # scalars
            # Rload: only copy if model doesn’t define waves (common rule of thumb)
            if (model.Rload == 0.0) and not (model.risingWaveList or model.fallingWaveList):
                if not self._is_use_na(global_.Rload) and global_.Rload != 0.0:
                    model.Rload = global_.Rload

            # Simulation time
            if model.simTime == 0.0:
                model.simTime = global_.simTime if (global_.simTime and global_.simTime > 0.0) else DEFAULT_SIM_TIME

            # Ramp container always present; inherit derateRampPct if not set
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

            # VI derate
            self._inherit_num(model, "derateVIPct", getattr(global_, "derateVIPct", 0.0))
            # clamp tolerance
            self._inherit_num(model, "clampTol",    getattr(global_, "clampTol", 0.0))

            logging.debug(
                "Model %s defaults: Vrange=%s PullupRef=%s PulldownRef=%s SimTime=%s",
                model.modelName, model.voltageRange, model.pullupRef, model.pulldownRef, model.simTime
            )

    def _derive_voltage_range_if_needed(self, model: IbisModel) -> None:
        """
        If [Voltage range] is missing (typ/min/max NaN) but pullup & pulldown
        references are populated, derive:
            Vrange.typ = pullupRef.typ - pulldownRef.typ
            Vrange.min = pullupRef.min - pulldownRef.min
            Vrange.max = pullupRef.max - pulldownRef.max
        """
        if not _is_nan_tmm(model.voltageRange):
            return

        pu = model.pullupRef
        pd = model.pulldownRef
        if _is_nan_tmm(pu) or _is_nan_tmm(pd):
            # cannot derive; leave as-is and let later validation complain if needed
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

    # -------------------------
    # Link pins → models (+ component → model overrides)
    # -------------------------
    def link_pins_to_models(self, ibis: IbisTOP) -> None:
        """
        Attach the actual IbisModel objects to pins by modelName and apply
        component-level overrides to those models that are actually used.
        Also propagate component spice filenames into model if not set.
        """
        logging.info("Linking pins to models and applying component overrides")

        # refresh index in case self.mList was mutated by the caller
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
                if up in {"POWER", "GND", "NC", "NOMODEL", "DUMMY", "#"}:
                    pin.model = None
                    continue

                mdl = self._model_idx.get(name.lower())
                if mdl is None:
                    pin.model = None
                    continue

                pin.model = mdl
                used_models[mdl.modelName.lower()] = mdl

                # component-level SPICE filenames if model didn't set its own
                if comp_spice_file and not mdl.spice_file:
                    mdl.spice_file = comp_spice_file
                # series decks: stash in ext_spice_cmd_file (or however you drive series sims)
                if comp_series_spice and mdl.seriesModel and not mdl.ext_spice_cmd_file:
                    mdl.ext_spice_cmd_file = comp_series_spice

            # Apply component overrides to the used models only
            self._apply_component_overrides_to_models(comp, used_models)

    def _apply_component_overrides_to_models(self, comp: IbisComponent, used_models: Dict[str, IbisModel]) -> None:
        """Component → model inheritance for models actually referenced by this component."""
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
            self._inherit_num(m, "simTime",       comp.simTime)
            self._inherit_num(m, "derateVIPct",   comp.derateVIPct)
            self._inherit_num(m, "derateRampPct", comp.derateRampPct)
            self._inherit_num(m, "clampTol",      comp.clampTol)

    # -------------------------
    # Parasitics → pins
    # -------------------------
    def propagate_pin_parasitics_to_pins(self, ibis: IbisTOP, global_: IbisGlobal) -> None:
        """
        Ensure each pin has a parasitic container and seed it from the component
        [R_pkg]/[L_pkg]/[C_pkg] if present, else from global. Create a *copy*
        so later edits on a pin don’t mutate component/global default objects.
        """
        for comp in ibis.cList:
            for pin in comp.pList:
                if pin.pParasitics is None:
                    # prefer component-level defaults if set; else global
                    src = comp.pinParasitics or global_.pinParasitics
                    pin.pParasitics = IbisPinParasitics(
                        R_pkg=IbisTypMinMax(src.R_pkg.typ, src.R_pkg.min, src.R_pkg.max),
                        L_pkg=IbisTypMinMax(src.L_pkg.typ, src.L_pkg.min, src.L_pkg.max),
                        C_pkg=IbisTypMinMax(src.C_pkg.typ, src.C_pkg.min, src.C_pkg.max),
                    )
                else:
                    # backfill missing sub-fields from comp/global
                    src = comp.pinParasitics or global_.pinParasitics
                    self._inherit_tmm(pin.pParasitics.R_pkg, src.R_pkg)
                    self._inherit_tmm(pin.pParasitics.L_pkg, src.L_pkg)
                    self._inherit_tmm(pin.pParasitics.C_pkg, src.C_pkg)

    # -------------------------
    # Validation helpers
    # -------------------------
    def validate_pin_links(self, ibis: IbisTOP) -> None:
        """
        Light validation of input/enable references and diff pins, and also
        complain when a non-special model name couldn't be resolved.
        """
        for comp in ibis.cList:
            for pin in comp.pList:
                # Unresolved model reference (non-special)
                name = (pin.modelName or "").strip()
                if name and name.upper() not in {"POWER", "GND", "NC", "NOMODEL", "DUMMY", "#"}:
                    if pin.model is None:
                        logging.error("Component '%s': pin '%s' refers to unknown model '%s'",
                                      comp.component, pin.pinName, pin.modelName)

                # If pin specifies an input pin, make sure it exists
                if getattr(pin, "inputPin", ""):
                    if self.get_matching_pin(pin.inputPin, comp.pList) is None:
                        logging.error("Component '%s': pin '%s' references missing input pin '%s'",
                                      comp.component, pin.pinName, pin.inputPin)

                # If pin specifies an enable pin, make sure it exists
                if getattr(pin, "enablePin", ""):
                    if self.get_matching_pin(pin.enablePin, comp.pList) is None:
                        logging.error("Component '%s': pin '%s' references missing enable pin '%s'",
                                      comp.component, pin.pinName, pin.enablePin)

            # Differential pairs sanity: ensure referenced pins exist (keep non-fatal)
            if getattr(comp, "dpList", None):
                for dp in comp.dpList:
                    if self.get_matching_pin(dp.invPin, comp.pList) is None:
                        logging.error("Component '%s': Diff pin '%s' not found",
                                      comp.component, dp.invPin)

    # -------------------------
    # Lookups
    # -------------------------
    def get_matching_pin(self, search_name: str, pList: List[IbisPin]) -> Optional[IbisPin]:
        """Case-insensitive pin lookup by name."""
        if not search_name:
            return None
        for pin in pList:
            if search_name.lower() == (pin.pinName or "").lower():
                return pin
        return None

    def get_matching_model(self, search_name: str, mList: List[IbisModel]) -> Optional[IbisModel]:
        """Case-insensitive model lookup by name; skip special keywords."""
        if not search_name:
            return None
        if search_name.upper() in {"GND", "POWER", "NC", "NOMODEL", "DUMMY", "#"}:
            return None
        for model in mList:
            if search_name.lower() == (model.modelName or "").lower():
                return model
        logging.warning("Model %s not found", search_name)
        return None
