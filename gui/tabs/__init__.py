# gui/tabs/__init__.py
from .input_tab import InputTab
from .models_tab import ModelsTab
from .pins_tab import PinsTab
from .simulation_tab import SimulationTab
from .ibis_viewer_tab import IbisViewerTab
from .plots_tab import PlotsTab
from .correlation_tab import CorrelationTab

__all__ = [
    "InputTab", "ModelsTab", "PinsTab", "SimulationTab",
    "IbisViewerTab", "PlotsTab", "CorrelationTab"
]