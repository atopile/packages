#! uv run
# /// script
# dependencies = [
#   "typer>=0.12",
#   "rich>=13.0.0",
# ]
# ///

import subprocess
import sys
import os
from pathlib import Path
import typer
from rich.console import Console
from rich.prompt import Confirm
from rich.table import Table
from rich.panel import Panel

app = typer.Typer()
console = Console()


def get_modified_pcb_files(base_branch: str = "origin/main") -> list[Path]:
    """Get all modified .kicad_pcb files compared to the base branch."""
    try:
        # Get all modified files
        result = subprocess.run(
            ["git", "diff", "--name-only", f"{base_branch}...HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )

        # Filter for .kicad_pcb files
        all_files = result.stdout.strip().split("\n")
        pcb_files = [
            Path(f) for f in all_files if f.endswith(".kicad_pcb") and f.strip()
        ]

        # Filter to only existing files (in case some were deleted)
        existing_pcb_files = [f for f in pcb_files if f.exists()]

        return existing_pcb_files

    except subprocess.CalledProcessError as e:
        console.print(f"[red]Error getting git diff: {e}[/red]")
        return []


def open_pcb_file(file_path: Path) -> bool:
    """Open a PCB file with the default application."""
    try:
        if sys.platform == "darwin":  # macOS
            subprocess.run(["open", str(file_path)], check=True)
        elif sys.platform == "linux":
            subprocess.run(["xdg-open", str(file_path)], check=True)
        elif sys.platform == "win32":
            os.startfile(str(file_path))
        else:
            console.print(f"[yellow]Unsupported platform: {sys.platform}[/yellow]")
            console.print(f"Please manually open: {file_path}")
            return False
        return True
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Error opening file {file_path}: {e}[/red]")
        return False
    except Exception as e:
        console.print(f"[red]Unexpected error opening file {file_path}: {e}[/red]")
        return False


@app.command()
def main(
    base_branch: str = typer.Option(
        "origin/main", "--base", "-b", help="Base branch to compare against"
    ),
    auto_open: bool = typer.Option(
        False,
        "--auto-open",
        "-a",
        help="Automatically open all files without prompting",
    ),
):
    """
    Find modified .kicad_pcb files in the current branch and interactively open them for review.

    This script will:
    1. Find all .kicad_pcb files modified compared to the base branch
    2. Display them in a table
    3. Allow you to open each one by pressing Enter (or skip with any other key)
    """

    # Check if we're in a git repository
    try:
        subprocess.run(
            ["git", "rev-parse", "--git-dir"], capture_output=True, check=True
        )
    except subprocess.CalledProcessError:
        console.print("[red]❌ Error: Not in a git repository[/red]")
        raise typer.Exit(1)

    console.print(
        f"[bold blue]🔍 Finding modified .kicad_pcb files compared to {base_branch}...[/bold blue]"
    )

    pcb_files = get_modified_pcb_files(base_branch)

    if not pcb_files:
        console.print("[yellow]No modified .kicad_pcb files found.[/yellow]")
        return

    # Display summary table
    table = Table(
        title="Modified PCB Files", show_header=True, header_style="bold magenta"
    )
    table.add_column("File", style="cyan", overflow="fold")
    table.add_column("Package", style="green")
    table.add_column("Size", justify="right", style="dim")

    for pcb_file in pcb_files:
        # Extract package name (assuming structure: packages/package-name/...)
        parts = pcb_file.parts
        package_name = "unknown"
        if len(parts) >= 2 and parts[0] == "packages":
            package_name = parts[1]

        # Get file size
        try:
            size = pcb_file.stat().st_size
            size_str = f"{size:,} bytes"
        except:
            size_str = "unknown"

        table.add_row(str(pcb_file), package_name, size_str)

    console.print(table)
    console.print()

    if auto_open:
        console.print("[bold yellow]Auto-opening all files...[/bold yellow]")
        for pcb_file in pcb_files:
            console.print(f"Opening: [cyan]{pcb_file}[/cyan]")
            open_pcb_file(pcb_file)
        return

    # Interactive review
    console.print(
        Panel.fit(
            "[bold]Interactive Review Mode[/bold]\n\n"
            "For each file:\n"
            "• Press [green]Enter[/green] to open the file\n"
            "• Press [red]any other key[/red] to skip\n"
            "• Press [yellow]Ctrl+C[/yellow] to exit",
            border_style="blue",
        )
    )
    console.print()

    opened_count = 0
    skipped_count = 0

    try:
        for i, pcb_file in enumerate(pcb_files, 1):
            console.print(
                f"[bold]File {i}/{len(pcb_files)}:[/bold] [cyan]{pcb_file}[/cyan]"
            )

            try:
                # Wait for user input
                user_input = input("Press Enter to open (any other key to skip): ")

                if user_input == "":  # Enter was pressed
                    console.print(f"[green]Opening {pcb_file}...[/green]")
                    if open_pcb_file(pcb_file):
                        opened_count += 1
                    else:
                        console.print("[red]Failed to open file[/red]")
                else:
                    console.print("[yellow]Skipped[/yellow]")
                    skipped_count += 1

            except KeyboardInterrupt:
                console.print("\n[yellow]Interrupted by user[/yellow]")
                break

            console.print()

    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")

    # Summary
    console.print(
        Panel.fit(
            f"[bold]Review Summary[/bold]\n\n"
            f"Files found: {len(pcb_files)}\n"
            f"Files opened: [green]{opened_count}[/green]\n"
            f"Files skipped: [yellow]{skipped_count}[/yellow]",
            border_style="green",
        )
    )


if __name__ == "__main__":
    app()
