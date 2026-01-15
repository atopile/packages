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
Package review queue runner.

Goal (simple v1):
- deterministically shard packages across multiple people
- for each package:
  - run `ato build` for every build target declared in `ato.yaml`
  - run `ato package verify -s` (strict)
  - write logs + a human-editable `review.todo.md` for feedback/notes
  - write a machine-readable `results.jsonl` (streaming) + final `results.json`

Notes:
- We intentionally do NOT integrate with any model APIs here (user requested a simple,
  file-based feedback loop). The `review.todo.md` is meant to be opened in Cursor.
- We do NOT do git operations or PR creation here yet; this runner focuses on review prep.
"""

from __future__ import annotations

import json
import os
import re
import shlex
import shutil
import subprocess
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

import typer
import yaml
from rich.console import Console
from rich.table import Table
from typing_extensions import Annotated

app = typer.Typer(rich_markup_mode="rich")
console = Console()


RUN_DIRNAME = "review_queue"


@dataclass(frozen=True)
class BuildResult:
    build: str
    rc: int
    seconds: float
    log_path: str


@dataclass(frozen=True)
class VerifyResult:
    rc: int
    seconds: float
    log_path: str


@dataclass(frozen=True)
class PackageResult:
    package: str
    package_dir: str
    shard: int
    shard_count: int
    started_at: str
    finished_at: str
    builds: list[BuildResult]
    verify: VerifyResult | None
    ok: bool
    layout_paths: dict[str, str]  # build_name -> kicad_pcb path
    todo_path: str


def _now_ts() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _run_cmd(
    cmd: list[str],
    cwd: Path,
    log_path: Path,
    env: dict[str, str] | None = None,
) -> tuple[int, float]:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    start = time.perf_counter()
    proc = subprocess.run(
        cmd,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
        env=env,
    )
    seconds = max(0.0, time.perf_counter() - start)
    # Always write combined output to log for easy triage
    log_path.write_text(proc.stdout or "", encoding="utf-8")
    return proc.returncode, seconds


def _default_ato_cmd(packages_repo_root: Path) -> list[str]:
    """
    Determine how to invoke the Atopile CLI.

    Prefer `ato` if it's on PATH (how most users run it).
    For local-dev checkouts, support running from the sibling `atopile/` repo using
    its uv-managed venv python.
    """
    if shutil.which("ato"):
        return ["ato"]

    sibling_atopile = (packages_repo_root.parent / "atopile").resolve()
    venv_python = sibling_atopile / ".venv" / "bin" / "python"
    if venv_python.exists():
        return [str(venv_python), "-m", "atopile"]

    # Last resort: hope `python -m atopile` works (if installed in current env)
    return ["python", "-m", "atopile"]


def _with_ato_cmd(ato_cmd: list[str], args: list[str]) -> list[str]:
    return [*ato_cmd, *args]


def _read_ato_yaml_builds(ato_yaml: Path) -> list[str]:
    """
    Return build target names declared in `ato.yaml` in stable order.

    We sort keys for determinism across Python versions / YAML emitters.
    """
    cfg = yaml.safe_load(ato_yaml.read_text(encoding="utf-8"))
    builds = cfg.get("builds") or {}
    if not isinstance(builds, dict):
        return []
    return sorted([str(k) for k in builds.keys()])


def _find_layout_pcb_paths(package_dir: Path, build_names: list[str]) -> dict[str, str]:
    """
    Prefer layouts/<build>/<build>.kicad_pcb since that's what gets reviewed.
    """
    out: dict[str, str] = {}
    for b in build_names:
        pcb = package_dir / "layouts" / b / f"{b}.kicad_pcb"
        if pcb.exists():
            out[b] = str(pcb)
    return out


def _write_todo(
    *,
    todo_path: Path,
    package_name: str,
    package_dir: Path,
    build_names: list[str],
    layout_paths: dict[str, str],
    shard: int,
    shard_count: int,
) -> None:
    todo_path.parent.mkdir(parents=True, exist_ok=True)

    def _open_cmd(path: str) -> str:
        if sys_platform := os.uname().sysname.lower():
            if "darwin" in sys_platform:
                return f"open {path!s}"
        return f"xdg-open {path!s}"

    lines: list[str] = []
    lines.append(f"# Review TODO: `{package_name}`")
    lines.append("")
    lines.append(f"- **package dir**: `{package_dir}`")
    lines.append(f"- **shard**: {shard}/{shard_count}")
    lines.append("")
    lines.append("## Status")
    lines.append("- [ ] Builds pass (all targets)")
    lines.append("- [ ] `ato package verify -s` passes")
    lines.append("- [ ] Layout reviewed (manual)")
    lines.append("")
    lines.append("## Layout review (open KiCad)")
    if not layout_paths:
        lines.append("- No `layouts/<build>/<build>.kicad_pcb` found yet (build may have failed).")
    else:
        for b in build_names:
            pcb = layout_paths.get(b)
            if pcb:
                lines.append(f"- **{b}**: `{pcb}`")
                lines.append(f"  - command: `{_open_cmd(pcb)}`")
    lines.append("")
    lines.append("## Notes / issues found")
    lines.append("- ")
    lines.append("")
    lines.append("## Fix-it tasks for Cursor/LLM")
    lines.append("- (add actionable TODOs here)")
    lines.append("")
    todo_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _discover_packages(packages_root: Path) -> list[Path]:
    # Only direct children (each is a package dir)
    out = []
    for d in sorted(packages_root.iterdir()):
        if not d.is_dir() or d.name.startswith("."):
            continue
        if (d / "ato.yaml").exists():
            out.append(d)
    return out


def _select_by_shard(packages: list[Path], shard_count: int, shard_index: int) -> list[Path]:
    if shard_count <= 1:
        return packages
    return [p for i, p in enumerate(packages) if (i % shard_count) == shard_index]


def _select_by_regex(packages: list[Path], package_regex: str) -> list[Path]:
    if not package_regex or package_regex == ".*":
        return packages
    rx = re.compile(package_regex)
    return [p for p in packages if rx.search(p.name)]


def _process_package(
    *,
    package_dir: Path,
    build_names: list[str],
    run_dir: Path,
    shard: int,
    shard_count: int,
    keep_picked_parts: bool,
    ato_cmd: list[str],
) -> PackageResult:
    package_name = package_dir.name
    started_at = _now_ts()

    pkg_run_dir = run_dir / package_name
    logs_dir = pkg_run_dir / "logs"
    todo_path = pkg_run_dir / "review.todo.md"

    layout_paths = _find_layout_pcb_paths(package_dir, build_names)
    _write_todo(
        todo_path=todo_path,
        package_name=package_name,
        package_dir=package_dir,
        build_names=build_names,
        layout_paths=layout_paths,
        shard=shard,
        shard_count=shard_count,
    )

    builds: list[BuildResult] = []
    all_build_ok = True
    for b in build_names:
        cmd = _with_ato_cmd(ato_cmd, ["build", "-b", b])
        if keep_picked_parts:
            cmd.append("--keep-picked-parts")
        log_path = logs_dir / f"build.{b}.log"
        rc, secs = _run_cmd(cmd, cwd=package_dir, log_path=log_path)
        builds.append(
            BuildResult(build=b, rc=rc, seconds=secs, log_path=str(log_path))
        )
        if rc != 0:
            all_build_ok = False
            # If one target fails, it's still useful to attempt others,
            # but in v1 we stop early to keep throughput predictable.
            break

    verify: VerifyResult | None = None
    verify_ok = False
    if all_build_ok:
        v_cmd = _with_ato_cmd(ato_cmd, ["package", "verify", "-s"])
        v_log = logs_dir / "verify.log"
        v_rc, v_secs = _run_cmd(v_cmd, cwd=package_dir, log_path=v_log)
        verify = VerifyResult(rc=v_rc, seconds=v_secs, log_path=str(v_log))
        verify_ok = v_rc == 0

    finished_at = _now_ts()
    ok = all_build_ok and verify_ok
    layout_paths = _find_layout_pcb_paths(package_dir, build_names)

    return PackageResult(
        package=package_name,
        package_dir=str(package_dir),
        shard=shard,
        shard_count=shard_count,
        started_at=started_at,
        finished_at=finished_at,
        builds=builds,
        verify=verify,
        ok=ok,
        layout_paths=layout_paths,
        todo_path=str(todo_path),
    )


@app.command()
def run(
    packages_root: Annotated[
        Path,
        typer.Option(
            help="Path to the packages root (directory containing package folders)."
        ),
    ] = Path("packages"),
    package_regex: Annotated[
        str, typer.Option(help="Regex filter against package directory name.")
    ] = ".*",
    shard_count: Annotated[int, typer.Option(help="Total number of shards.")] = 1,
    shard_index: Annotated[int, typer.Option(help="This shard index (0-based).")] = 0,
    jobs: Annotated[int, typer.Option(help="Max concurrent packages to process.")] = 2,
    keep_picked_parts: Annotated[
        bool,
        typer.Option(help="Pass --keep-picked-parts to builds (faster, stable picks)."),
    ] = True,
    out_dir: Annotated[
        Path,
        typer.Option(help="Output directory for review runs (default: ./build/review_queue)."),
    ] = Path("build") / RUN_DIRNAME,
    ato_cmd: Annotated[
        str,
        typer.Option(
            help=(
                "Command used to invoke Atopile. "
                "Examples: 'ato' or '/abs/path/to/atopile/.venv/bin/python -m atopile'"
            )
        ),
    ] = "",
    dry_run: Annotated[
        bool, typer.Option(help="Only plan the queue, don't run builds/verify.")
    ] = False,
) -> None:
    """
    Run the review queue for selected packages.

    Example (two reviewers):
      - Reviewer A: --shard-count 2 --shard-index 0
      - Reviewer B: --shard-count 2 --shard-index 1
    """
    if shard_index < 0 or shard_index >= shard_count:
        raise typer.BadParameter("--shard-index must be within [0, shard_count)")

    packages_root = packages_root.resolve()
    if not packages_root.exists():
        raise typer.BadParameter(f"packages_root not found: {packages_root}")

    packages_repo_root = packages_root.parent.resolve()
    ato_cmd_list = (
        shlex.split(ato_cmd) if ato_cmd.strip() else _default_ato_cmd(packages_repo_root)
    )

    all_pkgs = _discover_packages(packages_root)
    all_pkgs = _select_by_regex(all_pkgs, package_regex)
    selected = _select_by_shard(all_pkgs, shard_count=shard_count, shard_index=shard_index)

    run_id = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    run_dir = (out_dir / run_id).resolve()
    run_dir.mkdir(parents=True, exist_ok=True)

    plan_table = Table(title=f"Review queue plan (run={run_id})")
    plan_table.add_column("Package")
    plan_table.add_column("Build targets", justify="left")
    for p in selected:
        builds = _read_ato_yaml_builds(p / "ato.yaml")
        plan_table.add_row(p.name, ", ".join(builds) if builds else "[red]NO BUILDS[/red]")
    console.print(plan_table)
    console.print(
        f"[dim]Selected {len(selected)}/{len(all_pkgs)} packages "
        f"(shard {shard_index}/{shard_count}, jobs={jobs}).[/dim]"
    )
    console.print(f"[dim]Run output: {run_dir}[/dim]")

    if dry_run:
        return

    # Stream results so partial progress is saved even if interrupted.
    results_jsonl = run_dir / "results.jsonl"
    results_json = run_dir / "results.json"

    from concurrent.futures import ThreadPoolExecutor, as_completed

    results: list[PackageResult] = []

    with ThreadPoolExecutor(max_workers=max(1, jobs)) as ex:
        futures = {}
        for p in selected:
            build_names = _read_ato_yaml_builds(p / "ato.yaml")
            futures[
                ex.submit(
                    _process_package,
                    package_dir=p,
                    build_names=build_names,
                    run_dir=run_dir,
                    shard=shard_index,
                    shard_count=shard_count,
                    keep_picked_parts=keep_picked_parts,
                    ato_cmd=ato_cmd_list,
                )
            ] = p

        for fut in as_completed(futures):
            res = fut.result()
            results.append(res)

            # Append to jsonl
            with results_jsonl.open("a", encoding="utf-8") as f:
                f.write(json.dumps(asdict(res), sort_keys=True) + "\n")

            # Print lightweight live progress
            status = "[green]OK[/green]" if res.ok else "[red]FAIL[/red]"
            console.print(f"{status} {res.package}  todo={res.todo_path}")

    # Write aggregated json
    results_sorted = sorted(results, key=lambda r: r.package)
    results_json.write_text(
        json.dumps([asdict(r) for r in results_sorted], indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )

    ok_count = sum(1 for r in results_sorted if r.ok)
    fail_count = len(results_sorted) - ok_count
    console.print(
        f"[bold]Done.[/bold] ok={ok_count} fail={fail_count} "
        f"(see `{results_json}` / `{results_jsonl}`)"
    )


if __name__ == "__main__":
    app()
