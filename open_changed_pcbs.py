#!/usr/bin/env python3
"""
Script to open all changed KiCad PCB files for manual review.
This script identifies PCB files that have changed in the current PR and opens them in KiCad.
"""

import subprocess
import sys
import time
from pathlib import Path


def get_changed_pcb_files():
    """Get list of changed KiCad PCB files from the last 10 commits."""
    try:
        # Get changed files from the last 10 commits
        result = subprocess.run(
            ["git", "diff", "HEAD~10..HEAD", "--name-only"],
            capture_output=True,
            text=True,
            check=True,
        )

        # Filter for .kicad_pcb files
        changed_files = []
        for line in result.stdout.strip().split("\n"):
            if line.endswith(".kicad_pcb"):
                changed_files.append(line)

        return changed_files

    except subprocess.CalledProcessError as e:
        print(f"Error getting git diff: {e}")
        return []


def find_kicad_executable():
    """Find the KiCad PCB editor executable."""
    possible_paths = [
        "/Applications/KiCad/KiCad.app/Contents/MacOS/pcbnew",  # macOS
        "/usr/bin/pcbnew",  # Linux
        "/usr/local/bin/pcbnew",  # Linux alternative
        "pcbnew",  # If it's in PATH
    ]

    for path in possible_paths:
        try:
            result = subprocess.run(
                [path, "--version"], capture_output=True, check=True
            )
            print(f"Found KiCad at: {path}")
            return path
        except (subprocess.CalledProcessError, FileNotFoundError):
            continue

    print("Could not find KiCad PCB editor. Please ensure KiCad is installed.")
    return None


def open_pcb_file(kicad_path, pcb_file):
    """Open a single PCB file in KiCad."""
    pcb_path = Path(pcb_file)

    if not pcb_path.exists():
        print(f"Warning: PCB file does not exist: {pcb_file}")
        return False

    try:
        print(f"Opening: {pcb_file}")
        # Open KiCad PCB editor with the file
        subprocess.Popen([kicad_path, str(pcb_path.absolute())])
        return True
    except Exception as e:
        print(f"Error opening {pcb_file}: {e}")
        return False


def main():
    print("=== KiCad PCB Review Script ===")
    print("This script will open all changed KiCad PCB files for manual review.\n")

    # Get the project root directory
    project_root = Path.cwd()
    print(f"Working directory: {project_root}")

    # Get changed PCB files
    print("Getting list of changed PCB files...")
    changed_pcbs = get_changed_pcb_files()

    if not changed_pcbs:
        print("No changed PCB files found.")
        return

    print(f"Found {len(changed_pcbs)} changed PCB files:")
    for pcb in changed_pcbs:
        print(f"  - {pcb}")

    # Find KiCad executable
    kicad_path = find_kicad_executable()
    if not kicad_path:
        return

    # Ask for confirmation
    response = input(
        f"\nDo you want to open all {len(changed_pcbs)} PCB files? (y/N): "
    )
    if response.lower() not in ["y", "yes"]:
        print("Cancelled.")
        return

    # Open each PCB file
    print("\nOpening PCB files...")
    opened_count = 0

    for pcb_file in changed_pcbs:
        if open_pcb_file(kicad_path, pcb_file):
            opened_count += 1
            # Small delay between opening files to avoid overwhelming the system
            time.sleep(1)

    print(f"\nSuccessfully opened {opened_count} out of {len(changed_pcbs)} PCB files.")
    print("\nNote: Each PCB file should now be open in a separate KiCad window.")
    print("Review each PCB for:")
    print("  - Layout correctness")
    print("  - Component placement")
    print("  - Routing integrity")
    print("  - Design rule compliance")
    print("  - Any unexpected changes")


if __name__ == "__main__":
    main()
