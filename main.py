#!/usr/bin/env python3
# main.py — End-to-end driver: SPICE -> IBIS
import argparse
import logging
import os
import sys
#import shutil
import subprocess
from typing import Optional, Any
from pathlib import Path

from legacy.parser import S2IParser
#from s2iutil import S2IUtil
from s2ianaly import S2IAnaly
#from s2ioutput import S2IOutput
from s2ioutput import IbisWriter as S2IOutput  # ← Alias!

#!/usr/bin/env python3
"""Tiny compatibility shim for running the packaged CLI.

This file delegates execution to `s2ibispy.cli.main` so existing
invocations like `python main.py ...` continue to work during the
refactor. The real implementation lives in `src/s2ibispy/cli.py`.
"""
import sys

from s2ibispy.cli import main as package_main


def main(argv=None):
    # Delegate to the package CLI; allow passing argv for tests.
    return package_main(argv)


if __name__ == "__main__":
    sys.exit(main())
            capture_output=True,
