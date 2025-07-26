"""
Entry point for running license_reporter as a module.

This allows the package to be executed with:
    python -m license_reporter
"""

import sys
from .cli import main

if __name__ == "__main__":
    sys.exit(main())
