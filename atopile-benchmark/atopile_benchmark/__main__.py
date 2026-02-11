"""Allow running the package directly with `python -m atopile_benchmark`."""

import sys

from .cli import main

if __name__ == "__main__":
    sys.exit(main())
