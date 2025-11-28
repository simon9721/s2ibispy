# gui/tabs/__init__.py
from .main_entry_tab import MainEntryTab
from .ibis_viewer_tab import IbisViewerTab
from .plots_tab import PlotsTab
from .correlation_tab import CorrelationTab

__all__ = [
    "MainEntryTab",
    "IbisViewerTab", "PlotsTab", "CorrelationTab"
]