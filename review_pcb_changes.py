#!/usr/bin/env python3
"""
Advanced script to review KiCad PCB changes with detailed diff information.
This script shows what changed in each PCB file and provides options for selective opening.
"""

import subprocess
import sys
import time
from pathlib import Path
import json


def get_changed_pcb_files_with_stats():
    """Get list of changed KiCad PCB files with change statistics."""
    try:
        # Get changed files with stats
        result = subprocess.run(
            ["git", "diff", "HEAD~10..HEAD", "--stat", "--name-only"],
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


def get_file_change_summary(file_path):
    """Get a summary of changes for a specific file."""
    try:
        # Get the diff stats for this specific file
        result = subprocess.run(
            ["git", "diff", "HEAD~10..HEAD", "--numstat", file_path],
            capture_output=True,
            text=True,
            check=True,
        )

        if result.stdout.strip():
            parts = result.stdout.strip().split("\t")
            if len(parts) >= 2:
                additions = parts[0] if parts[0] != "-" else "0"
                deletions = parts[1] if parts[1] != "-" else "0"
                return f"+{additions} -{deletions}"

        return "No stats available"

    except subprocess.CalledProcessError:
        return "Error getting stats"


def show_file_changes(file_path):
    """Show a brief summary of what changed in the file."""
    try:
        # Get a condensed diff to understand what changed
        result = subprocess.run(
            [
                "git",
                "diff",
                "HEAD~10..HEAD",
                "--word-diff=color",
                "--no-index",
                "--",
                file_path,
            ],
            capture_output=True,
            text=True,
        )

        # For binary files like PCB, we can't show meaningful diffs
        # Instead, let's show the commit messages that affected this file
        commit_result = subprocess.run(
            ["git", "log", "HEAD~10..HEAD", "--oneline", "--", file_path],
            capture_output=True,
            text=True,
            check=True,
        )

        if commit_result.stdout.strip():
            return commit_result.stdout.strip().split("\n")
        else:
            return ["No commit messages found for this file"]

    except subprocess.CalledProcessError:
        return ["Error getting change information"]


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
        subprocess.Popen([kicad_path, str(pcb_path.absolute())])
        return True
    except Exception as e:
        print(f"Error opening {pcb_file}: {e}")
        return False


def main():
    print("=== Advanced KiCad PCB Review Script ===")
    print("This script analyzes and opens changed KiCad PCB files for manual review.\n")

    # Get the project root directory
    project_root = Path.cwd()
    print(f"Working directory: {project_root}")

    # Get changed PCB files
    print("Analyzing changed PCB files...")
    changed_pcbs = get_changed_pcb_files_with_stats()

    if not changed_pcbs:
        print("No changed PCB files found.")
        return

    # Show detailed information about each file
    print(f"\nFound {len(changed_pcbs)} changed PCB files:\n")

    for i, pcb in enumerate(changed_pcbs, 1):
        print(f"{i:2d}. {pcb}")

        # Show change statistics
        stats = get_file_change_summary(pcb)
        print(f"     Changes: {stats}")

        # Show related commits
        commits = show_file_changes(pcb)
        print(f"     Recent commits:")
        for commit in commits[:2]:  # Show only first 2 commits
            print(f"       - {commit}")

        # Check if file exists
        if not Path(pcb).exists():
            print(f"     ⚠️  WARNING: File does not exist!")

        print()

    # Find KiCad executable
    kicad_path = find_kicad_executable()
    if not kicad_path:
        return

    # Interactive selection
    print("Options:")
    print("  a - Open all PCB files")
    print("  s - Select specific files to open")
    print("  q - Quit without opening files")

    choice = input("\nWhat would you like to do? (a/s/q): ").lower()

    if choice == "q":
        print("Cancelled.")
        return

    files_to_open = []

    if choice == "a":
        files_to_open = changed_pcbs
    elif choice == "s":
        print("\nEnter the numbers of files to open (e.g., 1,3,5 or 1-3):")
        selection = input("Selection: ").strip()

        try:
            indices = []
            for part in selection.split(","):
                part = part.strip()
                if "-" in part:
                    start, end = map(int, part.split("-"))
                    indices.extend(range(start, end + 1))
                else:
                    indices.append(int(part))

            for idx in indices:
                if 1 <= idx <= len(changed_pcbs):
                    files_to_open.append(changed_pcbs[idx - 1])
                else:
                    print(f"Warning: Invalid selection {idx}")

        except ValueError:
            print("Invalid selection format. Please use numbers separated by commas.")
            return
    else:
        print("Invalid choice.")
        return

    if not files_to_open:
        print("No files selected.")
        return

    # Open selected PCB files
    print(f"\nOpening {len(files_to_open)} PCB files...")
    opened_count = 0

    for pcb_file in files_to_open:
        if open_pcb_file(kicad_path, pcb_file):
            opened_count += 1
            # Small delay between opening files
            time.sleep(1)

    print(
        f"\nSuccessfully opened {opened_count} out of {len(files_to_open)} PCB files."
    )
    print("\nReview checklist for each PCB:")
    print("  ✓ Component placement and orientation")
    print("  ✓ Routing and trace integrity")
    print("  ✓ Via placement and sizes")
    print("  ✓ Copper pour and ground planes")
    print("  ✓ Silkscreen and component references")
    print("  ✓ Design rule compliance")
    print("  ✓ Layer stackup consistency")
    print("  ✓ Manufacturing requirements")


if __name__ == "__main__":
    main()
