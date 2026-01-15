import json
import tempfile
import time
import unittest
import urllib.request
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from types import ModuleType
from typing import Any
import importlib.util


def _load_review_webui_module() -> ModuleType:
    """
    Load `scripts/review_webui.py` as a module without requiring `scripts/` to be a package.
    """
    repo_root = Path(__file__).resolve().parents[2]
    impl = repo_root / "review_webui.py"
    spec = importlib.util.spec_from_file_location("review_webui_impl", impl)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    # `dataclasses.dataclass` expects the defining module to exist in `sys.modules`.
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)  # type: ignore[attr-defined]
    return mod


def _write_minimal_package(pkg_dir: Path, *, package_name: str) -> None:
    pkg_dir.mkdir(parents=True, exist_ok=True)
    (pkg_dir / "demo.ato").write_text(
        'module Demo:\n    """demo"""\n    pass\n', encoding="utf-8"
    )
    (pkg_dir / "ato.yaml").write_text(
        "\n".join(
            [
                'requires-atopile: "^0.14.0"',
                "",
                "paths:",
                "  src: .",
                "  layout: ./layouts",
                "",
                "builds:",
                "  default:",
                "    entry: demo.ato:Demo",
                "",
                "package:",
                f"  identifier: atopile/{package_name}",
                "  repository: https://github.com/atopile/packages",
                f"  homepage: https://github.com/atopile/packages/tree/main/packages/{package_name}",
                '  version: "0.1.0"',
                "  authors:",
                "    - name: atopile",
                "      email: hi@atopile.io",
                '  summary: "test package"',
                "  license: MIT",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _http_get_json(url: str, *, timeout_s: float = 2.0) -> tuple[float, Any]:
    t0 = time.perf_counter()
    with urllib.request.urlopen(url, timeout=timeout_s) as r:
        data = r.read()
    dt = time.perf_counter() - t0
    return dt, json.loads(data.decode("utf-8"))


class TestReviewWebuiPerf(unittest.TestCase):
    """
    Closed-loop performance tests for the review web UI.

    These tests are intentionally lightweight:
    - no `ato build`
    - no `ato package verify`
    - no user interaction
    - no external network calls
    """

    def test_api_state_is_fast_and_does_not_timeout(self) -> None:
        mod = _load_review_webui_module()
        ReviewRun = getattr(mod, "ReviewRun")
        Server = getattr(mod, "Server")

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            packages_root = root / "packages"
            packages_root.mkdir(parents=True, exist_ok=True)

            # Create a moderately large state to stress JSON generation.
            selected = []
            for i in range(250):
                name = f"t-pkg-{i:04d}"
                pkg_dir = packages_root / name
                _write_minimal_package(pkg_dir, package_name=name)
                selected.append(pkg_dir)

            run_dir = root / "run"
            rr = ReviewRun(
                packages_root=packages_root,
                selected_packages=selected,
                jobs=1,
                run_dir=run_dir,
                ato_cmd=["ato"],  # not executed in this test
                keep_picked_parts=True,
                open_cmd="open",
                max_ready=10,
                server_origin="http://127.0.0.1:0",
                packages_repo_root=packages_root.parent,
                enable_publish=False,
            )

            srv = Server(
                host="127.0.0.1",
                port=0,  # ephemeral
                run=rr,
                kicanvas_js=Path(__file__),  # not used by this test
                model_viewer_js=Path(__file__),  # not used by this test
                cursor_cmd="cursor",
            )

            httpd, port = srv.start_in_thread()
            try:
                url = f"http://127.0.0.1:{port}/api/state"

                # Sequential sampling: should not timeout.
                dts = []
                for _ in range(30):
                    dt, payload = _http_get_json(url, timeout_s=2.0)
                    dts.append(dt)
                    self.assertIn("packages", payload)

                # Concurrency sampling: should not deadlock.
                with ThreadPoolExecutor(max_workers=10) as ex:
                    futs = [ex.submit(_http_get_json, url, timeout_s=2.0) for _ in range(40)]
                    for f in as_completed(futs, timeout=5.0):
                        dt, payload = f.result()
                        dts.append(dt)
                        self.assertIn("packages", payload)

                # Very conservative threshold: regression guard against multi-second hangs.
                self.assertLess(max(dts), 1.5, f"/api/state too slow: max={max(dts):.3f}s")
            finally:
                httpd.shutdown()
                httpd.server_close()
