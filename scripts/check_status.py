#!/usr/bin/env python3
# /// script
# dependencies = [
#   "typer>=0.12",
#   "typing_extensions>=4.10.0",
#   "rich>=13.0.0",
#   "pandas>=2.0.0",
# ]
# ///
"""
Check build status of all packages using the atopile backend.

Usage:
    # Using system ato:
    uv run scripts/check_status.py

    # Using atopile from a specific directory (e.g., atopile_reorg):
    uv run scripts/check_status.py --atopile-dir ~/github/atopile_reorg

    # Filter packages by regex:
    uv run scripts/check_status.py --package-regex "adi-.*"
"""

import re
import time
import subprocess
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Optional
import typer
from rich.console import Console, Group
from rich.table import Table
from rich.live import Live

app = typer.Typer()

console = Console()

# Global to hold the ato command path (set in main, used by workers)
_ato_cmd: list[str] = ["ato"]


def get_ato_command(atopile_dir: Optional[Path] = None) -> list[str]:
    """
    Get the ato command to use.
    If atopile_dir is provided, use the ato from that directory's venv.
    """
    if atopile_dir:
        venv_ato = atopile_dir / ".venv" / "bin" / "ato"
        if venv_ato.exists():
            return [str(venv_ato)]
        else:
            console.print(
                f"[yellow]Warning: {venv_ato} not found, falling back to system ato[/yellow]"
            )
    return ["ato"]


def build_package(
    package_dir: Path, args: tuple, ato_cmd: list[str]
) -> tuple[str, bool, float, int, str, str]:
    """
    Runs 'ato build --keep-picked-parts' for a package.
    Returns: (package_name, build_success, build_seconds, returncode, stdout, stderr)
    """
    package_name = package_dir.name

    # Build
    build_start = time.perf_counter()
    build_proc = subprocess.run(
        ato_cmd + ["build", "--keep-picked-parts"] + list(args),
        cwd=package_dir,
        capture_output=True,
        text=True,
        check=False,
    )
    build_success = build_proc.returncode == 0
    build_seconds = max(0.0, time.perf_counter() - build_start)

    return (
        package_name,
        build_success,
        build_seconds,
        build_proc.returncode,
        build_proc.stdout,
        build_proc.stderr,
    )


def _worker_init(ato_cmd: list[str]):
    """Initialize worker process with ato command."""
    global _ato_cmd
    _ato_cmd = ato_cmd


def _worker_build(args: tuple[Path, tuple]) -> tuple[str, bool, float, int, str, str]:
    """Worker function that uses the global ato command."""
    package_dir, build_args = args
    return build_package(package_dir, build_args, _ato_cmd)


