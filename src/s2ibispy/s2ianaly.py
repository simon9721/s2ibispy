"""Expose analyzer types used by the packaged CLI.

Prefer importing the original `S2IAnaly` from the repository root
`s2ianaly.py` when available. If it's not present or import fails,
provide a clear fallback stub that raises a helpful error when used.
"""
import logging
from typing import List, Dict, Any


try:
    # Prefer the original analyzer implementation if present at top-level.
    from s2ianaly import S2IAnaly  # type: ignore
except Exception:
    class S2IAnaly:
        def __init__(self, *args, **kwargs):
            raise ImportError(
                "The full analyzer implementation (`s2ianaly.S2IAnaly`) is not available in the package. "
                "During the refactor keep the top-level `s2ianaly.py` or add a full package copy."
            )


class FindSupplyPins:
    def find_pins(self, pin, pin_list: List[Any], has_mapping: bool) -> Dict[str, Any]:
        pullup = None
        pulldown = None
        for p in pin_list:
            pname = getattr(p, "pinName", str(p)).lower()
            if pname in {"vdd", "vcc", "vddio"} and pullup is None:
                pullup = p
            if pname in {"vss", "gnd", "0", "vssio"} and pulldown is None:
                pulldown = p

        if not pullup:
            logging.debug("No explicit VDD found in pin list — leaving pullup None")
        if not pulldown:
            logging.debug("No explicit VSS found in pin list — leaving pulldown None")

        return {"pullupPin": pullup, "pulldownPin": pulldown}
