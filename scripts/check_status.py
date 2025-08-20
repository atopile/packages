#! uv run
# /// script
# dependencies = [
#   "typer>=0.12",
#   "typing_extensions>=4.10.0",
#   "rich>=13.0.0",
#   "pandas>=2.0.0",
# ]
# ///

import re
import time
import subprocess
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
import typer
from rich.console import Console, Group
from rich.table import Table
from rich.live import Live

app = typer.Typer()

console = Console()


def build_and_verify(
    package_dir: Path, args: tuple
) -> tuple[
    str,
    bool,
    bool,
    float,
    int,
    str,
    str,
    int | None,
    str | None,
    str | None,
]:
    """
    Runs 'ato build --keep-picked-parts' then 'ato package verify' for a package.
    Returns: (package_name, build_success, verify_success, build_seconds)
    """
    package_name = package_dir.name

    # Build
    build_start = time.perf_counter()
    build_proc = subprocess.run(
        ["ato", "build", "--keep-picked-parts"] + list(args),
        cwd=package_dir,
        capture_output=True,
        text=True,
        check=False,
    )
    build_success = build_proc.returncode == 0
    build_seconds = max(0.0, time.perf_counter() - build_start)

    # Verify (only if build ok)
    verify_success = False
    verify_rc: int | None = None
    verify_stdout: str | None = None
    verify_stderr: str | None = None
    if build_success:
        verify_proc = subprocess.run(
            ["ato", "package", "verify"],
            cwd=package_dir,
            capture_output=True,
            text=True,
            check=False,
        )
        verify_rc = verify_proc.returncode
        verify_stdout = verify_proc.stdout
        verify_stderr = verify_proc.stderr
        verify_success = verify_rc == 0

    return (
        package_name,
        build_success,
        verify_success,
        build_seconds,
        build_proc.returncode,
        build_proc.stdout,
        build_proc.stderr,
        verify_rc,
        verify_stdout,
        verify_stderr,
    )


@app.command()
def main(
    args: list[str] = typer.Argument(None, help="Arguments to pass to ato build"),
    package_regex: str = typer.Option(None, help="Regex to filter packages to build"),
):
    """Builds and verifies all packages in the 'packages' directory in parallel."""
    original_dir = Path.cwd()
    packages_dir = Path("packages")

    if not packages_dir.is_dir():
        console.print(
            f"[red]❌ Error: 'packages' directory not found in {original_dir}[/red]"
        )
        return

    package_subdirs = [d for d in packages_dir.iterdir() if d.is_dir()]

    if not package_subdirs:
        console.print(f"[yellow]No packages found in {packages_dir}[/yellow]")
        return

    if package_regex:
        package_subdirs = [
            d for d in package_subdirs if re.match(package_regex, d.name)
        ]

    build_args = tuple(args) if args else ()

    # Accumulator for results and DataFrame
    results_rows: list[dict] = []

    def make_summary_tables() -> Group:
        # Totals
        build_fail = sum(1 for r in results_rows if r["build_success"] is False)
        verify_fail = sum(
            1 for r in results_rows if r["build_success"] and not r["verify_success"]
        )
        pass_both = sum(
            1 for r in results_rows if r["build_success"] and r["verify_success"]
        )

        # Top summary table with counts in headers
        summary = Table(show_header=True, header_style="bold magenta")
        summary.add_column(f"Fails Build ({build_fail})", justify="center")
        summary.add_column(f"Fails Verify ({verify_fail})", justify="center")
        summary.add_column(f"Passes Both ({pass_both})", justify="center")
        summary.add_row(
            f"[red]{build_fail}[/red]",
            f"[yellow]{verify_fail}[/yellow]",
            f"[green]{pass_both}[/green]",
        )

        # Detailed per-package table
        detail = Table(show_header=True, header_style="bold cyan")
        detail.add_column("Package", overflow="fold")
        detail.add_column("Build", justify="center")
        detail.add_column("Verify", justify="center")
        detail.add_column("Build Time (s)", justify="right")

        # Sort by build time (descending: slowest first)
        for r in sorted(results_rows, key=lambda x: x["build_seconds"], reverse=True):
            build_cell = (
                "[green]PASS[/green]" if r["build_success"] else "[red]FAIL[/red]"
            )
            if not r["build_success"]:
                verify_cell = "[dim]-[/dim]"
            else:
                verify_cell = (
                    "[green]PASS[/green]" if r["verify_success"] else "[red]FAIL[/red]"
                )
            detail.add_row(
                r["package_name"],
                build_cell,
                verify_cell,
                f"{r['build_seconds']:.1f}",
            )

        return Group(summary, detail)

    with Live(console=console, refresh_per_second=8) as live:
        with ProcessPoolExecutor() as executor:
            futures = {
                executor.submit(build_and_verify, subdir, build_args): subdir
                for subdir in package_subdirs
            }
            for future in as_completed(futures):
                (
                    package_name,
                    build_ok,
                    verify_ok,
                    build_secs,
                    build_rc,
                    build_out,
                    build_err,
                    verify_rc,
                    verify_out,
                    verify_err,
                ) = future.result()
                results_rows.append(
                    {
                        "package_name": package_name,
                        "build_success": build_ok,
                        "verify_success": verify_ok,
                        "build_seconds": build_secs,
                        "build_rc": build_rc,
                        "build_stdout": build_out,
                        "build_stderr": build_err,
                        "verify_rc": verify_rc,
                        "verify_stdout": verify_out,
                        "verify_stderr": verify_err,
                    }
                )
                # Update live tables
                live.update(make_summary_tables())

    # Construct DataFrame (optional) and save to CSV if pandas is available
    try:
        pd = __import__("pandas")
        df = pd.DataFrame(
            results_rows,
            columns=[
                "package_name",
                "build_success",
                "verify_success",
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

    # Exit with non-zero if any failed build or failed verify; print detailed logs
    any_failed = any(
        (not r["build_success"]) or (r["build_success"] and not r["verify_success"])
        for r in results_rows
    )
    if any_failed:
        console.rule("[bold red]Failure Details")
        for r in sorted(results_rows, key=lambda x: x["package_name"].lower()):
            if not r["build_success"]:
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
                continue
            if r["build_success"] and not r["verify_success"]:
                console.print(
                    f"[yellow]⚠️ {r['package_name']} – Verify failed (rc={r.get('verify_rc')})[/yellow]"
                )
                if r.get("verify_stderr"):
                    console.print("[bold]stderr:[/bold]")
                    console.print(r["verify_stderr"])
                if r.get("verify_stdout"):
                    console.print("[bold]stdout:[/bold]")
                    console.print(r["verify_stdout"])
                console.print()
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