@app.command()
def main(
    args: list[str] = typer.Argument(None, help="Arguments to pass to ato build"),
    package_regex: str = typer.Option(None, help="Regex to filter packages to build"),
    atopile_dir: Optional[Path] = typer.Option(
        None,
        "--atopile-dir",
        "-a",
        help="Path to atopile directory (uses its .venv/bin/ato)",
    ),
    max_workers: int = typer.Option(
        None, "--workers", "-w", help="Max parallel workers (default: CPU count)"
    ),
):
    """
    Builds all packages in the 'packages' directory in parallel.

    Uses the atopile backend from the specified directory, or system ato if not specified.
    """
    original_dir = Path.cwd()
    packages_dir = Path("packages")

    # Resolve atopile directory
    if atopile_dir:
        atopile_dir = Path(atopile_dir).expanduser().resolve()
        if not atopile_dir.exists():
            console.print(f"[red]❌ Error: atopile directory not found: {atopile_dir}[/red]")
            raise typer.Exit(code=1)

    ato_cmd = get_ato_command(atopile_dir)
    console.print(f"[dim]Using ato command: {' '.join(ato_cmd)}[/dim]")

    # Check ato version
    try:
        version_proc = subprocess.run(
            ato_cmd + ["--version"],
            capture_output=True,
            text=True,
            check=False,
        )
        if version_proc.returncode == 0:
            console.print(f"[dim]ato version: {version_proc.stdout.strip()}[/dim]")
    except Exception as e:
        console.print(f"[yellow]Warning: Could not get ato version: {e}[/yellow]")

    if not packages_dir.is_dir():
        console.print(
            f"[red]❌ Error: 'packages' directory not found in {original_dir}[/red]"
        )
        raise typer.Exit(code=1)

    package_subdirs = sorted([d for d in packages_dir.iterdir() if d.is_dir()])

    if not package_subdirs:
        console.print(f"[yellow]No packages found in {packages_dir}[/yellow]")
        return

    if package_regex:
        package_subdirs = [
            d for d in package_subdirs if re.match(package_regex, d.name)
        ]
        console.print(f"[dim]Filtered to {len(package_subdirs)} packages matching '{package_regex}'[/dim]")

    build_args = tuple(args) if args else ()

    # Accumulator for results
    results_rows: list[dict] = []
    total_packages = len(package_subdirs)

    def make_summary_tables() -> Group:
        # Totals
        build_fail = sum(1 for r in results_rows if r["build_success"] is False)
        build_pass = sum(1 for r in results_rows if r["build_success"] is True)
        pending = total_packages - len(results_rows)

        # Top summary table with counts in headers
        summary = Table(show_header=True, header_style="bold magenta")
        summary.add_column(f"Fails ({build_fail})", justify="center")
        summary.add_column(f"Passes ({build_pass})", justify="center")
        summary.add_column(f"Pending ({pending})", justify="center")
        summary.add_row(
            f"[red]{build_fail}[/red]",
            f"[green]{build_pass}[/green]",
            f"[dim]{pending}[/dim]",
        )

        # Detailed per-package table
        detail = Table(show_header=True, header_style="bold cyan")
        detail.add_column("Package", overflow="fold")
        detail.add_column("Build", justify="center")
        detail.add_column("Time (s)", justify="right")

        # Sort by build time (descending: slowest first)
        for r in sorted(results_rows, key=lambda x: x["build_seconds"], reverse=True):
            build_cell = (
                "[green]PASS[/green]" if r["build_success"] else "[red]FAIL[/red]"
            )
            detail.add_row(
                r["package_name"],
                build_cell,
                f"{r['build_seconds']:.1f}",
            )

        return Group(summary, detail)

    console.print(f"\n[bold]Building {total_packages} packages...[/bold]\n")

    with Live(console=console, refresh_per_second=4) as live:
        with ProcessPoolExecutor(
            max_workers=max_workers,
            initializer=_worker_init,
            initargs=(ato_cmd,),
        ) as executor:
            futures = {
                executor.submit(_worker_build, (subdir, build_args)): subdir
                for subdir in package_subdirs
            }
            for future in as_completed(futures):
                (
                    package_name,
                    build_ok,
                    build_secs,
                    build_rc,
                    build_out,
                    build_err,
                ) = future.result()
                results_rows.append(
                    {
                        "package_name": package_name,
                        "build_success": build_ok,
                        "build_seconds": build_secs,
                        "build_rc": build_rc,
                        "build_stdout": build_out,
                        "build_stderr": build_err,
                    }
                )
                # Update live tables
                live.update(make_summary_tables())

    # Print final summary
    build_fail = sum(1 for r in results_rows if not r["build_success"])
    build_pass = sum(1 for r in results_rows if r["build_success"])
    console.print(f"\n[bold]Summary: {build_pass} passed, {build_fail} failed[/bold]")

    # Construct DataFrame (optional) and save to CSV if pandas is available
    try:
        pd = __import__("pandas")
        df = pd.DataFrame(
            results_rows,
            columns=[
                "package_name",
                "build_success",
                "build_seconds",
            ],
        )
        out_csv = Path("build_status.csv")
        df.to_csv(out_csv, index=False)
        console.print(f"[dim]Saved build status to {out_csv.resolve()}[/dim]")
    except Exception:
        console.print(
            "[yellow]pandas not available; skipping DataFrame export[/yellow]"
        )

    # Exit with non-zero if any failed build; print detailed logs
    failed_packages = [r for r in results_rows if not r["build_success"]]
    if failed_packages:
        console.rule("[bold red]Failure Details")
        for r in sorted(failed_packages, key=lambda x: x["package_name"].lower()):
            console.print(
                f"[red]❌ {r['package_name']} – Build failed (rc={r.get('build_rc')})[/red]"
            )
            if r.get("build_stderr"):
                console.print("[bold]stderr:[/bold]")
                console.print(r["build_stderr"])
            if r.get("build_stdout"):
                console.print("[bold]stdout:[/bold]")
                console.print(r["build_stdout"])
            console.print()
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
