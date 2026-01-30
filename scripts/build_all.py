#! uv run
# /// script
# dependencies = [
#   "typer>=0.12",
#   "typing_extensions>=4.10.0",
#   "rich>=13.0.0",
# ]
# ///

import re
import typer
import subprocess
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.progress import (
    Progress,
    SpinnerColumn,
    BarColumn,
    TextColumn,
    TimeElapsedColumn,
)

app = typer.Typer()

console = Console()


def build_package(package_dir: Path, args: tuple) -> tuple[str, bool]:
    """Builds a single package using 'ato build' and captures output."""
    package_name = package_dir.name
    args_str = " with args:" + (" ".join(args)) if args else ""
    console.print(f"[yellow]🔨 Building package in {package_name}{args_str}[/yellow]")
    try:
        # Convert args tuple to a list for subprocess
        process = subprocess.run(
            ["ato", "build"] + list(args),
            cwd=package_dir,
            capture_output=True,
            text=True,
            check=True,
        )
        console.print(f"[green]✅ Successfully built {package_name}[/green]")
        # console.print(f"Output:\n{process.stdout}") # Optional: print stdout
        return package_name, True
    except subprocess.CalledProcessError as e:
        console.print(f"[red]❌ Error occurred in directory: {package_name}[/red]")
        # console.print(f"Stderr:\n{e.stderr}")
        return package_name, False


@app.command()
def main(
    args: list[str] = typer.Argument(None, help="Arguments to pass to ato build"),
    package_regex: str = typer.Option(None, help="Regex to filter packages to build"),
):
    """Builds all packages in the 'packages' directory in parallel."""
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

    successful_builds = []
    failed_builds = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task = progress.add_task(
            "[cyan]Building packages...[/cyan]", total=len(package_subdirs)
        )
        with ProcessPoolExecutor() as executor:
            futures = {
                executor.submit(build_package, subdir, build_args): subdir
                for subdir in package_subdirs
            }
            for future in as_completed(futures):
                package_name, success = future.result()
                if success:
                    successful_builds.append(package_name)
                else:
                    failed_builds.append(package_name)
                progress.update(task, advance=1)

    # Print summary report
    console.print("\n[bold blue]📊 Build Summary Report[/bold blue]")
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Status", style="dim", width=12)
    table.add_column("Package Name")

    console.print(f"\n[green]✅ Successful builds ({len(successful_builds)}):[/green]")
    for build in sorted(successful_builds):
        console.print(f"  - {build}")

    console.print(f"\n[red]❌ Failed builds ({len(failed_builds)}):[/red]")
    for build in sorted(failed_builds):
        console.print(f"  - {build}")

    console.print(f"\n[bold]📈 Total packages: {len(package_subdirs)}[/bold]")
    console.print(f"[green]✅ Successful: {len(successful_builds)}[/green]")
    console.print(f"[red]❌ Failed: {len(failed_builds)}[/red]")

    if failed_builds:
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
