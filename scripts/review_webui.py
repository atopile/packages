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
Local review workstation (web UI) for package upgrade/review.

Design goals:
- Zero external services. Everything is local + file-based.
- Reuse the same KiCanvas embed approach used by the VSCode extension:
    <script type="module" src="kicanvas.js"></script>
    <kicanvas-embed src=".../some.kicad_pcb"></kicanvas-embed>
- Keep state in a run directory so multiple reviewers can shard work and share artifacts.

This script can optionally publish (git branch + commit + PR + merge) when enabled.
"""

from __future__ import annotations

import json
import os
import platform
import re
import shlex
import shutil
import subprocess
import sys
import multiprocessing as mp
import threading
import time
import getpass
import signal
from dataclasses import asdict, dataclass, field
from datetime import datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Literal
from urllib.parse import parse_qs, quote, unquote, urlparse
from urllib.request import Request, urlopen

import typer
import yaml
from rich.console import Console
from typing_extensions import Annotated

console = Console()
app = typer.Typer(rich_markup_mode="rich")


Status = Literal[
    "not_started",
    "building",
    "verifying",
    "awaiting_review",
    "approved",
    "published",
    "pushing_branch",
    "branch_pushed",
    "pr_opened",
    "paused",
    "skipped",  # backward-compat for older run dirs
    "error",
    "needs_input",  # AI requested human assistance
]

AUTO_BEGIN = "<!-- AUTO:BEGIN -->"
AUTO_END = "<!-- AUTO:END -->"


def _now_id() -> str:
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


def _now_ts() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _discover_packages(packages_root: Path) -> list[Path]:
    out: list[Path] = []
    for d in sorted(packages_root.iterdir()):
        if not d.is_dir() or d.name.startswith("."):
            continue
        if (d / "ato.yaml").exists():
            out.append(d)
    return out


def _read_ato_yaml_builds(ato_yaml: Path) -> list[str]:
    cfg = yaml.safe_load(ato_yaml.read_text(encoding="utf-8"))
    builds = cfg.get("builds") or {}
    if not isinstance(builds, dict):
        return []
    return sorted([str(k) for k in builds.keys()])


def _read_ato_yaml_build_entries(ato_yaml: Path) -> dict[str, str]:
    """
    Return build_name -> entry string from `ato.yaml`.

    Example entry:
      "bosch-bme280.ato:BOSCH_BME280"
    We keep the raw entry string so the UI can resolve the underlying `.ato` file.
    """
    try:
        cfg = yaml.safe_load(ato_yaml.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}
    builds = cfg.get("builds") or {}
    if not isinstance(builds, dict):
        return {}
    out: dict[str, str] = {}
    for k, v in builds.items():
        if not isinstance(k, str) or not isinstance(v, dict):
            continue
        entry = v.get("entry")
        if isinstance(entry, str) and entry.strip():
            out[k] = entry.strip()
    return out


def _read_ato_yaml_package_identifier(ato_yaml: Path) -> str | None:
    """
    Read `package.identifier` from `ato.yaml` if present.

    We use this to query the packages registry for "published" status and
    show a green tick in the review UI once the registry reports `0.14.x`.
    """
    try:
        cfg = yaml.safe_load(ato_yaml.read_text(encoding="utf-8")) or {}
    except Exception:
        return None
    pkg = cfg.get("package") or {}
    if not isinstance(pkg, dict):
        return None
    ident = pkg.get("identifier")
    if not isinstance(ident, str):
        return None
    ident = ident.strip()
    return ident or None


def _select_by_regex(packages: list[Path], package_regex: str) -> list[Path]:
    if not package_regex or package_regex == ".*":
        return packages
    rx = re.compile(package_regex)
    return [p for p in packages if rx.search(p.name)]


def _select_by_shard(
    packages: list[Path], shard_count: int, shard_index: int
) -> list[Path]:
    if shard_count <= 1:
        return packages
    return [p for i, p in enumerate(packages) if (i % shard_count) == shard_index]


def _default_ato_cmd(packages_repo_root: Path) -> list[str]:
    if shutil.which("ato"):
        return ["ato"]
    sibling_atopile = (packages_repo_root.parent / "atopile").resolve()
    venv_python = sibling_atopile / ".venv" / "bin" / "python"
    if venv_python.exists():
        return [str(venv_python), "-m", "atopile"]
    return ["python", "-m", "atopile"]


def _default_cursor_cmd() -> str:
    """
    Pick a sensible default for opening files in Cursor.
    - Prefer `cursor` CLI if available.
    - On macOS, fall back to `open -a Cursor`.
    """
    if shutil.which("cursor"):
        return "cursor"
    if sys.platform == "darwin":
        return "open -a Cursor"
    # Best-effort fallback; users can override with --cursor-cmd.
    return "cursor"


def _default_kicanvas_js(packages_repo_root: Path) -> Path | None:
    """
    Default to the KiCanvas bundle we already ship in the VSCode extension repo.
    """
    sibling_atopile = (packages_repo_root.parent / "atopile").resolve()
    p = (
        sibling_atopile
        / "src"
        / "vscode-atopile"
        / "resources"
        / "kicanvas"
        / "kicanvas.js"
    )
    return p if p.exists() else None


def _default_model_viewer_js(packages_repo_root: Path) -> Path | None:
    sibling_atopile = (packages_repo_root.parent / "atopile").resolve()
    p = (
        sibling_atopile
        / "src"
        / "vscode-atopile"
        / "resources"
        / "model-viewer"
        / "model-viewer.min.js"
    )
    return p if p.exists() else None


def _open_file_cmd(path: Path, open_cmd: str) -> list[str]:
    """
    open_cmd examples:
      - "open" (mac)
      - "open -a KiCad" (mac, force KiCad)
      - "xdg-open" (linux)
    """
    return [*shlex.split(open_cmd), str(path)]


def _find_layout_pcb_paths(package_dir: Path, build_names: list[str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for b in build_names:
        pcb = package_dir / "layouts" / b / f"{b}.kicad_pcb"
        if pcb.exists():
            out[b] = str(pcb)
    return out


def _find_model_glb_paths(package_dir: Path, build_names: list[str]) -> dict[str, str]:
    """
    Matches VSCode extension convention (see vscode-atopile `manifest.ts`):
      build/builds/<build>/<build>.pcba.glb
    """
    out: dict[str, str] = {}
    for b in build_names:
        glb = package_dir / "build" / "builds" / b / f"{b}.pcba.glb"
        if glb.exists():
            out[b] = str(glb)
    return out


def _count_log_levels(log_text: str) -> tuple[int, int]:
    # We match Rich-style logs too (INFO/WARNING/ERROR)
    warn = len(re.findall(r"\bWARNING\b", log_text))
    err = len(re.findall(r"\bERROR\b", log_text))
    return warn, err


def _parse_build_summary_md(summary_md: str) -> dict[str, dict[str, object]]:
    """
    Parse `build/logs/latest/summary.md` produced by `ato build`.

    Returns mapping: build_name -> {status, seconds, warn, err}
      - status: "success" | "warning" | "failed"
      - seconds: float
      - warn/err: int

    Notes:
    - The summary is a markdown table with columns:
      | Target | Status | Time | Warn | Err | Logs |
    - Status is an emoji (✅/⚠️/❌).
    """
    out: dict[str, dict[str, object]] = {}
    for ln in summary_md.splitlines():
        s = ln.strip()
        if not s.startswith("|"):
            continue
        # Skip header/separator lines
        if "Target" in s and "Status" in s:
            continue
        if set(s) <= {"|", "-", " "}:
            continue
        parts = [p.strip() for p in s.strip("|").split("|")]
        if len(parts) < 6:
            continue
        target, status_txt, time_txt, warn_txt, err_txt, _logs = parts[:6]
        if not target:
            continue
        status = "success"
        if "❌" in status_txt:
            status = "failed"
        elif "⚠" in status_txt:
            status = "warning"
        secs = 0.0
        m = re.search(r"([0-9]+(?:\\.[0-9]+)?)\\s*s", time_txt)
        if m:
            secs = float(m.group(1))
        try:
            warn = int(re.sub(r"\\D+", "", warn_txt) or "0")
        except Exception:
            warn = 0
        try:
            err = int(re.sub(r"\\D+", "", err_txt) or "0")
        except Exception:
            err = 0
        out[target] = {"status": status, "seconds": secs, "warn": warn, "err": err}
    return out


def _review_worker_process(
    task_q: "mp.Queue[dict[str, Any]]",
    result_q: "mp.Queue[dict[str, Any]]",
    cancel_flags: Any,
    ato_cmd: list[str],
    keep_picked_parts: bool,
    jobs_per_pkg: int,
) -> None:
    """
    Worker process entrypoint.

    Runs in a separate process from the UI server. It receives package tasks, runs:
      - `ato build` (all targets) with internal process-based parallelism
      - `ato package verify -s`

    and sends results back to the UI process via `result_q`.
    """

    def cancelled(pkg: str) -> bool:
        try:
            return bool(cancel_flags.get(pkg, False))
        except Exception:
            return False

    def run_cmd_to_log(
        *,
        cmd: list[str],
        cwd: Path,
        log_path: Path,
        pkg: str,
        step: str,
        status_file: Path | None = None,
    ) -> tuple[int, float, int, int]:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        start = time.perf_counter()

        # Set up environment with status file for progress reporting
        env = os.environ.copy()
        if status_file:
            status_file.parent.mkdir(parents=True, exist_ok=True)
            env["ATO_BUILD_STATUS_FILE"] = str(status_file)

        with log_path.open("w", encoding="utf-8") as f:
            f.write("$ " + " ".join(shlex.quote(c) for c in cmd) + "\n\n")
            f.flush()
            proc = subprocess.Popen(
                cmd,
                cwd=cwd,
                stdout=f,
                stderr=subprocess.STDOUT,
                text=True,
                env=env,
            )
            # Report pid/step.
            result_q.put(
                {
                    "type": "step",
                    "package": pkg,
                    "current_step": step,
                    "current_pid": proc.pid,
                }
            )

            last_progress: str | None = None
            while True:
                rc = proc.poll()
                if rc is not None:
                    break
                if cancelled(pkg):
                    try:
                        f.write("\n\n[review-station] Cancel requested, terminating…\n")
                        f.flush()
                    except Exception:
                        pass
                    proc.terminate()
                    try:
                        proc.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        proc.kill()
                    rc = proc.returncode if proc.returncode is not None else -1
                    break

                # Read and report progress from status files
                # First try our status file, then check ato's per-build status files
                progress = None
                if status_file and status_file.exists():
                    try:
                        progress = status_file.read_text(encoding="utf-8").strip()
                    except Exception:
                        pass

                # Also check ato's build status files (in package's build/logs/latest/<build>/status.txt)
                # Collect progress for ALL active builds
                if not progress:
                    try:
                        import re
                        latest_logs = cwd / "build" / "logs" / "latest"
                        if latest_logs.exists():
                            build_statuses = {}
                            for status_path in latest_logs.glob("*/status.txt"):
                                try:
                                    build_name = status_path.parent.name
                                    txt = status_path.read_text(encoding="utf-8").strip()
                                    if txt:
                                        # Strip Rich markup like [green]...[/green]
                                        txt = re.sub(r"\[/?[a-z_]+\]", "", txt)
                                        build_statuses[build_name] = txt
                                except Exception:
                                    pass
                            if build_statuses:
                                # Send as JSON so frontend can parse per-build status
                                import json
                                progress = json.dumps(build_statuses)
                    except Exception:
                        pass

                if progress and progress != last_progress:
                    last_progress = progress
                    elapsed = time.perf_counter() - start
                    result_q.put(
                        {
                            "type": "progress",
                            "package": pkg,
                            "build_progress": progress,
                            "elapsed": round(elapsed, 1),
                        }
                    )

                time.sleep(0.2)

        # Clean up status file
        if status_file and status_file.exists():
            try:
                status_file.unlink()
            except Exception:
                pass

        secs = max(0.0, time.perf_counter() - start)
        try:
            txt = log_path.read_text(encoding="utf-8")
        except Exception:
            txt = ""
        warn, err = _count_log_levels(txt)
        return int(rc), secs, warn, err

    while True:
        task = task_q.get()
        pkg = str(task.get("package") or "")
        if not pkg:
            continue
        pkg_dir = Path(str(task["package_dir"]))
        pkg_run_dir = Path(str(task["run_dir"]))
        logs_dir = pkg_run_dir / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)

        # Build
        build_log_path = logs_dir / "build.log"
        per_pkg_jobs = int(task.get("jobs_per_pkg") or jobs_per_pkg or 1)
        cmd = [*ato_cmd, "build", "--jobs", str(max(1, per_pkg_jobs)), "-t", "all"]
        if keep_picked_parts:
            cmd.append("--keep-picked-parts")
        status_file = logs_dir / "build_status.txt"
        b_rc, b_secs, b_warn, b_err = run_cmd_to_log(
            cmd=cmd,
            cwd=pkg_dir,
            log_path=build_log_path,
            pkg=pkg,
            step="build",
            status_file=status_file,
        )

        # If cancelled mid-build, stop early.
        if cancelled(pkg):
            result_q.put(
                {
                    "type": "result",
                    "package": pkg,
                    "status": "paused",
                    "error": f"paused during build (rc={b_rc})",
                }
            )
            continue

        # Parse per-target summary if available.
        build_logs: dict[str, str] = {}
        build_rc: dict[str, int] = {}
        build_seconds: dict[str, float] = {}
        build_warn: dict[str, int] = {}
        build_err: dict[str, int] = {}

        summary_path = pkg_dir / "build" / "logs" / "latest" / "summary.md"
        per_target: dict[str, dict[str, object]] = {}
        if summary_path.exists():
            try:
                per_target = _parse_build_summary_md(
                    summary_path.read_text(encoding="utf-8")
                )
            except Exception:
                per_target = {}

        for name in list(task.get("build_names") or []):
            bname = str(name)
            candidate = pkg_dir / "build" / "logs" / "latest" / bname / "build.log"
            build_logs[bname] = str(candidate) if candidate.exists() else str(build_log_path)
            rec = per_target.get(bname)
            if rec:
                st = str(rec.get("status", "success"))
                build_seconds[bname] = float(rec.get("seconds", 0.0))  # type: ignore[arg-type]
                build_warn[bname] = int(rec.get("warn", 0))  # type: ignore[arg-type]
                build_err[bname] = int(rec.get("err", 0))  # type: ignore[arg-type]
                build_rc[bname] = 0 if st in ("success", "warning") else 1
            else:
                build_seconds[bname] = 0.0
                build_warn[bname] = 0
                build_err[bname] = 0
                build_rc[bname] = b_rc

        if b_rc != 0:
            result_q.put(
                {
                    "type": "result",
                    "package": pkg,
                    "status": "error",
                    "error": f"build failed (rc={b_rc})",
                    "build_logs": build_logs,
                    "build_rc": build_rc,
                    "build_seconds": build_seconds,
                    "build_warn": build_warn,
                    "build_err": build_err,
                }
            )
            continue

        # Verify
        v_log = logs_dir / "verify.log"
        v_cmd = [*ato_cmd, "package", "verify", "-s"]
        verify_status_file = logs_dir / "verify_status.txt"
        v_rc, v_secs, v_warn, v_err = run_cmd_to_log(
            cmd=v_cmd,
            cwd=pkg_dir,
            log_path=v_log,
            pkg=pkg,
            step="verify",
            status_file=verify_status_file,
        )

        if cancelled(pkg):
            result_q.put(
                {
                    "type": "result",
                    "package": pkg,
                    "status": "paused",
                    "error": f"paused during verify (rc={v_rc})",
                    "build_logs": build_logs,
                    "build_rc": build_rc,
                    "build_seconds": build_seconds,
                    "build_warn": build_warn,
                    "build_err": build_err,
                    "verify_log": str(v_log),
                    "verify_rc": v_rc,
                    "verify_seconds": v_secs,
                    "verify_warn": v_warn,
                    "verify_err": v_err,
                }
            )
            continue

        if v_rc == 0:
            status = "awaiting_review"
            err_msg = None
        else:
            status = "error"
            err_msg = f"verify failed (rc={v_rc})"

        result_q.put(
            {
                "type": "result",
                "package": pkg,
                "status": status,
                "error": err_msg,
                "build_logs": build_logs,
                "build_rc": build_rc,
                "build_seconds": build_seconds,
                "build_warn": build_warn,
                "build_err": build_err,
                "verify_log": str(v_log),
                "verify_rc": v_rc,
                "verify_seconds": v_secs,
                "verify_warn": v_warn,
                "verify_err": v_err,
            }
        )


def _count_log_levels_path(p: Path, *, max_bytes: int = 2_000_000) -> tuple[int, int]:
    """
    Count warning/error markers from a log file, best-effort.
    We cap bytes to avoid UI endpoints doing heavy work on giant logs.
    """
    try:
        with p.open("rb") as f:
            data = f.read(max_bytes)
        txt = data.decode("utf-8", errors="replace")
    except Exception:
        txt = ""
    return _count_log_levels(txt)


def _get_git_hash(cwd: Path) -> str | None:
    """
    Get the short git hash of the repo at cwd.
    """
    try:
        r = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
        )
        if r.returncode == 0:
            return r.stdout.strip()
    except Exception:
        pass
    return None


def _safe_cmd_version(cmd: list[str], *, cwd: Path) -> str | None:
    """
    Best-effort version probe for a CLI.
    Returns a short string (first line) or None.
    """
    try:
        r = subprocess.run(
            [*cmd, "--version"],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
        )
        out = (r.stdout or r.stderr or "").strip()
        if not out:
            return None
        return out.splitlines()[0].strip()
    except Exception:
        return None


def _pr_title_and_body(
    *,
    job: "JobState",
    package: str,
    branch: str,
    reviewer: str | None,
    target_requires_atopile: str,
    old_version: str | None,
    new_version: str | None,
    git_hash: str | None,
    changelog: str | None = None,
) -> tuple[str, str]:
    """
    Deterministic PR title/body (avoid gh --fill so this is stable across reruns).

    Format:
    Title: {package}: package update to v{new_version}, ato:{target_requires_atopile}
    Body: build targets, verify status, version, requires ato, changelog
    """
    # Title format: package: package update to vX.Y.Z, ato:^0.14.0
    version_part = f"to v{new_version}, " if new_version else ""
    title = f"{package}: package update {version_part}ato:{target_requires_atopile}"

    lines: list[str] = []

    # Build targets section
    lines.append("**Build targets:**")
    for b in job.build_names:
        rc = job.build_rc.get(b, "?")
        lines.append(f"- `{b}` = rc{rc}")
    lines.append("")

    # Package verify
    if job.verify_rc is not None:
        lines.append(f"**Package Verify:** rc{job.verify_rc}")
    lines.append("")

    # Version
    if old_version and new_version:
        lines.append(f"**Version:** {old_version} → {new_version}")
    elif new_version:
        lines.append(f"**Version:** {new_version}")
    lines.append("")

    # Requires ato
    lines.append(f"**Requires ato:** {target_requires_atopile}")
    lines.append("")

    # Changelog section
    lines.append("**Changelog:**")
    if changelog:
        for line in changelog.strip().split("\n"):
            lines.append(f"- {line.strip()}")
    else:
        lines.append("- Package update for new atopile version")
    lines.append("")

    # Metadata (collapsed details)
    lines.append("<details>")
    lines.append("<summary>Build metadata</summary>")
    lines.append("")
    lines.append(f"- Built at: `{job.started_at or '?'}` → `{job.finished_at or '?'}`")
    lines.append(f"- Machine: `{platform.node()}`")
    lines.append(f"- User: `{getpass.getuser()}`")
    if git_hash:
        lines.append(f"- Repo commit: `{git_hash}`")
    lines.append(f"- Approved by: `{job.approved_by or 'N/A'}`")
    lines.append(f"- Published by: `{reviewer or 'N/A'}`")
    lines.append("")
    lines.append("</details>")

    body = "\n".join(lines).strip() + "\n"
    return title, body


def _tail(text: str, n_lines: int = 80) -> str:
    lines = text.splitlines()
    if len(lines) <= n_lines:
        return text
    return "\n".join(lines[-n_lines:])


def _tail_file(path: Path, *, max_bytes: int = 64_000, n_lines: int = 120) -> str:
    """
    Efficiently tail a potentially large file without reading it all into memory.
    """
    try:
        with path.open("rb") as f:
            f.seek(0, os.SEEK_END)
            size = f.tell()
            start = max(0, size - max_bytes)
            f.seek(start, os.SEEK_SET)
            data = f.read()
        txt = data.decode("utf-8", errors="replace")
        return _tail(txt, n_lines=n_lines)
    except Exception:
        return ""


def _git_config(packages_repo_root: Path, key: str) -> str | None:
    try:
        r = subprocess.run(
            ["git", "config", "--get", key],
            cwd=packages_repo_root,
            capture_output=True,
            text=True,
            check=False,
        )
        v = (r.stdout or "").strip()
        return v or None
    except Exception:
        return None


def _bump_minor(version: str) -> str:
    major_s, minor_s, patch_s = version.strip().split(".")
    major, minor, _patch = int(major_s), int(minor_s), int(patch_s)
    return f"{major}.{minor + 1}.0"


def _bump_patch(version: str) -> str:
    major_s, minor_s, patch_s = version.strip().split(".")
    major, minor, patch = int(major_s), int(minor_s), int(patch_s)
    return f"{major}.{minor}.{patch + 1}"


def _rewrite_ato_yaml_for_publish(
    ato_yaml: Path, required_atopile: str = "^0.14.0"
) -> tuple[str | None, str | None]:
    """
    Update:
    - requires-atopile: -> ^0.14.0 (by default)
    - package.version: bump minor

    Returns (old_version, new_version).
    """
    txt = ato_yaml.read_text(encoding="utf-8")

    # requires-atopile
    txt2 = re.sub(
        r"(?m)^requires-atopile:\s*.*$",
        f"requires-atopile: {required_atopile}",
        txt,
        count=1,
    )

    # version bump (first occurrence under package section)
    m = re.search(r'(?m)^\s*version:\s*("?)(\d+\.\d+\.\d+)\1\s*$', txt2)
    old_v = None
    new_v = None
    if m:
        old_v = m.group(2)
        new_v = _bump_minor(old_v)
        quote = m.group(1)
        txt2 = re.sub(
            r'(?m)^(\s*version:\s*)("?)(\d+\.\d+\.\d+)\2\s*$',
            rf"\g<1>{quote}{new_v}{quote}",
            txt2,
            count=1,
        )

    if txt2 != txt:
        ato_yaml.write_text(txt2, encoding="utf-8")
    return old_v, new_v


def _series_tag_from_requires_atopile(required_atopile: str) -> str:
    """
    Convert requires-atopile strings to a short series tag for branch names.

    Examples:
    - "^0.14.0" -> "0.14.x"
    - "0.14.2"  -> "0.14.x"
    - "0.14.x"  -> "0.14.x"
    """
    s = (required_atopile or "").strip()
    m = re.search(r"(\d+)\.(\d+)(?:\.(\d+|x))?", s)
    if not m:
        return "unknown"
    major = m.group(1)
    minor = m.group(2)
    return f"{major}.{minor}.x"


def _slugify_branch_component(s: str) -> str:
    """
    Git branch-safe-ish slug. (We still rely on git to reject truly invalid names.)
    """
    s = (s or "").strip().lower()
    s = re.sub(r"[^a-z0-9._-]+", "-", s)
    s = re.sub(r"-{2,}", "-", s).strip("-")
    return s or "x"


def _check_existing_pr_for_package(
    package: str,
    repo_root: Path,
    target_requires_atopile: str = "^0.14.0",
) -> dict[str, Any] | None:
    """
    Check if there's an existing PR (open or merged) for this package on GitHub.

    Returns dict with branch/pr_url/merged if found, None otherwise.
    Requires `gh` CLI to be installed and authenticated.
    """
    if not shutil.which("gh"):
        return None

    series = _series_tag_from_requires_atopile(target_requires_atopile)
    expected_branch = f"package-update-{_slugify_branch_component(series)}-{_slugify_branch_component(package)}"

    try:
        # Check if there's an open or merged PR for this branch
        result = subprocess.run(
            ["gh", "pr", "view", "--head", expected_branch, "--json", "url,state,title"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0 and result.stdout.strip():
            import json as json_mod
            pr_info = json_mod.loads(result.stdout.strip())
            state = pr_info.get("state")
            if state == "OPEN":
                return {
                    "branch": expected_branch,
                    "pr_url": pr_info.get("url"),
                    "pr_title": pr_info.get("title"),
                    "merged": False,
                }
            elif state == "MERGED":
                return {
                    "branch": expected_branch,
                    "pr_url": pr_info.get("url"),
                    "pr_title": pr_info.get("title"),
                    "merged": True,
                }
    except Exception:
        pass

    # Search for merged PRs by title pattern (for cases where branch was deleted)
    # This catches PRs that were merged with the standard title format
    try:
        search_query = f"{package}: package update"
        result = subprocess.run(
            [
                "gh", "pr", "list",
                "--state", "merged",
                "--search", search_query,
                "--json", "url,title,mergedAt",
                "--limit", "5",
            ],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0 and result.stdout.strip():
            import json as json_mod
            prs = json_mod.loads(result.stdout.strip())
            # Look for a PR with matching package name and 0.14 in title
            for pr in prs:
                title = pr.get("title", "")
                # Match PRs like "adi-adxl345: package update to v0.2.0, ato:^0.14.0"
                if title.startswith(f"{package}:") and "0.14" in title:
                    return {
                        "branch": expected_branch,
                        "pr_url": pr.get("url"),
                        "pr_title": title,
                        "merged": True,
                    }
    except Exception:
        pass

    # Also check if the branch exists on remote (even without PR)
    try:
        result = subprocess.run(
            ["git", "ls-remote", "--heads", "origin", expected_branch],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0 and expected_branch in (result.stdout or ""):
            return {
                "branch": expected_branch,
                "pr_url": None,
                "merged": False,
            }
    except Exception:
        pass

    return None


def _extract_issues_for_job(job: "JobState") -> list[dict[str, Any]]:
    """
    Extract all errors/warnings from logs for a job.

    Returns list of issues with:
    - type: "error" | "warning"
    - message: the log line content
    - source: which log file/build step produced it
    """
    run_logs_dir = (Path(job.run_dir) / "logs").resolve()
    pkg_build_latest = (Path(job.package_dir) / "build" / "logs" / "latest").resolve()

    issues: list[dict[str, Any]] = []

    # Patterns for matching errors/warnings
    error_pattern = re.compile(r"\bERROR\b", re.IGNORECASE)
    warning_pattern = re.compile(r"\bWARNING\b", re.IGNORECASE)
    traceback_pattern = re.compile(r"^Traceback \(most recent call last\):", re.MULTILINE)

    def extract_from_log(
        log_path: Path,
        source_label: str,
        stage: str,
        max_bytes: int = 2_000_000,
    ) -> None:
        """Extract errors/warnings from a single log file."""
        if not log_path.exists():
            return
        try:
            with log_path.open("rb") as f:
                data = f.read(max_bytes)
            txt = data.decode("utf-8", errors="replace")
        except Exception:
            return

        lines = txt.splitlines()
        in_traceback = False

        for i, line in enumerate(lines):
            line_num = i + 1

            if traceback_pattern.match(line):
                in_traceback = True
                continue

            if in_traceback:
                if not line.strip() or error_pattern.search(line) or warning_pattern.search(line):
                    in_traceback = False
                else:
                    continue

            if error_pattern.search(line):
                clean_line = re.sub(r"\x1b\[[0-9;]*m", "", line).strip()
                if len(clean_line) > 10:
                    issues.append({
                        "type": "error",
                        "message": clean_line,
                        "source": source_label,
                        "stage": stage,
                        "line_num": line_num,
                    })
            elif warning_pattern.search(line):
                clean_line = re.sub(r"\x1b\[[0-9;]*m", "", line).strip()
                if len(clean_line) > 10:
                    issues.append({
                        "type": "warning",
                        "message": clean_line,
                        "source": source_label,
                        "stage": stage,
                        "line_num": line_num,
                    })

    # Extract from review-station build logs
    for b in job.build_names:
        fname = f"build.{b}.log"
        extract_from_log(run_logs_dir / fname, f"build ({b})", "build")

    # Extract from verify log
    extract_from_log(run_logs_dir / "verify.log", "verify", "verify")

    # Extract from package internal logs
    if pkg_build_latest.exists():
        for b in job.build_names:
            bdir = pkg_build_latest / b
            if not bdir.exists() or not bdir.is_dir():
                continue
            for p in sorted(bdir.iterdir()):
                if not p.is_file():
                    continue
                if not (p.name.endswith(".log") or p.name.endswith(".txt")):
                    continue
                extract_from_log(p, f"{b} / {p.name}", "build")

    # Sort: errors first, then by stage, then by line number
    stage_order = {"build": 0, "verify": 1, "other": 2}
    issues.sort(key=lambda x: (
        0 if x["type"] == "error" else 1,
        stage_order.get(x["stage"], 2),
        x["line_num"],
    ))

    # Deduplicate similar messages
    seen_messages: set[str] = set()
    unique_issues: list[dict[str, Any]] = []
    for issue in issues:
        norm = re.sub(r"\d+", "N", issue["message"][:100])
        if norm not in seen_messages:
            seen_messages.add(norm)
            unique_issues.append(issue)

    return unique_issues


def _update_todo_auto_section(
    *,
    todo_path: Path,
    job: "JobState",
    server_origin: str,
) -> None:
    """
    Maintain an auto-generated section in the per-package TODO file.
    This section is rewritten on status/log updates without clobbering user notes.
    """
    todo_path.parent.mkdir(parents=True, exist_ok=True)
    existing = todo_path.read_text(encoding="utf-8") if todo_path.exists() else ""

    build_lines = []
    for b in job.build_names:
        rc = job.build_rc.get(b)
        warn = job.build_warn.get(b, 0)
        err = job.build_err.get(b, 0)
        sec = job.build_seconds.get(b)
        sec_str = f"{sec:.1f}s" if isinstance(sec, (int, float)) else "?"
        lp = f"{server_origin}/log/{job.package}/build.{b}.log"
        pcb = job.layout_paths.get(b)
        pcb_link = f"{server_origin}/pcb/{job.package}/{b}"
        build_lines.append(
            f"- **{b}**: rc={rc}  warn/err={warn}/{err}  time={sec_str}  log: `{lp}`"
            + (f"  pcb: `{pcb}` (viewer: `{pcb_link}`)" if pcb else "")
        )

    verify_line = ""
    if job.verify_rc is not None:
        vl = f"{server_origin}/log/{job.package}/verify.log"
        verify_line = f"- **verify**: rc={job.verify_rc} warn/err={(job.verify_warn or 0)}/{(job.verify_err or 0)} time={(job.verify_seconds or 0):.1f}s log: `{vl}`"

    # API URLs for this package
    pkg_encoded = job.package.replace(" ", "%20")
    status_url = f"{server_origin}/api/package/{pkg_encoded}/status"
    rebuild_url = f"{server_origin}/api/package/{pkg_encoded}/restart"
    issues_url = f"{server_origin}/api/package/{pkg_encoded}/issues"

    message_url = f"{server_origin}/api/package/{pkg_encoded}/message"
    help_url = f"{server_origin}/api/package/{pkg_encoded}/request_help"
    logs_url = f"{server_origin}/api/package/{pkg_encoded}/logs"
    health_url = f"{server_origin}/api/health"

    auto = []
    auto.append(AUTO_BEGIN)
    auto.append("## Instructions for AI")
    auto.append("")
    auto.append(f"**Package**: `{job.package}`")
    auto.append(f"**Directory**: `{job.package_dir}`")
    auto.append("")
    auto.append("Review and fix the errors and warnings listed below. The main source files are:")
    auto.append(f"- `{job.package_dir}/{job.package}.ato` - main module")
    auto.append(f"- `{job.package_dir}/usage.ato` - usage example")
    auto.append(f"- `{job.package_dir}/ato.yaml` - build config")
    auto.append("")
    auto.append("### ⚠️ IMPORTANT: Use API to communicate with user!")
    auto.append("")
    auto.append("The user is watching a live dashboard. **Use these commands to communicate:**")
    auto.append("1. **Send `started` message FIRST** - so user knows you're working on it")
    auto.append("2. **Post progress updates** - user sees these in real-time")
    auto.append("3. **Request help if stuck** - highlights package for user attention")
    auto.append("4. **Send `finished` message LAST** - when done (success or giving up)")
    auto.append("")
    auto.append("### API Commands")
    auto.append("")
    auto.append("```bash")
    auto.append("# FIRST: Mark yourself as working on this package")
    auto.append(f"curl -X POST '{message_url}' -H 'Content-Type: application/json' \\")
    auto.append('  -d \'{"message": "Starting work on this package", "type": "started"}\'')
    auto.append("")
    auto.append("# Check build queue health")
    auto.append(f"curl -s '{health_url}' | jq .")
    auto.append("")
    auto.append("# Check current build status (includes progress, elapsed time, hints)")
    auto.append(f"curl -s '{status_url}' | jq .")
    auto.append("")
    auto.append("# Stream real-time updates (SSE) - great for watching builds")
    auto.append(f"curl -N '{server_origin}/api/package/{pkg_encoded}/stream'")
    auto.append("")
    auto.append("# Bump to front of queue (priority rebuild)")
    auto.append(f"curl -X POST '{server_origin}/api/package/{pkg_encoded}/prioritize'")
    auto.append("")
    auto.append("# List available log files")
    auto.append(f"curl -s '{logs_url}' | jq .")
    auto.append("")
    auto.append("# Trigger a rebuild after making fixes")
    auto.append(f"curl -X POST '{rebuild_url}'")
    auto.append("")
    auto.append("# Get detailed list of errors/warnings")
    auto.append(f"curl -s '{issues_url}' | jq .")
    auto.append("")
    auto.append("# Post a progress message (shown live in UI)")
    auto.append(f"curl -X POST '{message_url}' -H 'Content-Type: application/json' \\")
    auto.append('  -d \'{"message": "Working on fixing import errors...", "type": "progress"}\'')
    auto.append("")
    auto.append("# Request human assistance (highlights package in UI)")
    auto.append(f"curl -X POST '{help_url}' -H 'Content-Type: application/json' \\")
    auto.append('  -d \'{"reason": "Need help understanding the circuit topology"}\'')
    auto.append("")
    auto.append("# LAST: Mark yourself as done (success or giving up)")
    auto.append(f"curl -X POST '{message_url}' -H 'Content-Type: application/json' \\")
    auto.append('  -d \'{"message": "Fixed all issues, build passes", "type": "finished"}\'')
    auto.append("```")
    auto.append("")
    auto.append("**Tips:**")
    auto.append("- Status shows `current_step` and `build_progress` while building")
    auto.append("- Use `/api/package/{name}/prioritize` (POST) to bump to front of queue")
    auto.append("- Use `/api/package/{name}/stream` (GET) for real-time SSE updates")
    auto.append("- Message types: `started`, `finished`, `info`, `progress`, `warning`, `error`, `question`")
    auto.append("")
    auto.append("---")
    auto.append("")
    auto.append("## Auto summary (do not edit)")
    auto.append(f"- **status**: `{job.status}`")
    if job.package_identifier:
        auto.append(f"- **identifier**: `{job.package_identifier}`")
    if job.registry_requires_atopile:
        upd = "✅" if job.registry_updated_014 else "—"
        ver = (
            f" (published ver: `{job.registry_published_version}`)"
            if job.registry_published_version
            else ""
        )
        auto.append(
            f"- **registry**: requires-atopile `{job.registry_requires_atopile}` (0.14.x updated: {upd}){ver}"
        )
    elif job.registry_checked_at and job.registry_error:
        auto.append(
            f"- **registry**: error `{job.registry_error}` @ `{job.registry_checked_at}`"
        )
    if job.error:
        auto.append(f"- **error**: `{job.error}`")
    if job.started_at:
        auto.append(f"- **started**: `{job.started_at}`")
    if job.finished_at:
        auto.append(f"- **finished**: `{job.finished_at}`")
    if job.approved_by:
        auto.append(f"- **approved**: `{job.approved_by}` @ `{job.approved_at}`")
    if job.cancel_requested:
        auto.append(
            f"- **skip requested**: `{job.skip_reason or ''}` @ `{job.skip_requested_at or '?'}` (step: `{job.current_step or '?'}`)"
        )
    auto.append("")
    auto.append("### Build logs")
    auto.extend(build_lines or ["- (no builds yet)"])
    auto.append("")
    auto.append("### Verify")
    auto.append(verify_line or "- (not run yet)")

    # Extract and include issues (errors/warnings)
    try:
        issues = _extract_issues_for_job(job)
        if issues:
            errors = [i for i in issues if i["type"] == "error"]
            warnings = [i for i in issues if i["type"] == "warning"]

            auto.append("")
            auto.append(f"### Issues ({len(errors)} errors, {len(warnings)} warnings)")

            if errors:
                auto.append("")
                auto.append("#### Errors")
                for issue in errors[:20]:  # Limit to first 20
                    # Truncate long messages
                    msg = issue["message"]
                    if len(msg) > 120:
                        msg = msg[:117] + "..."
                    auto.append(f"- `{issue['source']}`: {msg}")
                if len(errors) > 20:
                    auto.append(f"- ... and {len(errors) - 20} more errors")

            if warnings:
                auto.append("")
                auto.append("#### Warnings")
                for issue in warnings[:20]:  # Limit to first 20
                    msg = issue["message"]
                    if len(msg) > 120:
                        msg = msg[:117] + "..."
                    auto.append(f"- `{issue['source']}`: {msg}")
                if len(warnings) > 20:
                    auto.append(f"- ... and {len(warnings) - 20} more warnings")
    except Exception:
        pass  # Don't fail todo update if issue extraction fails

    auto.append(AUTO_END)
    auto_text = "\n".join(auto) + "\n"

    if AUTO_BEGIN in existing and AUTO_END in existing:
        pre = existing.split(AUTO_BEGIN)[0]
        post = existing.split(AUTO_END)[1]
        merged = pre + auto_text + post.lstrip("\n")
    else:
        merged = (existing.rstrip() + "\n\n" if existing.strip() else "") + auto_text

    if merged != existing:
        todo_path.write_text(merged, encoding="utf-8")


@dataclass
class JobState:
    package: str
    package_dir: str
    build_names: list[str]
    status: Status = "not_started"
    started_at: str | None = None
    finished_at: str | None = None
    error: str | None = None

    # Paths created per run
    run_dir: str = ""
    todo_path: str = ""

    # Outputs
    build_logs: dict[str, str] = field(default_factory=dict)  # build -> log file path
    verify_log: str | None = None
    build_rc: dict[str, int] = field(default_factory=dict)
    verify_rc: int | None = None
    build_seconds: dict[str, float] = field(default_factory=dict)
    verify_seconds: float | None = None
    build_warn: dict[str, int] = field(default_factory=dict)
    build_err: dict[str, int] = field(default_factory=dict)
    verify_warn: int | None = None
    verify_err: int | None = None
    layout_paths: dict[str, str] = field(default_factory=dict)
    model_paths: dict[str, str] = field(default_factory=dict)  # build -> glb
    build_entries: dict[str, str] = field(
        default_factory=dict
    )  # build -> entry (file.ato:Module)
    approved_by: str | None = None
    approved_at: str | None = None

    # User-initiated skip/stop (cancellation is cooperative for running subprocesses)
    cancel_requested: bool = False
    skip_reason: str | None = None
    skip_requested_at: str | None = None
    current_step: str | None = None  # e.g. "build:<name>" / "verify"
    current_pid: int | None = None
    build_progress: str | None = None  # e.g. "Picking parts 3/10"

    # Registry metadata (best-effort, optional)
    package_identifier: str | None = None
    registry_requires_atopile: str | None = None
    registry_checked_at: str | None = None
    registry_error: str | None = None
    registry_updated_014: bool = False
    registry_published_version: str | None = None

    # Publish/push metadata (local automation)
    published_branch: str | None = None
    published_at: str | None = None
    published_target_requires_atopile: str | None = None
    publish_error: str | None = None
    published_pr_url: str | None = None
    published_pr_title: str | None = None
    published_pr_body: str | None = None

    # Flag to skip PR check after manual restart (allows re-publishing to existing branch)
    skip_pr_check: bool = False

    # AI agent interaction
    agent_messages: list[dict[str, Any]] = field(default_factory=list)
    agent_working: bool = False  # True if an LLM is actively working on this package
    agent_working_since: str | None = None
    needs_input_reason: str | None = None  # Why the AI requested help
    needs_input_at: str | None = None

    def to_public(self) -> dict[str, Any]:
        return asdict(self)


class ReviewRun:
    def __init__(
        self,
        *,
        packages_root: Path,
        selected_packages: list[Path],
        jobs: int,
        run_dir: Path,
        ato_cmd: list[str],
        keep_picked_parts: bool,
        open_cmd: str,
        max_ready: int = 10,
        server_origin: str = "http://127.0.0.1:8787",
        packages_repo_root: Path | None = None,
        publish_anyway: bool = False,
        registry_url: str = "https://packages.atopileapi.com",
        registry_refresh_seconds: float = 60.0,
    ):
        self.packages_root = packages_root
        self.packages_repo_root = packages_repo_root or packages_root.parent.resolve()
        self.selected_packages = selected_packages
        self.jobs = max(1, jobs)
        self.run_dir = run_dir
        # Tests (and some callers) may pass a fresh directory; ensure it exists before we
        # start writing state/logs.
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self.ato_cmd = ato_cmd
        self.keep_picked_parts = keep_picked_parts
        self.open_cmd = open_cmd
        self.max_ready = max(1, max_ready)
        self.server_origin = server_origin.rstrip("/")
        # If True, allow publishing even if build/verify have not completed successfully.
        # Useful for testing the git/gh plumbing or for emergency pushes.
        self.publish_anyway = bool(publish_anyway)
        self.registry_url = registry_url.rstrip("/")
        self.registry_refresh_seconds = max(5.0, float(registry_refresh_seconds))

        self._lock = threading.Lock()
        # Serialize writes of `state.json` on disk (multiple workers may call `_write_state()`).
        # This lock MUST NOT be held while we hold `self._lock` to avoid deadlocks.
        self._state_io_lock = threading.Lock()
        self._jobs: dict[str, JobState] = {}
        self._queue: list[str] = []
        self._threads: list[threading.Thread] = []
        self._stop = False
        # Cached state snapshot for the UI.
        # Important: `/api/state` is hit frequently; serializing a huge dict on every request
        # can stall the server. We refresh this cache only when state changes.
        self._state_cache: dict[str, Any] = {}
        self._state_cache_json: bytes = b"{}"

        for pkg_dir in selected_packages:
            build_names = _read_ato_yaml_builds(pkg_dir / "ato.yaml")
            build_entries = _read_ato_yaml_build_entries(pkg_dir / "ato.yaml")
            pkg_run_dir = run_dir / pkg_dir.name
            # Store TODO in the package directory so it persists across sessions
            todo_path = pkg_dir / "review.todo.md"
            js = JobState(
                package=pkg_dir.name,
                package_dir=str(pkg_dir),
                build_names=build_names,
                run_dir=str(pkg_run_dir),
                todo_path=str(todo_path),
            )
            js.package_identifier = _read_ato_yaml_package_identifier(
                pkg_dir / "ato.yaml"
            )
            js.build_entries = build_entries
            # Seed layout/model paths from the package directory so KiCanvas can render even
            # before a build has completed (layouts are typically checked into the package).
            js.layout_paths = _find_layout_pcb_paths(pkg_dir, build_names)
            js.model_paths = _find_model_glb_paths(pkg_dir, build_names)

            self._jobs[pkg_dir.name] = js
            self._queue.append(pkg_dir.name)

        self._write_state()

    def start(self) -> None:
        # One UI process owns state + scheduling; spawn N worker processes to run builds.
        #
        # Worker processes communicate back via a result queue; the UI process applies
        # updates and persists `state.json`.
        self._mp_manager = mp.Manager()
        self._mp_cancel = self._mp_manager.dict()  # package -> bool
        self._mp_tasks: mp.Queue[dict[str, Any]] = mp.Queue()
        self._mp_results: mp.Queue[dict[str, Any]] = mp.Queue()
        self._mp_procs: list[mp.Process] = []

        for i in range(self.jobs):
            p = mp.Process(
                target=_review_worker_process,
                name=f"review-worker-proc-{i}",
                args=(
                    self._mp_tasks,
                    self._mp_results,
                    self._mp_cancel,
                    self.ato_cmd,
                    self.keep_picked_parts,
                    max(1, (os.cpu_count() or 4) // max(1, self.jobs)),
                ),
                daemon=True,
            )
            p.start()
            self._mp_procs.append(p)

        # Single orchestrator thread: dispatch work + apply results.
        t = threading.Thread(
            target=self._orchestrate,
            name="review-orchestrator",
            daemon=True,
        )
        t.start()
        self._threads.append(t)

        t = threading.Thread(
            target=self._registry_poller, name="registry-poller", daemon=True
        )
        t.start()
        self._threads.append(t)

        # Background thread to check for existing PRs while builds run
        t = threading.Thread(
            target=self._check_existing_prs_background,
            name="pr-checker",
            daemon=True,
        )
        t.start()
        self._threads.append(t)

    def _check_existing_prs_background(self) -> None:
        """
        Background thread that checks for existing PRs/branches while builds run.

        If a package is found to already be published (merged PR or on registry),
        we update its status and cancel any running build for it.
        """
        # Small delay to let server fully start
        time.sleep(0.5)

        with self._lock:
            packages_to_check = list(self._jobs.keys())

        for pkg_name in packages_to_check:
            if self._stop:
                break

            already_published = False
            pr_info: dict[str, Any] | None = None

            # First, quick check: is this package already on the registry for 0.14.x?
            try:
                with self._lock:
                    job = self._jobs.get(pkg_name)
                    if job and job.registry_updated_014:
                        already_published = True

                # If not yet checked by registry poller, do a quick registry check
                if not already_published and job and job.package_identifier:
                    ident = job.package_identifier
                    ident_path = quote(ident, safe="/")
                    url = f"{self.registry_url}/v1/package/{ident_path}"
                    req = Request(url, headers={"User-Agent": "packages-review-station/0"})
                    with urlopen(req, timeout=5) as r:
                        data = json.loads(r.read().decode("utf-8"))
                    latest_version = ((data or {}).get("info") or {}).get("version", "")

                    # Get release info to check requires_atopile
                    if latest_version:
                        rel_url = f"{self.registry_url}/v1/package/{ident_path}/releases/{quote(latest_version, safe='')}"
                        rel_req = Request(rel_url, headers={"User-Agent": "packages-review-station/0"})
                        with urlopen(rel_req, timeout=5) as rr:
                            rel_data = json.loads(rr.read().decode("utf-8"))
                        requires_atopile = ((rel_data or {}).get("info") or {}).get("requires_atopile", "")

                        # Already published for 0.14.x?
                        if re.match(r"^\^?0\.14\.\d+", requires_atopile):
                            already_published = True
                            with self._lock:
                                if job:
                                    job.registry_published_version = latest_version
                                    job.registry_requires_atopile = requires_atopile
                                    job.registry_updated_014 = True
            except Exception:
                pass  # Registry check failed, fall through to PR check

            # If already on registry for 0.14, mark as published
            if already_published:
                with self._lock:
                    job = self._jobs.get(pkg_name)
                    if job and job.status in ("not_started", "building", "verifying"):
                        job.status = "published"
                        if pkg_name in self._queue:
                            self._queue.remove(pkg_name)
                        if hasattr(self, "_mp_cancel"):
                            try:
                                self._mp_cancel[pkg_name] = True
                            except Exception:
                                pass
                self._write_state()
                time.sleep(0.02)
                continue

            # Fall back to PR check
            try:
                pr_info = _check_existing_pr_for_package(
                    package=pkg_name,
                    repo_root=self.packages_repo_root,
                )
                if pr_info:
                    with self._lock:
                        job = self._jobs.get(pkg_name)
                        if not job:
                            continue

                        # Determine new status
                        if pr_info.get("merged"):
                            new_status = "published"
                        elif pr_info.get("pr_url"):
                            new_status = "pr_opened"
                        else:
                            new_status = "branch_pushed"

                        # Only update if package hasn't already completed or errored
                        if job.status in ("not_started", "building", "verifying"):
                            job.published_branch = pr_info.get("branch")
                            job.published_pr_url = pr_info.get("pr_url")
                            job.published_pr_title = pr_info.get("pr_title")
                            job.status = new_status

                            # Remove from queue if still queued
                            if pkg_name in self._queue:
                                self._queue.remove(pkg_name)

                            # Cancel build if running
                            if hasattr(self, "_mp_cancel"):
                                try:
                                    self._mp_cancel[pkg_name] = True
                                except Exception:
                                    pass

                    self._write_state()
            except Exception:
                pass  # Don't crash the thread on individual failures

            # Small delay between checks to avoid hammering APIs
            time.sleep(0.02)

    def stop(self) -> None:
        self._stop = True

    def _orchestrate(self) -> None:
        """
        Scheduler loop (UI process).

        - Dispatch packages into the worker process pool
        - Apply worker results back into in-memory state
        """
        while not self._stop:
            # Apply any pending results quickly.
            try:
                while True:
                    msg = self._mp_results.get_nowait()
                    self._apply_worker_msg(msg)
            except Exception:
                pass

            # Dispatch next work if we have capacity and haven't exceeded max_ready.
            self._dispatch_next()
            time.sleep(0.05)

    def _dispatch_next(self) -> None:
        with self._lock:
            ready = sum(
                1 for j in self._jobs.values() if j.status in ("awaiting_review",)
            )
            in_flight = sum(
                1
                for j in self._jobs.values()
                if j.status in ("building", "verifying")
            )
            if ready >= self.max_ready:
                return
            if in_flight >= self.jobs:
                return

            pkg: str | None = None
            for name in self._queue:
                j = self._jobs[name]
                if j.status != "not_started":
                    continue
                if j.cancel_requested:
                    continue
                pkg = name
                j.status = "building"
                j.started_at = _now_ts()
                j.error = None
                j.finished_at = None
                j.current_step = "build"
                j.current_pid = None
                break

        if not pkg:
            return
        self._write_state()

        job = self.get_job(pkg)
        assert job is not None
        self._mp_cancel[pkg] = False
        self._mp_tasks.put(
            {
                "package": pkg,
                "package_dir": job.package_dir,
                "run_dir": job.run_dir,
                "build_names": list(job.build_names),
                "server_origin": self.server_origin,
                "jobs_per_pkg": max(1, (os.cpu_count() or 4) // max(1, self.jobs)),
            }
        )

    def _apply_worker_msg(self, msg: dict[str, Any]) -> None:
        pkg = str(msg.get("package") or "")
        if not pkg:
            return
        typ = str(msg.get("type") or "")

        with self._lock:
            j = self._jobs.get(pkg)
            if not j:
                return

            if typ == "step":
                j.current_step = msg.get("current_step")
                j.current_pid = msg.get("current_pid")
                j.build_progress = None  # Reset progress when step changes
            elif typ == "progress":
                j.build_progress = msg.get("build_progress")
            elif typ == "result":
                # Build outputs
                j.build_logs = dict(msg.get("build_logs") or j.build_logs)
                j.build_rc = dict(msg.get("build_rc") or j.build_rc)
                j.build_seconds = dict(msg.get("build_seconds") or j.build_seconds)
                j.build_warn = dict(msg.get("build_warn") or j.build_warn)
                j.build_err = dict(msg.get("build_err") or j.build_err)

                # Verify outputs
                j.verify_log = msg.get("verify_log") or j.verify_log
                j.verify_rc = msg.get("verify_rc", j.verify_rc)
                j.verify_seconds = msg.get("verify_seconds", j.verify_seconds)
                j.verify_warn = msg.get("verify_warn", j.verify_warn)
                j.verify_err = msg.get("verify_err", j.verify_err)

                # Layout/model refresh
                try:
                    pkg_dir = Path(j.package_dir)
                    j.layout_paths = _find_layout_pcb_paths(pkg_dir, j.build_names)
                    j.model_paths = _find_model_glb_paths(pkg_dir, j.build_names)
                except Exception:
                    pass

                j.error = msg.get("error")
                j.finished_at = _now_ts()
                j.current_step = None
                j.current_pid = None
                j.build_progress = None  # Clear progress when complete

                status = msg.get("status")
                # Don't overwrite "published"/"pr_opened"/"branch_pushed" with "paused"
                # (background checker may have already marked this package)
                if j.status in ("published", "pr_opened", "branch_pushed"):
                    pass  # Keep the status set by background checker
                elif status in (
                    "awaiting_review",
                    "error",
                    "paused",
                ):
                    j.status = status
                else:
                    j.status = "error"
                    j.error = j.error or f"unknown worker status: {status!r}"

                # Auto-resume jobs that were paused for priority rebuild
                if j.status == "paused" and j.skip_reason and "paused for priority rebuild" in j.skip_reason:
                    j.status = "not_started"
                    j.cancel_requested = False
                    j.skip_reason = None
                    j.skip_requested_at = None
                    j.error = None
                    j.finished_at = None
                    # Keep partial build results but allow rebuild

                # If build/verify passed, check if there's already a PR for this package
                # Skip this check if package was manually restarted (to allow re-publishing)
                if j.status == "awaiting_review" and not j.skip_pr_check:
                    existing = _check_existing_pr_for_package(
                        package=pkg,
                        repo_root=self.packages_repo_root,
                    )
                    if existing:
                        j.published_branch = existing.get("branch")
                        j.published_pr_url = existing.get("pr_url")
                        j.published_pr_title = existing.get("pr_title")
                        if existing.get("merged"):
                            # PR was already merged - package is published for this series
                            j.status = "published"
                        elif existing.get("pr_url"):
                            j.status = "pr_opened"
                        else:
                            j.status = "branch_pushed"

                # Reset skip_pr_check flag after use
                j.skip_pr_check = False

        self._write_state()
        # Keep todo updated after each completion.
        job = self.get_job(pkg)
        if job:
            _update_todo_auto_section(
                todo_path=Path(job.todo_path), job=job, server_origin=self.server_origin
            )

    def _refresh_state_cache_locked(self) -> None:
        """
        Refresh the cached state payload + pre-serialized JSON.
        Must be called with `self._lock` held.
        """
        payload = {
            "run_dir": str(self.run_dir),
            "updated_at": _now_ts(),
            "config": {
                # If True, the server will allow publishing even if build/verify are incomplete/failed.
                "publish_anyway": bool(getattr(self, "publish_anyway", False)),
            },
            "packages": {k: v.to_public() for k, v in self._jobs.items()},
            "queue": list(self._queue),
        }
        self._state_cache = payload
        # Compact JSON: much cheaper to generate and transmit than pretty JSON.
        self._state_cache_json = (
            json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
            + b"\n"
        )

    def _write_state(self) -> None:
        """
        Persist the current state to disk and refresh the cached `/api/state` payload.
        This is safe to call from anywhere; it does not hold the lock while writing.
        """
        # Snapshot under lock.
        with self._lock:
            self._refresh_state_cache_locked()
            data = self._state_cache_json

        # Keep state file always valid JSON (atomic replace).
        state_path = self.run_dir / "state.json"
        # Use a unique temp name to avoid cross-thread races.
        tmp = state_path.with_name(
            f".state.{os.getpid()}.{threading.get_ident()}.{time.time_ns()}.tmp"
        )
        state_path.parent.mkdir(parents=True, exist_ok=True)
        with self._state_io_lock:
            tmp.write_bytes(data)
            tmp.replace(state_path)

    def get_state(self) -> dict[str, Any]:
        # Prefer cached snapshot (only refreshed on state changes).
        with self._lock:
            return dict(self._state_cache)

    def get_state_json(self) -> bytes:
        """
        Fast path for `/api/state` to avoid repeated heavy JSON serialization.
        """
        with self._lock:
            return self._state_cache_json

    def get_job(self, package: str) -> JobState | None:
        with self._lock:
            return self._jobs.get(package)

    def set_todo(self, package: str, text: str) -> None:
        job = self.get_job(package)
        if not job:
            raise KeyError(package)
        p = Path(job.todo_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
        # Re-append auto section after edits so logs/links stay handy.
        _update_todo_auto_section(
            todo_path=p, job=job, server_origin=self.server_origin
        )

    def add_agent_message(self, package: str, message: str, msg_type: str = "info") -> dict[str, Any]:
        """
        Add a message from an AI agent. Messages are stored in memory and shown in the UI.

        Args:
            package: The package name
            message: The message text
            msg_type: One of "info", "progress", "warning", "error", "question", "started", "finished"

        Returns:
            The created message object
        """
        with self._lock:
            job = self._jobs.get(package)
            if not job:
                raise KeyError(package)

            ts = _now_ts()
            msg_obj = {
                "id": f"msg-{len(job.agent_messages)}",
                "type": msg_type,
                "message": message,
                "timestamp": ts,
            }
            job.agent_messages.append(msg_obj)

            # Handle special message types that affect package state
            if msg_type == "started":
                job.agent_working = True
                job.agent_working_since = ts
            elif msg_type == "finished":
                job.agent_working = False

        self._write_state()
        return msg_obj

    def get_agent_messages(self, package: str) -> list[dict[str, Any]]:
        """Get all agent messages for a package."""
        job = self.get_job(package)
        if not job:
            raise KeyError(package)
        return list(job.agent_messages)

    def clear_agent_messages(self, package: str) -> None:
        """Clear all agent messages for a package."""
        with self._lock:
            job = self._jobs.get(package)
            if not job:
                raise KeyError(package)
            job.agent_messages.clear()
        self._write_state()

    def request_user_help(self, package: str, reason: str) -> None:
        """
        AI agent requests human assistance. Puts the package in 'needs_input' status.

        Args:
            package: The package name
            reason: Why help is needed (shown in UI)
        """
        with self._lock:
            job = self._jobs.get(package)
            if not job:
                raise KeyError(package)
            # Only transition if not currently building
            if job.status in ("building", "verifying"):
                raise ValueError("Cannot request help while build is running")
            job.status = "needs_input"
            job.needs_input_reason = reason
            job.needs_input_at = _now_ts()
            # Also add as a message
            job.agent_messages.append({
                "id": f"msg-{len(job.agent_messages)}",
                "type": "question",
                "message": f"🆘 Help requested: {reason}",
                "timestamp": _now_ts(),
            })
        self._write_state()
        _update_todo_auto_section(
            todo_path=Path(job.todo_path), job=job, server_origin=self.server_origin
        )

    def resolve_help_request(self, package: str) -> None:
        """Mark a help request as resolved, returning to awaiting_review status."""
        with self._lock:
            job = self._jobs.get(package)
            if not job:
                raise KeyError(package)
            if job.status != "needs_input":
                return
            job.status = "awaiting_review"
            job.needs_input_reason = None
            job.needs_input_at = None
        self._write_state()
        _update_todo_auto_section(
            todo_path=Path(job.todo_path), job=job, server_origin=self.server_origin
        )

    def approve(self, package: str, reviewer: str | None) -> None:
        with self._lock:
            job = self._jobs.get(package)
            if not job:
                raise KeyError(package)
            job.approved_by = reviewer
            job.approved_at = _now_ts()
        self._write_state()
        _update_todo_auto_section(
            todo_path=Path(job.todo_path),
            job=job,
            server_origin=self.server_origin,
        )

    def unapprove(self, package: str) -> None:
        with self._lock:
            job = self._jobs.get(package)
            if not job:
                raise KeyError(package)
            if not job.approved_by:
                return
            job.approved_by = None
            job.approved_at = None
        self._write_state()
        _update_todo_auto_section(
            todo_path=Path(job.todo_path), job=job, server_origin=self.server_origin
        )

    def restart(self, package: str, priority: bool = True, clear_publish_state: bool = True) -> None:
        """
        Restart a package build.

        If priority=True (default), pauses one running job to make room and
        starts this package immediately for faster debugging iteration.

        If clear_publish_state=True (default), clears any previous publish state
        so the package can be rebuilt and re-published to update an existing branch/PR.
        """
        paused_pkg = None
        with self._lock:
            job = self._jobs.get(package)
            if not job:
                raise KeyError(package)
            # If this job is currently running, can't restart it
            if job.status in ("building", "verifying"):
                raise ValueError("Job is currently running")

            # Priority restart: pause another running job to make room
            if priority:
                running_jobs = [
                    (name, j) for name, j in self._jobs.items()
                    if j.status in ("building", "verifying") and name != package
                ]
                if running_jobs:
                    # Pause the first running job (will be resumed later via queue)
                    paused_pkg, paused_job = running_jobs[0]
                    paused_job.cancel_requested = True
                    paused_job.skip_requested_at = _now_ts()
                    paused_job.skip_reason = f"paused for priority rebuild of {package}"

            # Reset state but keep reviewer notes file.
            job.status = "not_started"
            job.started_at = None
            job.finished_at = None
            job.error = None
            job.build_logs.clear()
            job.verify_log = None
            job.build_rc.clear()
            job.verify_rc = None
            job.build_seconds.clear()
            job.verify_seconds = None
            job.build_warn.clear()
            job.build_err.clear()
            job.verify_warn = None
            job.verify_err = None
            job.layout_paths = _find_layout_pcb_paths(
                Path(job.package_dir), job.build_names
            )
            job.model_paths = _find_model_glb_paths(
                Path(job.package_dir), job.build_names
            )
            job.approved_by = None
            job.approved_at = None

            # Clear publish state so package can be re-published after rebuild
            if clear_publish_state:
                job.published_branch = None
                job.published_at = None
                job.published_target_requires_atopile = None
                job.publish_error = None
                job.published_pr_url = None
                job.published_pr_title = None
                job.published_pr_body = None
                # Skip PR check after rebuild so status stays as awaiting_review
                job.skip_pr_check = True
            job.cancel_requested = False
            job.skip_reason = None
            job.skip_requested_at = None
            job.current_step = None
            job.current_pid = None
            job.build_entries = _read_ato_yaml_build_entries(
                Path(job.package_dir) / "ato.yaml"
            )
            # Move to front of queue so it builds next
            self._queue = [package] + [p for p in self._queue if p != package]

        # Signal worker process to cancel the paused job (if any)
        if paused_pkg and hasattr(self, "_mp_cancel"):
            try:
                self._mp_cancel[paused_pkg] = True
            except Exception:
                pass

        self._write_state()
        _update_todo_auto_section(
            todo_path=Path(job.todo_path), job=job, server_origin=self.server_origin
        )

    def pause(self, package: str) -> None:
        """
        Pause/stop a package.

        - If the package is currently building/verifying, we request cancellation; the worker
          will terminate the running subprocess.
        - If it is not running, we immediately mark it as paused and it will not be picked up.
        """
        with self._lock:
            job = self._jobs.get(package)
            if not job:
                raise KeyError(package)
            job.cancel_requested = True
            job.skip_requested_at = _now_ts()
            if job.status not in ("building", "verifying"):
                job.status = "paused"
                job.finished_at = _now_ts()
                job.current_step = None
                job.current_pid = None
        # Signal worker process (if running) to cancel.
        if hasattr(self, "_mp_cancel"):
            try:
                self._mp_cancel[package] = True
            except Exception:
                pass
        self._write_state()
        _update_todo_auto_section(
            todo_path=Path(job.todo_path), job=job, server_origin=self.server_origin
        )

    def unpause(self, package: str) -> None:
        """
        Resume a paused package by returning it to not_started.
        """
        with self._lock:
            job = self._jobs.get(package)
            if not job:
                raise KeyError(package)
            if job.status not in ("paused", "skipped"):
                return
            job.cancel_requested = False
            job.skip_requested_at = None
            job.current_step = None
            job.current_pid = None
            job.status = "not_started"
            job.error = None
            job.finished_at = None
        if hasattr(self, "_mp_cancel"):
            try:
                self._mp_cancel[package] = False
            except Exception:
                pass
        self._write_state()
        _update_todo_auto_section(
            todo_path=Path(job.todo_path), job=job, server_origin=self.server_origin
        )

    def prioritize(self, package: str) -> None:
        """
        Move a package to the front of the queue so it is processed next.

        - If paused, we unpause it (return to not_started).
        - If already running, we leave it alone (it is already being processed).
        """
        with self._lock:
            job = self._jobs.get(package)
            if not job:
                raise KeyError(package)

            if job.status in ("paused", "skipped"):
                job.cancel_requested = False
                job.skip_requested_at = None
                job.current_step = None
                job.current_pid = None
                job.status = "not_started"
                job.error = None
                job.finished_at = None

            if job.status == "not_started":
                # stable: move to front
                self._queue = [package] + [p for p in self._queue if p != package]
        self._write_state()
        _update_todo_auto_section(
            todo_path=Path(job.todo_path), job=job, server_origin=self.server_origin
        )

    def sort_queue(self, order: str = "asc") -> None:
        """Sort the queue alphabetically (asc=A-Z, desc=Z-A)."""
        with self._lock:
            # Only sort packages that are still in queue (not_started, paused, skipped)
            queued = [
                name
                for name in self._queue
                if self._jobs[name].status in ("not_started", "paused", "skipped")
            ]
            not_queued = [name for name in self._queue if name not in queued]

            if order == "desc":
                queued.sort(reverse=True)
            else:
                queued.sort()

            # Keep non-queued items in their current order, append sorted queue
            self._queue = not_queued + queued
        self._write_state()

    def get_whoami(self) -> dict[str, Any]:
        return {
            "name": _git_config(self.packages_repo_root, "user.name"),
            "email": _git_config(self.packages_repo_root, "user.email"),
        }

    def git_diff(self, package: str) -> str:
        job = self.get_job(package)
        if not job:
            raise KeyError(package)
        pkg_rel = f"packages/{package}"
        # Reviewer-focused diff:
        # - show `.ato` and `README.md` changes
        # - exclude any `parts/` directory (autogenerated/imported blobs)
        #
        # We use git pathspec magic to keep this fast and accurate.
        pathspecs = [
            f":(glob){pkg_rel}/**/*.ato",
            f":(glob){pkg_rel}/**/README.md",
            f":(exclude,glob){pkg_rel}/**/parts/**",
        ]
        for base in ("origin/main", "main"):
            r = subprocess.run(
                ["git", "diff", f"{base}...HEAD", "--", *pathspecs],
                cwd=self.packages_repo_root,
                capture_output=True,
                text=True,
                check=False,
            )
            if r.returncode == 0:
                return r.stdout or ""
        return ""

    def git_diff_info(self, package: str) -> dict[str, Any]:
        """
        Return reviewer-focused diff plus a summary of changed files *not shown* in the diff.

        The web UI shows only `.ato` files (excluding `parts/`). However, for package
        maintenance it's still useful to know *what else changed* (e.g. regenerated
        footprints/layouts) without dumping it into the diff viewer.
        """
        job = self.get_job(package)
        if not job:
            raise KeyError(package)
        pkg_rel = f"packages/{package}"

        shown_pathspecs = [
            f":(glob){pkg_rel}/**/*.ato",
            f":(glob){pkg_rel}/**/README.md",
            f":(exclude,glob){pkg_rel}/**/parts/**",
        ]

        def summarize_hidden(
            all_files: list[str], shown_files: set[str]
        ) -> dict[str, int]:
            from collections import Counter

            hidden = [p for p in all_files if p not in shown_files]
            c: Counter[str] = Counter()
            prefix = pkg_rel + "/"
            for p in hidden:
                rel = p[len(prefix) :] if p.startswith(prefix) else p
                ext = Path(rel).suffix.lower()
                if rel.startswith("parts/"):
                    c[f"parts/*{ext or ''}"] += 1
                elif rel.startswith("layouts/"):
                    c[f"layouts/*{ext or ''}"] += 1
                elif rel == "ato.yaml":
                    c["ato.yaml"] += 1
                elif rel.lower().endswith(".md"):
                    c["*.md"] += 1
                elif ext:
                    c[f"*{ext}"] += 1
                else:
                    c["(no extension)"] += 1
            # Stable ordering in UI
            return dict(sorted(c.items(), key=lambda kv: (-kv[1], kv[0])))

        for base in ("origin/main", "main"):
            # Full change list for the package dir
            all_r = subprocess.run(
                ["git", "diff", "--name-only", f"{base}...HEAD", "--", pkg_rel],
                cwd=self.packages_repo_root,
                capture_output=True,
                text=True,
                check=False,
            )
            if all_r.returncode != 0:
                continue

            shown_r = subprocess.run(
                [
                    "git",
                    "diff",
                    "--name-only",
                    f"{base}...HEAD",
                    "--",
                    *shown_pathspecs,
                ],
                cwd=self.packages_repo_root,
                capture_output=True,
                text=True,
                check=False,
            )
            if shown_r.returncode != 0:
                continue

            diff_r = subprocess.run(
                ["git", "diff", f"{base}...HEAD", "--", *shown_pathspecs],
                cwd=self.packages_repo_root,
                capture_output=True,
                text=True,
                check=False,
            )
            if diff_r.returncode != 0:
                continue

            all_files = [
                ln.strip() for ln in (all_r.stdout or "").splitlines() if ln.strip()
            ]
            shown_files = {
                ln.strip() for ln in (shown_r.stdout or "").splitlines() if ln.strip()
            }
            hidden_summary = summarize_hidden(all_files, shown_files)
            hidden_total = len([p for p in all_files if p not in shown_files])

            return {
                "diff": diff_r.stdout or "",
                "changed_total": len(all_files),
                "shown_total": len(shown_files),
                "hidden_total": hidden_total,
                "hidden_summary": hidden_summary,
            }

        return {
            "diff": "",
            "changed_total": 0,
            "shown_total": 0,
            "hidden_total": 0,
            "hidden_summary": {},
        }

    def _registry_poller(self) -> None:
        """
        Best-effort poll of the packages registry.

        We use this to display a stable "Published ✅" indicator for packages
        that are already published as `0.14.x` on the registry, even if the
        local review run hasn't processed them yet.
        """
        next_refresh: dict[str, float] = {}
        while not self._stop:
            time.sleep(0.25)
            now = time.time()

            # Snapshot identifiers outside lock.
            #
            # Important: with thousands of packages, polling all identifiers quickly becomes
            # expensive (network + CPU). We only poll a small window of packages near the front
            # of the queue, plus anything that's actively in-progress or awaiting review.
            with self._lock:
                queue = list(self._queue)
                # Poll a limited window near the front of the queue.
                poll_window = min(max(self.max_ready * 3, 30), len(queue))
                front = set(queue[:poll_window])
                # Always include "active" jobs regardless of queue position.
                active = {
                    n
                    for n, j in self._jobs.items()
                    if j.status
                    in (
                        "building",
                        "verifying",
                        "awaiting_review",
                        "approved",
                        "pushing_branch",
                        "branch_pushed",
                        "pr_opened",
                    )
                }
                want = front | active
                items = [
                    (name, self._jobs[name].package_identifier)
                    for name in queue
                    if name in want and self._jobs[name].package_identifier
                ]

            if not items:
                time.sleep(1.0)
                continue

            did_any = False
            for name, ident in items:
                assert ident is not None
                due = next_refresh.get(ident, 0.0)
                if now < due:
                    continue

                did_any = True
                next_refresh[ident] = now + self.registry_refresh_seconds

                try:
                    # Mirror `PackagesAPIClient.get_package(identifier)`:
                    # GET /v1/package/{identifier} -> response.info.version
                    ident_path = quote(ident, safe="/")
                    url = f"{self.registry_url}/v1/package/{ident_path}"
                    req = Request(
                        url, headers={"User-Agent": "packages-review-station/0"}
                    )
                    with urlopen(req, timeout=10) as r:
                        data = json.loads(r.read().decode("utf-8"))

                    latest_version = ((data or {}).get("info") or {}).get("version")
                    if (
                        not isinstance(latest_version, str)
                        or not latest_version.strip()
                    ):
                        raise ValueError("registry response missing info.version")
                    latest_version = latest_version.strip()

                    # Now fetch the release record so we can read requires_atopile (this is what
                    # tells us if the package was updated to atopile 0.14.x).
                    rel_url = f"{self.registry_url}/v1/package/{ident_path}/releases/{quote(latest_version, safe='')}"
                    rel_req = Request(
                        rel_url, headers={"User-Agent": "packages-review-station/0"}
                    )
                    with urlopen(rel_req, timeout=10) as rr:
                        rel_data = json.loads(rr.read().decode("utf-8"))
                    requires_atopile = ((rel_data or {}).get("info") or {}).get(
                        "requires_atopile"
                    )
                    if (
                        not isinstance(requires_atopile, str)
                        or not requires_atopile.strip()
                    ):
                        raise ValueError(
                            "registry response missing info.requires_atopile"
                        )
                    requires_atopile = requires_atopile.strip()

                    # Consider updated if it requires atopile 0.14.x (most packages use caret).
                    updated_014 = bool(re.match(r"^\^?0\.14\.\d+", requires_atopile))

                    with self._lock:
                        j = self._jobs.get(name)
                        if j:
                            j.registry_published_version = latest_version
                            j.registry_requires_atopile = requires_atopile
                            j.registry_checked_at = _now_ts()
                            j.registry_error = None
                            j.registry_updated_014 = updated_014
                    self._write_state()
                    # Avoid hammering the registry when lots of packages are queued.
                    time.sleep(0.05)
                except Exception as e:
                    with self._lock:
                        j = self._jobs.get(name)
                        if j:
                            j.registry_checked_at = _now_ts()
                            j.registry_error = str(e)
                            j.registry_updated_014 = False
                    self._write_state()
                    time.sleep(0.1)

            if not did_any:
                time.sleep(0.5)

    def publish(
        self,
        package: str,
        *,
        commit_message: str,
        reviewer: str | None,
        target_requires_atopile: str,
    ) -> dict[str, Any]:
        """
        Push a per-package branch (best-effort) without touching the current working branch.

        Current behavior (intentionally conservative for large review runs):
        - Create/reset a branch named `package-update-<series>-<package>`
        - In a temporary git worktree based on origin/main (or main):
          - copy the package directory from the current working tree
          - rewrite `requires-atopile` and bump package minor version
          - commit *only* this package directory
          - force-push the branch (overwrite remote if it already exists)

        This allows reviewers to push WIP branches safely while keeping their
        current local branch (with many packages in progress) unchanged.
        """
        job = self.get_job(package)
        if not job:
            raise KeyError(package)

        # By default, publishing is only allowed once build + verify have completed successfully.
        # This keeps the action safe to click during long review runs.
        if not self.publish_anyway:
            build_names = list(job.build_names or [])
            missing_builds = [b for b in build_names if job.build_rc.get(b) is None]
            bad_builds = [
                b
                for b in build_names
                if (job.build_rc.get(b) is not None and int(job.build_rc.get(b)) != 0)
            ]
            verify_missing = job.verify_rc is None
            verify_bad = job.verify_rc is not None and int(job.verify_rc) != 0

            if missing_builds or bad_builds or verify_missing or verify_bad:
                reasons: list[str] = []
                if missing_builds:
                    reasons.append(f"build incomplete: {', '.join(missing_builds)}")
                if bad_builds:
                    reasons.append(f"build failed: {', '.join(bad_builds)}")
                if verify_missing:
                    reasons.append("verify incomplete")
                if verify_bad:
                    reasons.append(f"verify failed (rc={job.verify_rc})")
                raise PermissionError(
                    "Publish blocked until build+verify succeed. "
                    + "; ".join(reasons)
                    + ". Start server with --publish-anyway to override."
                )

        pkg_rel = f"packages/{package}"
        series = _series_tag_from_requires_atopile(target_requires_atopile)
        branch = f"package-update-{_slugify_branch_component(series)}-{_slugify_branch_component(package)}"

        # Mark in-progress early so the UI shows movement while we run git ops.
        with self._lock:
            job.status = "pushing_branch"
            job.publish_error = None
        self._write_state()
        _update_todo_auto_section(
            todo_path=Path(job.todo_path), job=job, server_origin=self.server_origin
        )

        who = self.get_whoami()
        reviewer = reviewer or job.approved_by or who.get("name")

        def run_git(args: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
            return subprocess.run(
                ["git", *args],
                cwd=cwd,
                capture_output=True,
                text=True,
                check=False,
            )

        def run_gh(args: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
            return subprocess.run(
                ["gh", *args],
                cwd=cwd,
                capture_output=True,
                text=True,
                check=False,
            )

        out: list[dict[str, Any]] = []
        repo = self.packages_repo_root
        src_pkg = repo / pkg_rel
        if not src_pkg.exists():
            raise FileNotFoundError(f"package path not found: {src_pkg}")

        # Pick a stable base ref to create the worktree from.
        base_ref = "origin/main"
        r = run_git(["rev-parse", "--verify", base_ref], cwd=repo)
        if r.returncode != 0:
            base_ref = "main"

        worktrees_root = (self.run_dir / "_publish_worktrees").resolve()
        worktrees_root.mkdir(parents=True, exist_ok=True)
        wt_dir = worktrees_root / branch

        # Best-effort cleanup of prior worktree.
        run_git(["worktree", "remove", "--force", str(wt_dir)], cwd=repo)

        # Create/reset worktree to the target branch based on base_ref.
        r = run_git(
            ["worktree", "add", "--force", "-B", branch, str(wt_dir), base_ref],
            cwd=repo,
        )
        out.append(
            {
                "cmd": [
                    "git",
                    "worktree",
                    "add",
                    "--force",
                    "-B",
                    branch,
                    str(wt_dir),
                    base_ref,
                ],
                "rc": r.returncode,
                "out": r.stdout,
                "err": r.stderr,
            }
        )
        if r.returncode != 0:
            raise RuntimeError(f"git worktree add failed:\n{r.stderr}")

        wt_repo = wt_dir
        wt_pkg = wt_repo / pkg_rel

        # Replace package directory in worktree with current working tree snapshot.
        if wt_pkg.exists():
            shutil.rmtree(wt_pkg)

        def _ignore(_dir: str, names: list[str]) -> set[str]:
            # Never copy build outputs or review notes into publish branches.
            ignore = set()
            for n in names:
                if n in {"build", ".pytest_cache", "__pycache__", "review.todo.md"}:
                    ignore.add(n)
            return ignore

        shutil.copytree(src_pkg, wt_pkg, ignore=_ignore, dirs_exist_ok=True)

        # Apply required changes (version + requires-atopile) in the worktree copy
        old_v, new_v = _rewrite_ato_yaml_for_publish(
            wt_pkg / "ato.yaml", required_atopile=target_requires_atopile
        )

        # Generate commit message (now that we know the version)
        version_part = f"to v{new_v}, " if new_v else ""
        cm = (
            commit_message or ""
        ).strip() or f"{package}: package update {version_part}ato:{target_requires_atopile}"
        # Add build stats
        cm += "\n\nBuild targets:"
        for b in job.build_names:
            cm += f"\n  {b} = rc{job.build_rc.get(b)}"
        cm += f"\nPackage Verify: rc{job.verify_rc}"
        if old_v and new_v:
            cm += f"\nVersion: {old_v} -> {new_v}"
        cm += f"\nRequires ato: {target_requires_atopile}"

        # Commit only this package directory
        for cmd in (
            ["add", "--", pkg_rel],
            ["commit", "-m", cm],
        ):
            r = run_git(cmd, cwd=wt_repo)
            out.append(
                {
                    "cmd": ["git", *cmd],
                    "rc": r.returncode,
                    "out": r.stdout,
                    "err": r.stderr,
                }
            )
            if r.returncode != 0:
                raise RuntimeError(f"git failed: {' '.join(cmd)}\n{r.stderr}")

        # Force-push branch (overwrite remote branch if it already exists)
        pushed = False
        r = run_git(["push", "-u", "origin", branch, "--force-with-lease"], cwd=wt_repo)
        out.append(
            {
                "cmd": ["git", "push", "-u", "origin", branch, "--force-with-lease"],
                "rc": r.returncode,
                "out": r.stdout,
                "err": r.stderr,
            }
        )
        pushed = r.returncode == 0
        if not pushed:
            raise RuntimeError(f"git push failed:\n{r.stderr}")

        git_hash = _get_git_hash(repo)
        pr_title, pr_body = _pr_title_and_body(
            job=job,
            package=package,
            branch=branch,
            reviewer=reviewer,
            target_requires_atopile=target_requires_atopile,
            old_version=old_v,
            new_version=new_v,
            git_hash=git_hash,
        )

        # Create or reuse PR (best-effort, requires `gh`).
        pr_url: str | None = None
        if shutil.which("gh"):
            # Try to find existing PR for this branch first (common when re-running publish).
            r = run_gh(
                ["pr", "view", "--head", branch, "--json", "url", "--jq", ".url"],
                cwd=wt_repo,
            )
            out.append(
                {"cmd": ["gh", "pr", "view", "--head", branch, "--json", "url", "--jq", ".url"], "rc": r.returncode, "out": r.stdout, "err": r.stderr}
            )
            if r.returncode == 0 and (r.stdout or "").strip():
                pr_url = (r.stdout or "").strip()
            else:
                r = run_gh(
                    ["pr", "create", "--title", pr_title, "--body", pr_body, "--head", branch, "--base", "main"],
                    cwd=wt_repo,
                )
                out.append(
                    {"cmd": ["gh", "pr", "create", "--title", pr_title, "--body", "<…>", "--head", branch, "--base", "main"], "rc": r.returncode, "out": r.stdout, "err": r.stderr}
                )
                if r.returncode == 0:
                    # gh prints the URL on success (usually last line)
                    pr_url = (r.stdout or "").strip().splitlines()[-1] if (r.stdout or "").strip() else None

        # Cleanup worktree to avoid accumulating many working dirs.
        run_git(["worktree", "remove", "--force", str(wt_dir)], cwd=repo)

        with self._lock:
            job.published_branch = branch
            job.published_at = _now_ts()
            job.published_target_requires_atopile = target_requires_atopile
            job.published_pr_url = pr_url
            job.published_pr_title = pr_title if pr_url else None
            job.published_pr_body = pr_body if pr_url else None
            job.status = "pr_opened" if pr_url else "branch_pushed"
            job.publish_error = None
        self._write_state()
        _update_todo_auto_section(
            todo_path=Path(job.todo_path), job=job, server_origin=self.server_origin
        )

        return {"branch": branch, "pushed": pushed, "pr_url": pr_url, "commands": out}

    def uprev_and_publish(
        self,
        package: str,
        *,
        reviewer: str | None = None,
    ) -> dict[str, Any]:
        """
        Quick uprev: read version from origin/main, bump patch, and create PR.

        Uses `git show` to read ato.yaml directly from origin/main, ensuring
        we always bump from the current main version (no merge conflicts).
        """
        job = self.get_job(package)
        if not job:
            raise KeyError(package)

        who = self.get_whoami()
        reviewer = reviewer or who.get("name")

        def run_git(args: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
            return subprocess.run(
                ["git", *args],
                cwd=cwd,
                capture_output=True,
                text=True,
                check=False,
            )

        def run_gh(args: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
            return subprocess.run(
                ["gh", *args],
                cwd=cwd,
                capture_output=True,
                text=True,
                check=False,
            )

        out: list[dict[str, Any]] = []
        repo = self.packages_repo_root
        pkg_rel = f"packages/{package}"

        # 1. Fetch latest origin/main
        r = run_git(["fetch", "origin", "main"], cwd=repo)
        out.append({"cmd": "fetch origin main", "rc": r.returncode, "err": r.stderr})
        if r.returncode != 0:
            raise RuntimeError(f"git fetch failed:\n{r.stderr}")

        # 2. Read ato.yaml directly from origin/main using git show
        ato_yaml_ref = f"origin/main:{pkg_rel}/ato.yaml"
        r = run_git(["show", ato_yaml_ref], cwd=repo)
        out.append({"cmd": f"show {ato_yaml_ref}", "rc": r.returncode})
        if r.returncode != 0:
            raise FileNotFoundError(f"Could not read {ato_yaml_ref}:\n{r.stderr}")

        txt = r.stdout

        # 3. Extract current version from main
        m = re.search(r'(?m)^\s*version:\s*"?(\d+\.\d+\.\d+)"?\s*$', txt)
        if not m:
            raise ValueError("Could not find version in ato.yaml")

        old_version = m.group(1)
        new_version = _bump_patch(old_version)

        # 4. Update version in the content
        txt2 = re.sub(
            r'(?m)^(\s*version:\s*)("?)(\d+\.\d+\.\d+)\2\s*$',
            rf'\g<1>"{new_version}"',
            txt,
            count=1,
        )

        # 5. Create a fresh branch from origin/main
        branch = f"uprev-{_slugify_branch_component(package)}-v{new_version.replace('.', '-')}"

        worktrees_root = (self.run_dir / "_publish_worktrees").resolve()
        worktrees_root.mkdir(parents=True, exist_ok=True)
        wt_dir = worktrees_root / branch

        # Cleanup any prior worktree
        run_git(["worktree", "remove", "--force", str(wt_dir)], cwd=repo)

        # Create fresh worktree from origin/main
        r = run_git(
            ["worktree", "add", "--force", "-B", branch, str(wt_dir), "origin/main"],
            cwd=repo,
        )
        out.append({"cmd": "worktree add", "rc": r.returncode, "err": r.stderr})
        if r.returncode != 0:
            raise RuntimeError(f"git worktree add failed:\n{r.stderr}")

        # 6. Write the updated ato.yaml
        wt_pkg = wt_dir / pkg_rel
        ato_yaml_path = wt_pkg / "ato.yaml"
        ato_yaml_path.write_text(txt2, encoding="utf-8")

        # Commit
        cm = f"{package}: uprev to v{new_version}\n\nVersion: {old_version} -> {new_version}"
        for cmd in (
            ["add", "--", pkg_rel],
            ["commit", "-m", cm],
        ):
            r = run_git(cmd, cwd=wt_dir)
            out.append({"cmd": cmd, "rc": r.returncode, "err": r.stderr})
            if r.returncode != 0 and cmd[0] == "commit":
                run_git(["worktree", "remove", "--force", str(wt_dir)], cwd=repo)
                raise RuntimeError(f"git {cmd} failed:\n{r.stderr}")

        # Push
        r = run_git(["push", "--force", "-u", "origin", branch], cwd=wt_dir)
        out.append({"cmd": "push", "rc": r.returncode, "err": r.stderr})
        pushed = r.returncode == 0

        # Create PR
        pr_url: str | None = None
        if pushed and shutil.which("gh"):
            pr_title = f"{package}: uprev to v{new_version}"
            pr_body = f"Version bump: {old_version} → {new_version}\n\nReviewer: {reviewer or 'unknown'}"

            # Check if PR already exists
            r = run_gh(["pr", "view", "--head", branch, "--json", "url"], cwd=wt_dir)
            if r.returncode == 0 and r.stdout.strip():
                pr_info = json.loads(r.stdout.strip())
                pr_url = pr_info.get("url")
            else:
                # Create new PR
                r = run_gh(
                    ["pr", "create", "--title", pr_title, "--body", pr_body, "--head", branch, "--base", "main"],
                    cwd=wt_dir,
                )
                out.append({"cmd": "pr create", "rc": r.returncode, "err": r.stderr})
                if r.returncode == 0:
                    pr_url = (r.stdout or "").strip().splitlines()[-1] if (r.stdout or "").strip() else None

        # Cleanup worktree
        run_git(["worktree", "remove", "--force", str(wt_dir)], cwd=repo)

        # Update job state
        with self._lock:
            job.published_branch = branch
            job.published_at = _now_ts()
            job.published_pr_url = pr_url
            job.published_pr_title = f"{package}: uprev to v{new_version}" if pr_url else None
            job.status = "pr_opened" if pr_url else "branch_pushed"
            job.publish_error = None
        self._write_state()

        return {
            "branch": branch,
            "pushed": pushed,
            "pr_url": pr_url,
            "old_version": old_version,
            "new_version": new_version,
            "commands": out,
        }

    def open_kicad(self, package: str, build: str) -> None:
        job = self.get_job(package)
        if not job:
            raise KeyError(package)
        pcb = job.layout_paths.get(build)
        if not pcb:
            raise FileNotFoundError(f"No pcb for build={build}")
        cmd = _open_file_cmd(Path(pcb), self.open_cmd)
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def open_cursor(self, package: str, build: str, cursor_cmd: str) -> None:
        """
        Open the build's `.ato` file in Cursor.

        We resolve the file path from the build's `entry:` in `ato.yaml`.
        """
        job = self.get_job(package)
        if not job:
            raise KeyError(package)
        entry = (job.build_entries or {}).get(build)
        if not entry:
            raise FileNotFoundError(f"No entry found for build={build}")
        ato_rel = entry.split(":", 1)[0].strip()
        if not ato_rel:
            raise FileNotFoundError(f"Bad entry for build={build}: {entry}")
        ato_path = (Path(job.package_dir) / ato_rel).resolve()
        if not ato_path.exists():
            raise FileNotFoundError(f"ato file not found: {ato_path}")

        cmd = [*shlex.split(cursor_cmd), str(ato_path)]
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def open_logs_in_cursor(self, package: str, cursor_cmd: str) -> None:
        """
        Open the package's review.todo.md file in Cursor (reusing current window).

        This file contains feedback notes and autogenerated build summary.
        """
        job = self.get_job(package)
        if not job:
            raise KeyError(package)

        todo_file = Path(job.todo_path)
        if not todo_file.exists():
            raise FileNotFoundError(f"Todo file not found: {todo_file}")

        # Open the todo file in the current Cursor window
        cmd = [*shlex.split(cursor_cmd), "--reuse-window", str(todo_file)]
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def start_agent_for_package(self, package: str) -> dict[str, Any]:
        """
        Start the Cursor Agent CLI to fix a package.

        Returns info about the spawned process.
        """
        job = self.get_job(package)
        if not job:
            raise KeyError(package)

        todo_file = Path(job.todo_path)
        if not todo_file.exists():
            raise FileNotFoundError(f"Todo file not found: {todo_file}")

        # Check if cursor agent is available
        cursor_agent = shutil.which("cursor")
        if not cursor_agent:
            raise FileNotFoundError("Cursor CLI not found in PATH")

        prompt = f"Please read {todo_file} and fix the package following the instructions inside. The file contains build errors/warnings and API endpoints for triggering rebuilds."

        # Start cursor agent in the package directory
        cmd = [
            cursor_agent, "agent",
            "--workspace", str(job.package_dir),
            prompt
        ]

        # Start in background - agent runs interactively in a new terminal
        proc = subprocess.Popen(
            cmd,
            cwd=job.package_dir,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )

        return {
            "pid": proc.pid,
            "package": package,
            "workspace": job.package_dir,
            "todo_file": str(todo_file),
        }

    def list_logs(self, package: str) -> dict[str, Any]:
        """
        Return a structured log index for the UI.

        We expose:
        - Review-station logs (per-run): `run__<filename>`
        - Package build logs (latest): `pkg__latest__<build>__<filename>`
        """
        job = self.get_job(package)
        if not job:
            raise KeyError(package)

        run_logs_dir = (Path(job.run_dir) / "logs").resolve()
        pkg_build_latest = (Path(job.package_dir) / "build" / "logs" / "latest").resolve()

        def safe_rel_child(root: Path, child: Path) -> bool:
            try:
                child.resolve().relative_to(root)
                return True
            except Exception:
                return False

        stages: dict[str, list[dict[str, Any]]] = {"build": [], "verify": [], "other": []}

        # Review-station build logs (one per build target)
        for b in job.build_names:
            fname = f"build.{b}.log"
            p = run_logs_dir / fname
            stages["build"].append(
                {
                    "id": f"run__{fname}",
                    "label": f"ato build -b {b}",
                    "warn": int(job.build_warn.get(b, 0) or 0),
                    "err": int(job.build_err.get(b, 0) or 0),
                    "size": p.stat().st_size if p.exists() else 0,
                    "exists": p.exists(),
                }
            )

        # Review-station verify log
        v = run_logs_dir / "verify.log"
        stages["verify"].append(
            {
                "id": "run__verify.log",
                "label": "ato package verify -s",
                "warn": int(job.verify_warn or 0),
                "err": int(job.verify_err or 0),
                "size": v.stat().st_size if v.exists() else 0,
                "exists": v.exists(),
            }
        )

        # Any other files produced by the review-station runner
        if run_logs_dir.exists():
            for p in sorted(run_logs_dir.iterdir()):
                if not p.is_file():
                    continue
                if p.name.startswith("build.") and p.name.endswith(".log"):
                    continue
                if p.name == "verify.log":
                    continue
                stages["other"].append(
                    {
                        "id": f"run__{p.name}",
                        "label": p.name,
                        "warn": None,
                        "err": None,
                        "size": p.stat().st_size,
                        "exists": True,
                    }
                )

        # Package internal logs: build/logs/latest/<build>/*
        #
        # NOTE: This directory can contain many logs. We intentionally avoid scanning file
        # contents here (too expensive for periodic UI refresh). Instead, we use filename
        # heuristics for warning/error badges; the reviewer can open the log to see details.
        if pkg_build_latest.exists():
            for b in job.build_names:
                bdir = pkg_build_latest / b
                if not bdir.exists() or not bdir.is_dir():
                    continue
                for p in sorted(bdir.iterdir()):
                    if not p.is_file():
                        continue
                    # Keep it practical: logs/text only
                    if not (p.name.endswith(".log") or p.name.endswith(".txt")):
                        continue
                    if not safe_rel_child(pkg_build_latest, p):
                        continue
                    name_l = p.name.lower()
                    e = 1 if ".error." in name_l or name_l.endswith(".error.log") else 0
                    w = 1 if ".warning." in name_l or name_l.endswith(".warning.log") else 0
                    stages["build"].append(
                        {
                            "id": f"pkg__latest__{b}__{p.name}",
                            "label": f"{b} / {p.name}",
                            "warn": int(w),
                            "err": int(e),
                            "size": p.stat().st_size,
                            "exists": True,
                        }
                    )

        return {"package": package, "stages": stages}

    def list_issues(self, package: str) -> dict[str, Any]:
        """
        Extract and aggregate all errors/warnings from logs for quick review.

        Returns structured list of issues with:
        - type: "error" | "warning"
        - message: the log line content
        - source: which log file/build step produced it
        - line_num: line number in the log file (for reference)
        """
        job = self.get_job(package)
        if not job:
            raise KeyError(package)

        run_logs_dir = (Path(job.run_dir) / "logs").resolve()
        pkg_build_latest = (Path(job.package_dir) / "build" / "logs" / "latest").resolve()

        issues: list[dict[str, Any]] = []

        # Patterns for matching errors/warnings in Rich-style logs
        # Match lines like: "ERROR  some message" or "│ ERROR │ message"
        error_pattern = re.compile(r"\bERROR\b", re.IGNORECASE)
        warning_pattern = re.compile(r"\bWARNING\b", re.IGNORECASE)
        # Also match Python traceback starts
        traceback_pattern = re.compile(r"^Traceback \(most recent call last\):", re.MULTILINE)

        def extract_from_log(
            log_path: Path,
            source_label: str,
            stage: str,
            max_bytes: int = 2_000_000,
            log_id_override: str | None = None,
        ) -> None:
            """Extract errors/warnings from a single log file."""
            if not log_path.exists():
                return
            try:
                with log_path.open("rb") as f:
                    data = f.read(max_bytes)
                txt = data.decode("utf-8", errors="replace")
            except Exception:
                return

            lines = txt.splitlines()
            in_traceback = False
            traceback_start = 0

            for i, line in enumerate(lines):
                line_num = i + 1

                # Track tracebacks as error blocks
                if traceback_pattern.match(line):
                    in_traceback = True
                    traceback_start = line_num
                    continue

                if in_traceback:
                    # End of traceback: blank line or new log entry
                    if not line.strip() or (error_pattern.search(line) or warning_pattern.search(line)):
                        in_traceback = False
                    else:
                        continue

                # Match explicit ERROR/WARNING markers
                # Determine log_id - use override if provided, otherwise fall back to run__ prefix
                effective_log_id = log_id_override if log_id_override else f"run__{log_path.name}"

                if error_pattern.search(line):
                    # Clean up the line - remove ANSI codes and excessive whitespace
                    clean_line = re.sub(r"\x1b\[[0-9;]*m", "", line).strip()
                    # Skip empty or too-short messages
                    if len(clean_line) > 10:
                        issues.append({
                            "type": "error",
                            "message": clean_line,
                            "source": source_label,
                            "stage": stage,
                            "line_num": line_num,
                            "log_id": effective_log_id,
                        })
                elif warning_pattern.search(line):
                    clean_line = re.sub(r"\x1b\[[0-9;]*m", "", line).strip()
                    if len(clean_line) > 10:
                        issues.append({
                            "type": "warning",
                            "message": clean_line,
                            "source": source_label,
                            "stage": stage,
                            "line_num": line_num,
                            "log_id": effective_log_id,
                        })

        # Extract from review-station build logs
        for b in job.build_names:
            fname = f"build.{b}.log"
            p = run_logs_dir / fname
            extract_from_log(p, f"build ({b})", "build", log_id_override=fname)

        # Extract from verify log
        v = run_logs_dir / "verify.log"
        extract_from_log(v, "verify", "verify", log_id_override="verify.log")

        # Extract from package internal logs (build/logs/latest/<build>/*)
        if pkg_build_latest.exists():
            for b in job.build_names:
                bdir = pkg_build_latest / b
                if not bdir.exists() or not bdir.is_dir():
                    continue
                for p in sorted(bdir.iterdir()):
                    if not p.is_file():
                        continue
                    if not (p.name.endswith(".log") or p.name.endswith(".txt")):
                        continue
                    # Use pkg__latest__<build>__<filename> format for package logs
                    pkg_log_id = f"pkg__latest__{b}__{p.name}"
                    extract_from_log(p, f"{b} / {p.name}", "build", log_id_override=pkg_log_id)

        # Sort: errors first, then by stage (build before verify), then by line number
        stage_order = {"build": 0, "verify": 1, "other": 2}
        issues.sort(key=lambda x: (
            0 if x["type"] == "error" else 1,
            stage_order.get(x["stage"], 2),
            x["line_num"],
        ))

        # Deduplicate similar messages (keep first occurrence)
        seen_messages: set[str] = set()
        unique_issues: list[dict[str, Any]] = []
        for issue in issues:
            # Normalize message for dedup (remove line numbers, timestamps)
            norm = re.sub(r"\d+", "N", issue["message"][:100])
            if norm not in seen_messages:
                seen_messages.add(norm)
                unique_issues.append(issue)

        # Summary counts
        error_count = sum(1 for i in unique_issues if i["type"] == "error")
        warning_count = sum(1 for i in unique_issues if i["type"] == "warning")

        return {
            "package": package,
            "issues": unique_issues,
            "error_count": error_count,
            "warning_count": warning_count,
            "total_count": len(unique_issues),
        }

    # (worker threads removed; builds are executed in worker *processes*)


class Server:
    def __init__(
        self,
        *,
        host: str,
        port: int,
        run: ReviewRun,
        kicanvas_js: Path,
        model_viewer_js: Path,
        cursor_cmd: str,
    ):
        self.host = host
        self.port = port
        self.run = run
        self.kicanvas_js = kicanvas_js
        self.model_viewer_js = model_viewer_js
        self.cursor_cmd = cursor_cmd

    def serve(self) -> None:
        httpd, actual_port = self._build_httpd()
        # Update our port for log messages if caller used port=0 (ephemeral).
        self.port = actual_port
        console.print(
            f"[green]Review web UI running:[/green] http://{self.host}:{self.port}"
        )
        console.print(f"[dim]Run dir:[/dim] {self.run.run_dir}")
        httpd.serve_forever()

    def start_in_thread(self) -> tuple[ThreadingHTTPServer, int]:
        """
        Start the HTTP server in a background thread (used by tests/benchmarks).

        Returns: (httpd, port)
        """
        httpd, actual_port = self._build_httpd()
        self.port = actual_port
        t = threading.Thread(target=httpd.serve_forever, daemon=True)
        t.start()
        return httpd, actual_port

    def _static_dir(self) -> Path:
        # Prefer the consolidated folder layout (scripts/review_station/static),
        # but keep backwards compatibility with the older path.
        static_dir = Path(__file__).parent / "review_station" / "static"
        if static_dir.exists():
            return static_dir
        return Path(__file__).parent / "review_webui_static"

    def _build_httpd(self) -> tuple[ThreadingHTTPServer, int]:
        """
        Build the HTTP server (but don't start serving yet).

        Important: this exists to enable closed-loop tests that can bring up and
        tear down the server without a CLI subprocess.
        """
        run = self.run
        kicanvas_js = self.kicanvas_js
        model_viewer_js = self.model_viewer_js
        cursor_cmd = self.cursor_cmd
        static_dir = self._static_dir()

        server_log_path = (run.run_dir / "server.log").resolve()

        def _log_line(line: str) -> None:
            try:
                server_log_path.parent.mkdir(parents=True, exist_ok=True)
                with server_log_path.open("a", encoding="utf-8") as f:
                    f.write(line.rstrip() + "\n")
            except Exception:
                pass

        class Handler(BaseHTTPRequestHandler):
            def _send(self, status: int, content_type: str, body: bytes) -> None:
                t0 = getattr(self, "_t0", None)
                dt_ms = (time.perf_counter() - t0) * 1000.0 if t0 else None
                self.send_response(status)
                self.send_header("Content-Type", content_type)
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(body)
                if dt_ms is not None:
                    _log_line(
                        f"{_now_ts()} {self.command} {self.path} -> {status} {len(body)}B {dt_ms:.1f}ms"
                    )

            def _send_json(self, status: int, payload: Any) -> None:
                self._send(
                    status,
                    "application/json; charset=utf-8",
                    (
                        json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
                        + "\n"
                    ).encode("utf-8"),
                )

            def _read_json(self) -> Any:
                n = int(self.headers.get("Content-Length", "0"))
                raw = self.rfile.read(n) if n else b"{}"
                return json.loads(raw.decode("utf-8"))

            def log_message(
                self, fmt: str, *args: Any
            ) -> None:  # quiet default logging
                return

            def do_GET(self) -> None:  # noqa: N802
                self._t0 = time.perf_counter()
                try:
                    u = urlparse(self.path)
                    path = u.path

                    if path == "/api/state":
                        return self._send(
                            HTTPStatus.OK,
                            "application/json; charset=utf-8",
                            run.get_state_json(),
                        )

                    if path == "/api/whoami":
                        return self._send_json(HTTPStatus.OK, run.get_whoami())

                    if path == "/api/health":
                        # Health check for AI agents to verify service is running
                        with run._lock:
                            total = len(run._jobs)
                            building = sum(1 for j in run._jobs.values() if j.status in ("building", "verifying"))
                            queued = sum(1 for j in run._jobs.values() if j.status == "not_started")
                            completed = sum(1 for j in run._jobs.values() if j.status in ("awaiting_review", "approved", "pr_opened", "branch_pushed"))
                            errors = sum(1 for j in run._jobs.values() if j.status == "error")
                        return self._send_json(HTTPStatus.OK, {
                            "status": "ok",
                            "total_packages": total,
                            "building": building,
                            "queued": queued,
                            "completed": completed,
                            "errors": errors,
                            "queue_order": run._queue[:10],  # First 10 in queue
                        })

                    if path.startswith("/api/package/") and path.endswith("/diff"):
                        pkg = unquote(
                            path.removeprefix("/api/package/").removesuffix("/diff")
                        ).strip("/")
                        try:
                            return self._send_json(HTTPStatus.OK, run.git_diff_info(pkg))
                        except KeyError:
                            return self._send_json(
                                HTTPStatus.NOT_FOUND, {"error": "unknown package"}
                            )
                        except Exception as e:
                            return self._send_json(
                                HTTPStatus.INTERNAL_SERVER_ERROR, {"error": str(e)}
                            )

                    if path.startswith("/api/package/") and path.endswith("/logs"):
                        pkg = unquote(
                            path.removeprefix("/api/package/").removesuffix("/logs")
                        ).strip("/")
                        try:
                            return self._send_json(HTTPStatus.OK, run.list_logs(pkg))
                        except KeyError:
                            return self._send_json(
                                HTTPStatus.NOT_FOUND, {"error": "unknown package"}
                            )
                        except Exception as e:
                            return self._send_json(
                                HTTPStatus.INTERNAL_SERVER_ERROR, {"error": str(e)}
                            )

                    # Agent messages endpoint (GET)
                    if path.startswith("/api/package/") and path.endswith("/messages"):
                        pkg = unquote(
                            path.removeprefix("/api/package/").removesuffix("/messages")
                        ).strip("/")
                        try:
                            messages = run.get_agent_messages(pkg)
                            return self._send_json(HTTPStatus.OK, {"package": pkg, "messages": messages})
                        except KeyError:
                            return self._send_json(
                                HTTPStatus.NOT_FOUND, {"error": "unknown package"}
                            )

                    # SSE streaming endpoint for watching package status in real-time
                    if path.startswith("/api/package/") and path.endswith("/stream"):
                        pkg = unquote(
                            path.removeprefix("/api/package/").removesuffix("/stream")
                        ).strip("/")
                        job = run.get_job(pkg)
                        if not job:
                            return self._send_json(
                                HTTPStatus.NOT_FOUND, {"error": "unknown package"}
                            )
                        # Send SSE headers
                        self.send_response(HTTPStatus.OK)
                        self.send_header("Content-Type", "text/event-stream")
                        self.send_header("Cache-Control", "no-cache")
                        self.send_header("Connection", "keep-alive")
                        self.send_header("Access-Control-Allow-Origin", "*")
                        self.end_headers()

                        import json as _json
                        last_status = None
                        last_progress = None
                        last_msg_count = 0
                        try:
                            while True:
                                job = run.get_job(pkg)
                                if not job:
                                    break
                                # Send update if status, progress, or messages changed
                                current_status = job.status
                                current_progress = job.build_progress
                                current_msg_count = len(job.agent_messages)

                                if (current_status != last_status or
                                    current_progress != last_progress or
                                    current_msg_count != last_msg_count):

                                    event_data = {
                                        "package": pkg,
                                        "status": job.status,
                                        "build_progress": job.build_progress,
                                        "current_step": job.current_step,
                                        "error": job.error,
                                        "finished": job.finished_at is not None,
                                        "messages": job.agent_messages[-5:] if job.agent_messages else [],
                                    }
                                    self.wfile.write(f"data: {_json.dumps(event_data)}\n\n".encode())
                                    self.wfile.flush()

                                    last_status = current_status
                                    last_progress = current_progress
                                    last_msg_count = current_msg_count

                                # Exit if job is finished
                                if job.finished_at:
                                    # Send final status
                                    final_data = {
                                        "package": pkg,
                                        "status": job.status,
                                        "finished": True,
                                        "build_rc": dict(job.build_rc),
                                        "verify_rc": job.verify_rc,
                                        "error": job.error,
                                    }
                                    self.wfile.write(f"data: {_json.dumps(final_data)}\n\n".encode())
                                    self.wfile.flush()
                                    break

                                time.sleep(0.3)  # Check every 300ms
                        except (BrokenPipeError, ConnectionResetError):
                            pass  # Client disconnected
                        return

                    if path.startswith("/api/package/") and path.endswith("/issues"):
                        pkg = unquote(
                            path.removeprefix("/api/package/").removesuffix("/issues")
                        ).strip("/")
                        try:
                            return self._send_json(HTTPStatus.OK, run.list_issues(pkg))
                        except KeyError:
                            return self._send_json(
                                HTTPStatus.NOT_FOUND, {"error": "unknown package"}
                            )
                        except Exception as e:
                            return self._send_json(
                                HTTPStatus.INTERNAL_SERVER_ERROR, {"error": str(e)}
                            )

                    # Simple status endpoint for AI agents
                    if path.startswith("/api/package/") and path.endswith("/status"):
                        pkg = unquote(
                            path.removeprefix("/api/package/").removesuffix("/status")
                        ).strip("/")
                        job = run.get_job(pkg)
                        if not job:
                            return self._send_json(
                                HTTPStatus.NOT_FOUND, {"error": "unknown package"}
                            )
                        # Calculate elapsed time if running
                        elapsed = None
                        if job.started_at and not job.finished_at:
                            try:
                                from datetime import datetime
                                started = datetime.fromisoformat(job.started_at.replace("Z", "+00:00"))
                                elapsed = (datetime.now(started.tzinfo) - started).total_seconds()
                            except Exception:
                                pass
                        # Calculate queue position
                        queue_position = None
                        queue_total = None
                        if job.status == "not_started":
                            try:
                                queue_position = run._queue.index(pkg) + 1
                                queue_total = len([p for p in run._queue if run._jobs[p].status == "not_started"])
                            except (ValueError, KeyError):
                                pass
                        # Return concise status for AI consumption
                        status_info = {
                            "package": pkg,
                            "status": job.status,
                            "current_step": job.current_step,
                            "build_progress": job.build_progress,
                            "elapsed_seconds": round(elapsed, 1) if elapsed else None,
                            "queue_position": f"{queue_position} of {queue_total}" if queue_position else None,
                            "error": job.error,
                            "build_rc": dict(job.build_rc),
                            "verify_rc": job.verify_rc,
                            "build_errors": dict(job.build_err),
                            "build_warnings": dict(job.build_warn),
                            "verify_errors": job.verify_err,
                            "verify_warnings": job.verify_warn,
                            "started_at": job.started_at,
                            "finished_at": job.finished_at,
                            "pr_url": job.published_pr_url,
                            "hints": {
                                "logs_endpoint": f"/api/package/{pkg}/logs",
                                "issues_endpoint": f"/api/package/{pkg}/issues",
                                "restart_endpoint": f"/api/package/{pkg}/restart (POST) - pauses another job for priority",
                            },
                        }
                        return self._send_json(HTTPStatus.OK, status_info)

                    if path.startswith("/api/package/"):
                        pkg = unquote(path.removeprefix("/api/package/")).strip("/")
                        job = run.get_job(pkg)
                        if not job:
                            return self._send_json(
                                HTTPStatus.NOT_FOUND, {"error": "unknown package"}
                            )

                        # Include small log excerpts for quick triage
                        excerpts: dict[str, str] = {}
                        for b, lp in job.build_logs.items():
                            try:
                                excerpts[f"build.{b}"] = _tail_file(
                                    Path(lp), n_lines=120
                                )
                            except Exception:
                                pass
                        if job.verify_log:
                            try:
                                excerpts["verify"] = _tail_file(
                                    Path(job.verify_log), n_lines=120
                                )
                            except Exception:
                                pass

                        todo_text = ""
                        try:
                            todo_text = Path(job.todo_path).read_text(encoding="utf-8")
                        except Exception:
                            todo_text = ""

                        return self._send_json(
                            HTTPStatus.OK,
                            {
                                "job": job.to_public(),
                                "todo": todo_text,
                                "excerpts": excerpts,
                            },
                        )

                    if path == "/kicanvas.js":
                        try:
                            return self._send(
                                HTTPStatus.OK,
                                "application/javascript; charset=utf-8",
                                kicanvas_js.read_bytes(),
                            )
                        except Exception as e:
                            return self._send_json(
                                HTTPStatus.INTERNAL_SERVER_ERROR, {"error": str(e)}
                            )

                    if path == "/model-viewer.min.js":
                        try:
                            return self._send(
                                HTTPStatus.OK,
                                "application/javascript; charset=utf-8",
                                model_viewer_js.read_bytes(),
                            )
                        except Exception as e:
                            return self._send_json(
                                HTTPStatus.INTERNAL_SERVER_ERROR, {"error": str(e)}
                            )

                    if path.startswith("/pcb/"):
                        # Accept either:
                        # - /pcb/<pkg>/<build>
                        # - /pcb/<pkg>/<build>.kicad_pcb   (preferred: matches real extension)
                        parts = path.split("/")
                        if len(parts) != 4:
                            return self._send_json(
                                HTTPStatus.BAD_REQUEST, {"error": "bad pcb path"}
                            )
                        _, _, pkg, build_part = parts
                        # KiCanvas requests `<build>.kicad_pcb` where `<build>` is the build name.
                        # For compatibility with our earlier API and any manual links, accept:
                        # - "<build>.kicad_pcb"
                        # - "<build>" (no suffix)
                        build = build_part.removesuffix(".kicad_pcb")
                        job = run.get_job(pkg)
                        if not job:
                            return self._send_json(
                                HTTPStatus.NOT_FOUND, {"error": "unknown package"}
                            )
                        pcb = job.layout_paths.get(build)
                        if not pcb:
                            # Fallback: resolve from canonical path on disk, even if `layout_paths`
                            # wasn't populated yet (early in a run).
                            pkg_dir = Path(job.package_dir)
                            candidate = (
                                pkg_dir / "layouts" / build / f"{build}.kicad_pcb"
                            )
                            if candidate.exists():
                                pcb = str(candidate)
                            else:
                                return self._send_json(
                                    HTTPStatus.NOT_FOUND, {"error": "pcb not found"}
                                )
                        p = Path(pcb)
                        if not p.exists():
                            return self._send_json(
                                HTTPStatus.NOT_FOUND, {"error": "pcb file missing"}
                            )
                        # KiCanvas parses KiCad's S-expression text.
                        # Use text/plain, and allow same-origin fetch.
                        return self._send(
                            HTTPStatus.OK,
                            "text/plain; charset=utf-8",
                            p.read_bytes(),
                        )

                    if path.startswith("/glb/"):
                        # Accept either:
                        # - /glb/<pkg>/<build>
                        # - /glb/<pkg>/<build>.glb
                        parts = path.split("/")
                        if len(parts) != 4:
                            return self._send_json(
                                HTTPStatus.BAD_REQUEST, {"error": "bad glb path"}
                            )
                        _, _, pkg, build_part = parts
                        build = build_part.removesuffix(".glb")
                        job = run.get_job(pkg)
                        if not job:
                            return self._send_json(
                                HTTPStatus.NOT_FOUND, {"error": "unknown package"}
                            )
                        glb = job.model_paths.get(build)
                        if not glb:
                            return self._send_json(
                                HTTPStatus.NOT_FOUND, {"error": "glb not found"}
                            )
                        p = Path(glb)
                        if not p.exists():
                            return self._send_json(
                                HTTPStatus.NOT_FOUND, {"error": "glb file missing"}
                            )
                        return self._send(
                            HTTPStatus.OK, "model/gltf-binary", p.read_bytes()
                        )

                    if path.startswith("/log/"):
                        # /log/<pkg>/<name> where name is "build.default.log" or "verify.log"
                        parts = path.split("/")
                        if len(parts) != 4:
                            return self._send_json(
                                HTTPStatus.BAD_REQUEST, {"error": "bad log path"}
                            )
                        _, _, pkg, name = parts
                        job = run.get_job(pkg)
                        if not job:
                            return self._send_json(
                                HTTPStatus.NOT_FOUND, {"error": "unknown package"}
                            )
                        lp: str | None = None
                        if name == "verify.log":
                            lp = job.verify_log
                        elif name.startswith("build.") and name.endswith(".log"):
                            build = name.removeprefix("build.").removesuffix(".log")
                            lp = job.build_logs.get(build)
                        elif name.startswith("run__"):
                            run_logs_dir = (Path(job.run_dir) / "logs").resolve()
                            candidate = (
                                run_logs_dir / name.removeprefix("run__")
                            ).resolve()
                            try:
                                candidate.relative_to(run_logs_dir)
                                lp = str(candidate)
                            except Exception:
                                lp = None
                        elif name.startswith("pkg__latest__"):
                            # `pkg__latest__<build>__<file>`
                            parts2 = name.split("__", 3)
                            if len(parts2) == 4:
                                _, _, build, fname = parts2
                                root = (
                                    Path(job.package_dir) / "build" / "logs" / "latest"
                                ).resolve()
                                candidate = (root / build / fname).resolve()
                                try:
                                    candidate.relative_to(root)
                                    lp = str(candidate)
                                except Exception:
                                    lp = None
                        if not lp:
                            # Avoid browser console spam while builds are still running.
                            return self._send(
                                HTTPStatus.OK,
                                "text/plain; charset=utf-8",
                                b"(log not ready yet)\n",
                            )
                        try:
                            p = Path(lp)
                            # Avoid freezing the browser by sending extremely large logs.
                            # Default to last 1MB; enough for context. (Reviewer can still open the file on disk.)
                            max_bytes = 1_000_000
                            data = p.read_bytes()
                            if len(data) > max_bytes:
                                data = (
                                    b"(log truncated to last 1MB for UI responsiveness)\n\n"
                                    + data[-max_bytes:]
                                )
                            return self._send(
                                HTTPStatus.OK, "text/plain; charset=utf-8", data
                            )
                        except Exception as e:
                            return self._send_json(
                                HTTPStatus.INTERNAL_SERVER_ERROR, {"error": str(e)}
                            )

                    # Static UI
                    if path == "/":
                        p = static_dir / "index.html"
                    else:
                        p = static_dir / path.lstrip("/")
                    if not p.exists():
                        return self._send_json(
                            HTTPStatus.NOT_FOUND, {"error": "not found"}
                        )

                    ct = "text/plain; charset=utf-8"
                    if p.name.endswith(".html"):
                        ct = "text/html; charset=utf-8"
                    elif p.name.endswith(".css"):
                        ct = "text/css; charset=utf-8"
                    elif p.name.endswith(".js"):
                        ct = "application/javascript; charset=utf-8"

                    return self._send(HTTPStatus.OK, ct, p.read_bytes())
                except Exception as e:
                    _log_line(f"{_now_ts()} EXC GET {self.path}: {type(e).__name__}: {e}")
                    return self._send_json(
                        HTTPStatus.INTERNAL_SERVER_ERROR, {"error": str(e)}
                    )

            def do_POST(self) -> None:  # noqa: N802
                self._t0 = time.perf_counter()
                try:
                    u = urlparse(self.path)
                    path = u.path

                    if path == "/api/sort_queue":
                        try:
                            payload = self._read_json()
                            order = payload.get("order", "asc")
                            run.sort_queue(order)
                            return self._send_json(HTTPStatus.OK, {"ok": True})
                        except Exception as e:
                            return self._send_json(
                                HTTPStatus.INTERNAL_SERVER_ERROR, {"error": str(e)}
                            )

                    if path.startswith("/api/package/") and path.endswith("/todo"):
                        pkg = unquote(
                            path.removeprefix("/api/package/").removesuffix("/todo")
                        ).strip("/")
                        try:
                            payload = self._read_json()
                            run.set_todo(pkg, payload.get("todo", ""))
                            return self._send_json(HTTPStatus.OK, {"ok": True})
                        except KeyError:
                            return self._send_json(
                                HTTPStatus.NOT_FOUND, {"error": "unknown package"}
                            )
                        except Exception as e:
                            return self._send_json(
                                HTTPStatus.INTERNAL_SERVER_ERROR, {"error": str(e)}
                            )

                    if path.startswith("/api/package/") and path.endswith("/approve"):
                        pkg = unquote(
                            path.removeprefix("/api/package/").removesuffix("/approve")
                        ).strip("/")
                        try:
                            payload = self._read_json()
                            reviewer = payload.get("reviewer")
                            run.approve(pkg, reviewer)
                            return self._send_json(HTTPStatus.OK, {"ok": True})
                        except KeyError:
                            return self._send_json(
                                HTTPStatus.NOT_FOUND, {"error": "unknown package"}
                            )
                        except Exception as e:
                            return self._send_json(
                                HTTPStatus.INTERNAL_SERVER_ERROR, {"error": str(e)}
                            )

                    if path.startswith("/api/package/") and path.endswith("/open"):
                        pkg = unquote(
                            path.removeprefix("/api/package/").removesuffix("/open")
                        ).strip("/")
                        try:
                            payload = self._read_json()
                            build = payload.get("build")
                            if not build:
                                return self._send_json(
                                    HTTPStatus.BAD_REQUEST, {"error": "missing build"}
                                )
                            run.open_kicad(pkg, build)
                            return self._send_json(HTTPStatus.OK, {"ok": True})
                        except KeyError:
                            return self._send_json(
                                HTTPStatus.NOT_FOUND, {"error": "unknown package"}
                            )
                        except Exception as e:
                            return self._send_json(
                                HTTPStatus.INTERNAL_SERVER_ERROR, {"error": str(e)}
                            )

                    if path.startswith("/api/package/") and path.endswith("/open_cursor"):
                        pkg = unquote(
                            path.removeprefix("/api/package/").removesuffix("/open_cursor")
                        ).strip("/")
                        try:
                            payload = self._read_json()
                            build = payload.get("build")
                            if not build:
                                return self._send_json(
                                    HTTPStatus.BAD_REQUEST, {"error": "missing build"}
                                )
                            run.open_cursor(pkg, build, cursor_cmd=cursor_cmd)
                            return self._send_json(HTTPStatus.OK, {"ok": True})
                        except KeyError:
                            return self._send_json(
                                HTTPStatus.NOT_FOUND, {"error": "unknown package"}
                            )
                        except Exception as e:
                            return self._send_json(
                                HTTPStatus.INTERNAL_SERVER_ERROR, {"error": str(e)}
                            )

                    if path.startswith("/api/package/") and path.endswith(
                        "/open_logs_cursor"
                    ):
                        pkg = unquote(
                            path.removeprefix("/api/package/").removesuffix(
                                "/open_logs_cursor"
                            )
                        ).strip("/")
                        try:
                            run.open_logs_in_cursor(pkg, cursor_cmd=cursor_cmd)
                            return self._send_json(HTTPStatus.OK, {"ok": True})
                        except KeyError:
                            return self._send_json(
                                HTTPStatus.NOT_FOUND, {"error": "unknown package"}
                            )
                        except Exception as e:
                            return self._send_json(
                                HTTPStatus.INTERNAL_SERVER_ERROR, {"error": str(e)}
                            )

                    # Start Cursor Agent for a package
                    if path.startswith("/api/package/") and path.endswith(
                        "/start_agent"
                    ):
                        pkg = unquote(
                            path.removeprefix("/api/package/").removesuffix(
                                "/start_agent"
                            )
                        ).strip("/")
                        try:
                            result = run.start_agent_for_package(pkg)
                            return self._send_json(HTTPStatus.OK, {"ok": True, **result})
                        except KeyError:
                            return self._send_json(
                                HTTPStatus.NOT_FOUND, {"error": "unknown package"}
                            )
                        except FileNotFoundError as e:
                            return self._send_json(
                                HTTPStatus.BAD_REQUEST, {"error": str(e)}
                            )
                        except Exception as e:
                            return self._send_json(
                                HTTPStatus.INTERNAL_SERVER_ERROR, {"error": str(e)}
                            )

                    if path.startswith("/api/package/") and path.endswith("/restart"):
                        pkg = unquote(
                            path.removeprefix("/api/package/").removesuffix("/restart")
                        ).strip("/")
                        try:
                            run.restart(pkg)
                            return self._send_json(HTTPStatus.OK, {"ok": True})
                        except KeyError:
                            return self._send_json(
                                HTTPStatus.NOT_FOUND, {"error": "unknown package"}
                            )
                        except Exception as e:
                            return self._send_json(
                                HTTPStatus.BAD_REQUEST, {"error": str(e)}
                            )

                    # AI agent message endpoint
                    if path.startswith("/api/package/") and path.endswith("/message"):
                        pkg = unquote(
                            path.removeprefix("/api/package/").removesuffix("/message")
                        ).strip("/")
                        try:
                            payload = self._read_json()
                            message = payload.get("message", "")
                            msg_type = payload.get("type", "info")
                            if not message:
                                return self._send_json(
                                    HTTPStatus.BAD_REQUEST, {"error": "message is required"}
                                )
                            msg_obj = run.add_agent_message(pkg, message, msg_type)
                            return self._send_json(HTTPStatus.OK, {"ok": True, "message": msg_obj})
                        except KeyError:
                            return self._send_json(
                                HTTPStatus.NOT_FOUND, {"error": "unknown package"}
                            )
                        except Exception as e:
                            return self._send_json(
                                HTTPStatus.INTERNAL_SERVER_ERROR, {"error": str(e)}
                            )

                    # AI agent request help endpoint
                    if path.startswith("/api/package/") and path.endswith("/request_help"):
                        pkg = unquote(
                            path.removeprefix("/api/package/").removesuffix("/request_help")
                        ).strip("/")
                        try:
                            payload = self._read_json()
                            reason = payload.get("reason", "AI needs human assistance")
                            run.request_user_help(pkg, reason)
                            return self._send_json(HTTPStatus.OK, {"ok": True, "status": "needs_input"})
                        except KeyError:
                            return self._send_json(
                                HTTPStatus.NOT_FOUND, {"error": "unknown package"}
                            )
                        except ValueError as e:
                            return self._send_json(
                                HTTPStatus.BAD_REQUEST, {"error": str(e)}
                            )
                        except Exception as e:
                            return self._send_json(
                                HTTPStatus.INTERNAL_SERVER_ERROR, {"error": str(e)}
                            )

                    # Resolve help request endpoint
                    if path.startswith("/api/package/") and path.endswith("/resolve_help"):
                        pkg = unquote(
                            path.removeprefix("/api/package/").removesuffix("/resolve_help")
                        ).strip("/")
                        try:
                            run.resolve_help_request(pkg)
                            return self._send_json(HTTPStatus.OK, {"ok": True})
                        except KeyError:
                            return self._send_json(
                                HTTPStatus.NOT_FOUND, {"error": "unknown package"}
                            )

                    # Clear agent messages endpoint
                    if path.startswith("/api/package/") and path.endswith("/clear_messages"):
                        pkg = unquote(
                            path.removeprefix("/api/package/").removesuffix("/clear_messages")
                        ).strip("/")
                        try:
                            run.clear_agent_messages(pkg)
                            return self._send_json(HTTPStatus.OK, {"ok": True})
                        except KeyError:
                            return self._send_json(
                                HTTPStatus.NOT_FOUND, {"error": "unknown package"}
                            )

                    if path.startswith("/api/package/") and path.endswith("/pause"):
                        pkg = unquote(
                            path.removeprefix("/api/package/").removesuffix("/pause")
                        ).strip("/")
                        try:
                            run.pause(pkg)
                            return self._send_json(HTTPStatus.OK, {"ok": True})
                        except KeyError:
                            return self._send_json(
                                HTTPStatus.NOT_FOUND, {"error": "unknown package"}
                            )
                        except Exception as e:
                            return self._send_json(
                                HTTPStatus.BAD_REQUEST, {"error": str(e)}
                            )

                    if path.startswith("/api/package/") and path.endswith("/unpause"):
                        pkg = unquote(
                            path.removeprefix("/api/package/").removesuffix("/unpause")
                        ).strip("/")
                        try:
                            run.unpause(pkg)
                            return self._send_json(HTTPStatus.OK, {"ok": True})
                        except KeyError:
                            return self._send_json(
                                HTTPStatus.NOT_FOUND, {"error": "unknown package"}
                            )
                        except Exception as e:
                            return self._send_json(
                                HTTPStatus.BAD_REQUEST, {"error": str(e)}
                            )

                    if path.startswith("/api/package/") and path.endswith("/prioritize"):
                        pkg = unquote(
                            path.removeprefix("/api/package/").removesuffix("/prioritize")
                        ).strip("/")
                        try:
                            run.prioritize(pkg)
                            return self._send_json(HTTPStatus.OK, {"ok": True})
                        except KeyError:
                            return self._send_json(
                                HTTPStatus.NOT_FOUND, {"error": "unknown package"}
                            )
                        except Exception as e:
                            return self._send_json(
                                HTTPStatus.BAD_REQUEST, {"error": str(e)}
                            )

                    if path.startswith("/api/package/") and path.endswith("/unapprove"):
                        pkg = unquote(
                            path.removeprefix("/api/package/").removesuffix("/unapprove")
                        ).strip("/")
                        try:
                            run.unapprove(pkg)
                            return self._send_json(HTTPStatus.OK, {"ok": True})
                        except KeyError:
                            return self._send_json(
                                HTTPStatus.NOT_FOUND, {"error": "unknown package"}
                            )
                        except Exception as e:
                            return self._send_json(
                                HTTPStatus.BAD_REQUEST, {"error": str(e)}
                            )

                    if path.startswith("/api/package/") and path.endswith("/publish"):
                        pkg = unquote(
                            path.removeprefix("/api/package/").removesuffix("/publish")
                        ).strip("/")
                        print(f"[PUBLISH] Starting publish for {pkg}", flush=True)
                        _log_line(f"{_now_ts()} PUBLISH: Starting publish for {pkg}")
                        try:
                            payload = self._read_json()
                            reviewer = payload.get("reviewer")
                            commit_message = payload.get("commit_message") or ""
                            target_requires_atopile = (
                                payload.get("target_requires_atopile") or "^0.14.0"
                            )
                            print(f"[PUBLISH] {pkg} reviewer={reviewer} target={target_requires_atopile}", flush=True)
                            _log_line(f"{_now_ts()} PUBLISH: {pkg} reviewer={reviewer} target={target_requires_atopile}")
                            res = run.publish(
                                pkg,
                                commit_message=commit_message,
                                reviewer=reviewer,
                                target_requires_atopile=target_requires_atopile,
                            )
                            print(f"[PUBLISH] {pkg} SUCCESS pr_url={res.get('pr_url')}", flush=True)
                            _log_line(f"{_now_ts()} PUBLISH: {pkg} SUCCESS pr_url={res.get('pr_url')}")
                            return self._send_json(
                                HTTPStatus.OK, {"ok": True, "result": res}
                            )
                        except PermissionError as e:
                            print(f"[PUBLISH] {pkg} PERMISSION ERROR: {e}", flush=True)
                            _log_line(f"{_now_ts()} PUBLISH: {pkg} PERMISSION ERROR: {e}")
                            return self._send_json(
                                HTTPStatus.FORBIDDEN, {"error": str(e)}
                            )
                        except KeyError:
                            print(f"[PUBLISH] {pkg} NOT FOUND", flush=True)
                            _log_line(f"{_now_ts()} PUBLISH: {pkg} NOT FOUND")
                            return self._send_json(
                                HTTPStatus.NOT_FOUND, {"error": "unknown package"}
                            )
                        except Exception as e:
                            print(f"[PUBLISH] {pkg} FAILED: {type(e).__name__}: {e}", flush=True)
                            _log_line(f"{_now_ts()} PUBLISH: {pkg} FAILED: {type(e).__name__}: {e}")
                            # Record the failure on the job for visibility in the UI.
                            try:
                                j = run.get_job(pkg)
                                if j:
                                    with run._lock:
                                        j.status = "error"
                                        j.publish_error = str(e)
                                        j.error = str(e)
                                        j.finished_at = _now_ts()
                                        run._write_state()
                            except Exception:
                                pass
                            return self._send_json(
                                HTTPStatus.BAD_REQUEST, {"error": str(e)}
                            )

                    # POST /api/package/{name}/uprev - quick version bump and PR
                    if path.startswith("/api/package/") and path.endswith("/uprev"):
                        pkg = unquote(
                            path.removeprefix("/api/package/").removesuffix("/uprev")
                        ).strip("/")
                        print(f"[UPREV] Starting uprev for {pkg}", flush=True)
                        try:
                            payload = self._read_json()
                            reviewer = payload.get("reviewer")
                            res = run.uprev_and_publish(pkg, reviewer=reviewer)
                            print(f"[UPREV] {pkg} SUCCESS: {res.get('old_version')} -> {res.get('new_version')}, pr_url={res.get('pr_url')}", flush=True)
                            return self._send_json(
                                HTTPStatus.OK, {"ok": True, "result": res}
                            )
                        except KeyError:
                            print(f"[UPREV] {pkg} NOT FOUND", flush=True)
                            return self._send_json(
                                HTTPStatus.NOT_FOUND, {"error": "unknown package"}
                            )
                        except Exception as e:
                            print(f"[UPREV] {pkg} FAILED: {type(e).__name__}: {e}", flush=True)
                            return self._send_json(
                                HTTPStatus.BAD_REQUEST, {"error": str(e)}
                            )

                    return self._send_json(
                        HTTPStatus.NOT_FOUND, {"error": "not found"}
                    )
                except Exception as e:
                    _log_line(f"{_now_ts()} EXC POST {self.path}: {type(e).__name__}: {e}")
                    return self._send_json(
                        HTTPStatus.INTERNAL_SERVER_ERROR, {"error": str(e)}
                    )

        # Best-effort reuse to avoid TIME_WAIT issues on fast restarts.
        ThreadingHTTPServer.allow_reuse_address = True
        try:
            httpd = ThreadingHTTPServer((self.host, self.port), Handler)
        except OSError as e:
            if getattr(e, "errno", None) == 48:  # macOS EADDRINUSE
                raise RuntimeError(
                    f"Port already in use: {self.host}:{self.port}\n\n"
                    f"Another review server is likely still running.\n"
                    f"- Stop it (Ctrl+C) in the terminal that started it, or\n"
                    f"- Re-run with a different `--port`, or\n"
                    f"- Re-run with `--kill-existing` (pidfile-based best-effort)\n"
                ) from e
            raise

        actual_port = int(httpd.server_address[1])
        return httpd, actual_port


@app.command()
def serve(
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
    jobs: Annotated[
        int, typer.Option(help="Max concurrent packages to build/verify.")
    ] = 2,
    max_ready: Annotated[
        int,
        typer.Option(
            help="Max number of packages to keep in awaiting_review/approved before pausing builds."
        ),
    ] = 10,
    keep_picked_parts: Annotated[
        bool,
        typer.Option(help="Pass --keep-picked-parts to builds (faster, stable picks)."),
    ] = True,
    out_dir: Annotated[
        Path,
        typer.Option(
            help="Output directory for review runs (default: ./build/review_webui)."
        ),
    ] = Path("build") / "review_webui",
    ato_cmd: Annotated[
        str,
        typer.Option(
            help=(
                "Command used to invoke Atopile. "
                "Examples: 'ato' or '/abs/path/to/atopile/.venv/bin/python -m atopile'"
            )
        ),
    ] = "",
    kicanvas_js: Annotated[
        Path | None,
        typer.Option(
            help="Path to kicanvas.js bundle (defaults to sibling atopile VSCode extension copy)."
        ),
    ] = None,
    model_viewer_js: Annotated[
        Path | None,
        typer.Option(
            help="Path to model-viewer.min.js bundle (defaults to sibling atopile VSCode extension copy)."
        ),
    ] = None,
    host: Annotated[
        str, typer.Option(help="Host to bind the web server.")
    ] = "127.0.0.1",
    port: Annotated[int, typer.Option(help="Port to bind the web server.")] = 8787,
    kill_existing: Annotated[
        bool,
        typer.Option(
            help="If set, tries to terminate the previous review server on the same host/port using a pidfile in out_dir."
        ),
    ] = False,
    open_cmd: Annotated[
        str,
        typer.Option(
            help="Command used to open a .kicad_pcb for review (e.g. 'open', 'open -a KiCad', 'xdg-open')."
        ),
    ] = "open",
    cursor_cmd: Annotated[
        str,
        typer.Option(
            help="Command used to open a file in Cursor (e.g. 'cursor', 'open -a Cursor')."
        ),
    ] = "",
    publish_anyway: Annotated[
        bool,
        typer.Option(
            help="Allow publishing even if build/verify are not successful (unsafe; overrides publish guard)."
        ),
    ] = False,
    registry_url: Annotated[
        str,
        typer.Option(
            help=(
                "Packages registry base URL for published-version checks "
                "(default matches atopile config default)."
            )
        ),
    ] = "https://packages.atopileapi.com",
    registry_refresh_seconds: Annotated[
        float,
        typer.Option(
            help="How often to refresh registry metadata per package (seconds)."
        ),
    ] = 60.0,
) -> None:
    if shard_index < 0 or shard_index >= shard_count:
        raise typer.BadParameter("--shard-index must be within [0, shard_count)")

    packages_root = packages_root.resolve()
    if not packages_root.exists():
        raise typer.BadParameter(f"packages_root not found: {packages_root}")

    packages_repo_root = packages_root.parent.resolve()
    ato_cmd_list = (
        shlex.split(ato_cmd)
        if ato_cmd.strip()
        else _default_ato_cmd(packages_repo_root)
    )

    if kicanvas_js is None:
        kicanvas_js = _default_kicanvas_js(packages_repo_root)
    if kicanvas_js is None or not kicanvas_js.exists():
        raise typer.BadParameter(
            "kicanvas.js not found. Pass --kicanvas-js explicitly, or ensure the sibling "
            "`atopile/src/vscode-atopile/resources/kicanvas/kicanvas.js` exists."
        )

    if model_viewer_js is None:
        model_viewer_js = _default_model_viewer_js(packages_repo_root)
    if model_viewer_js is None or not model_viewer_js.exists():
        raise typer.BadParameter(
            "model-viewer.min.js not found. Pass --model-viewer-js explicitly, or ensure the sibling "
            "`atopile/src/vscode-atopile/resources/model-viewer/model-viewer.min.js` exists."
        )

    pkgs = _discover_packages(packages_root)
    pkgs = _select_by_regex(pkgs, package_regex)
    pkgs = _select_by_shard(pkgs, shard_count=shard_count, shard_index=shard_index)

    out_dir = out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    pidfile = out_dir / f"_review_webui_{host}_{port}.pid"
    if kill_existing and pidfile.exists():
        try:
            old_pid_s = pidfile.read_text(encoding="utf-8").strip()
            old_pid = int(old_pid_s)
            if old_pid > 0:
                os.kill(old_pid, signal.SIGTERM)
                time.sleep(0.4)
        except Exception:
            pass

    run_id = _now_id()
    run_dir = (out_dir / run_id).resolve()
    run_dir.mkdir(parents=True, exist_ok=True)

    server_origin = f"http://{host}:{port}"
    rr = ReviewRun(
        packages_root=packages_root,
        selected_packages=pkgs,
        jobs=jobs,
        run_dir=run_dir,
        ato_cmd=ato_cmd_list,
        keep_picked_parts=keep_picked_parts,
        open_cmd=open_cmd,
        max_ready=max_ready,
        server_origin=server_origin,
        packages_repo_root=packages_repo_root,
        publish_anyway=publish_anyway,
        registry_url=registry_url,
        registry_refresh_seconds=registry_refresh_seconds,
    )
    rr.start()

    # Record pid for `--kill-existing` convenience.
    try:
        pidfile.write_text(str(os.getpid()), encoding="utf-8")
    except Exception:
        pass

    Server(
        host=host,
        port=port,
        run=rr,
        kicanvas_js=kicanvas_js.resolve(),
        model_viewer_js=model_viewer_js.resolve(),
        cursor_cmd=(cursor_cmd.strip() or _default_cursor_cmd()),
    ).serve()


if __name__ == "__main__":
    app()
