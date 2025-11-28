#!/usr/bin/env python3
"""Tiny compatibility shim for running the packaged CLI.

This file delegates execution to `s2ibispy.cli.main` so existing
invocations like `python main.py ...` continue to work during the
refactor. The real implementation lives in `src/s2ibispy/cli.py`.
"""
import sys
from s2ibispy.cli import main as package_main


def main(argv=None, gui=None):
    # Delegate to the package CLI; allow passing argv for tests.
    return package_main(argv, gui=gui)


if __name__ == "__main__":
    sys.exit(main())
