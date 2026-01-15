#! uv run
# /// script
# dependencies = [
#   "typer>=0.12",
#   "rich>=13.0.0",
#   "pyyaml>=6.0.2",
#   "typing_extensions>=4.10.0",
# ]
# ///

"""
Canonical entrypoint for the review station web UI.

We keep the implementation in `scripts/review_webui.py` for now to avoid breaking
existing workflows, but provide this stable path under `scripts/review_station/`.
"""

from __future__ import annotations

import runpy
from pathlib import Path


def _main() -> None:
    impl = (Path(__file__).resolve().parents[1] / "review_webui.py").resolve()
    runpy.run_path(str(impl), run_name="__main__")


if __name__ == "__main__":
    _main()
