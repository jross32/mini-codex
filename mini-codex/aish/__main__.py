"""Entry point for AISH CLI.

Enables: python -m aish <command> [args]
"""

import sys
from aish.cli import main

if __name__ == "__main__":
    sys.exit(main())
