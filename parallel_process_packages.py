#!/usr/bin/env python3
"""
Script to process packages in parallel for faster execution
"""

import os
import re
import subprocess
import sys
import threading
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import Queue


def run_command(cmd, cwd=None, capture_output=True):
    """Run a command and return success status, stdout, stderr"""
    # Replace 'ato' with the full command (properly escaped)
    ATO_CMD = '"/Users/narayanpowderly/Library/Application Support/Cursor/User/globalStorage/atopile.atopile/uv-bin/uv" tool run -p 3.13 --from atopile ato'
    if cmd.startswith("ato "):
        cmd = cmd.replace("ato ", f"{ATO_CMD} ", 1)

    try:
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=cwd,
            capture_output=capture_output,
            text=True,
            timeout=600,  # 10 minute timeout for builds
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out"
    except Exception as e:
        return False, "", str(e)


def process_package(package_name):
    """Process a single package"""
    package_dir = Path(f"packages/{package_name}")

    if not package_dir.exists():
        return package_name, False, f"❌ Package directory not found: {package_dir}"

    # Check if ato.yaml exists
    ato_yaml = package_dir / "ato.yaml"
    if not ato_yaml.exists():
        return package_name, True, f"⚠️  No ato.yaml found in {package_name}, skipping"

    log_messages = []
    log_messages.append(f"🔄 Processing {package_name}...")

    # Step 1: Try frozen build first
    log_messages.append(f"  Running ato build --frozen...")
    success, stdout, stderr = run_command("ato build --frozen", cwd=package_dir)

    if not success:
        log_messages.append(f"  ❌ Frozen build failed, trying regular build first...")
        if stderr:
            log_messages.append(f"     Error: {stderr[:300]}...")

        # Step 2: Run regular build
        log_messages.append(f"  Running ato build...")
        success, stdout, stderr = run_command("ato build", cwd=package_dir)

        if not success:
            log_messages.append(f"  ❌ Regular build failed: {stderr[:300]}...")
            return package_name, False, "\n".join(log_messages)

        log_messages.append(f"  ✅ Regular build succeeded")

        # Step 3: Try frozen build again
        log_messages.append(f"  Running ato build --frozen again...")
        success, stdout, stderr = run_command("ato build --frozen", cwd=package_dir)

        if not success:
            log_messages.append(f"  ❌ Frozen build still failed: {stderr[:300]}...")
            return package_name, False, "\n".join(log_messages)

    log_messages.append(f"  ✅ Frozen build succeeded")

    # Step 4: Run package verify
    log_messages.append(f"  Running ato package verify -s...")
    success, stdout, stderr = run_command("ato package verify -s", cwd=package_dir)

    if not success:
        log_messages.append(f"  ❌ Package verify failed: {stderr[:300]}...")
        return package_name, False, "\n".join(log_messages)

    log_messages.append(f"  ✅ Package verify succeeded")

    # Step 5: Check for changes and commit if any
    success, stdout, stderr = run_command("git status --porcelain", cwd=package_dir)
    if stdout.strip():
        log_messages.append(f"  📝 Changes detected, committing...")
        run_command("git add .", cwd=package_dir)
        commit_msg = f"{package_name}: Automated build and verify updates"
        success, stdout, stderr = run_command(
            f'git commit -m "{commit_msg}"', cwd=package_dir
        )
        if success:
            log_messages.append(f"  ✅ Changes committed")
        else:
            log_messages.append(f"  ❌ Failed to commit: {stderr[:200]}...")
    else:
        log_messages.append(f"  ℹ️  No changes to commit")

    return package_name, True, "\n".join(log_messages)


def print_progress(completed, total, successful, failed):
    """Print progress update"""
    print(
        f"\r📊 Progress: {completed}/{total} | ✅ {successful} | ❌ {failed}",
        end="",
        flush=True,
    )


def extract_packages_from_todos():
    """Extract all package names from package-todos.md"""
    todos_file = Path("packages/package-todos.md")
    if not todos_file.exists():
        print("package-todos.md not found!")
        return []

    packages = []
    with open(todos_file, "r") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()

            # Skip empty lines, comments, or process description lines
            if (
                not line
                or line.startswith("#")
                or "Pipeline:" in line
                or "Process" in line
                or line.startswith("0.")
                or line.startswith("1.")
            ):
                continue

            # Only process lines that look like package entries (have ' - ' in them)
            if " - " in line:
                # Extract package name (everything before the first ' - ')
                package_name = line.split(" - ")[0].strip()
                # Only include valid package names (letters, numbers, hyphens)
                if re.match(r"^[a-zA-Z0-9\-_]+$", package_name):
                    # Skip non-package entries
                    if package_name not in [
                        "logos",
                        "mounting_holes",
                        "netties",
                        "review",
                    ]:
                        packages.append(package_name)

    return packages


def main():
    """Main function"""
    print("🚀 Starting parallel package processing...")

    # Change to the packages directory
    os.chdir("/Users/narayanpowderly/projects/packages")

    # Extract ALL packages from the todo list
    packages_to_process = extract_packages_from_todos()

    print(
        f"Processing {len(packages_to_process)} packages with {min(8, len(packages_to_process))} parallel workers"
    )

    successful = 0
    failed = 0
    completed = 0
    results = {}

    # Use ThreadPoolExecutor for parallel processing
    with ThreadPoolExecutor(max_workers=8) as executor:
        # Submit all tasks
        future_to_package = {
            executor.submit(process_package, pkg): pkg for pkg in packages_to_process
        }

        # Process completed tasks as they finish
        for future in as_completed(future_to_package):
            package_name = future_to_package[future]
            try:
                pkg_name, success, log_message = future.result()
                completed += 1

                if success:
                    successful += 1
                    results[pkg_name] = ("SUCCESS", log_message)
                else:
                    failed += 1
                    results[pkg_name] = ("FAILED", log_message)

                # Print progress
                print_progress(completed, len(packages_to_process), successful, failed)

            except Exception as e:
                completed += 1
                failed += 1
                results[package_name] = ("ERROR", f"Exception: {e}")
                print_progress(completed, len(packages_to_process), successful, failed)

    print("\n")  # New line after progress

    # Print detailed results
    print("\n" + "=" * 80)
    print("📋 DETAILED RESULTS")
    print("=" * 80)

    for package in packages_to_process:
        if package in results:
            status, log_message = results[package]
            if status == "SUCCESS":
                print(f"✅ {package}")
                # Only show first and last few lines for successful packages
                lines = log_message.split("\n")
                if len(lines) > 6:
                    print(f"   {lines[0]}")
                    print(f"   {lines[-1]}")
                else:
                    for line in lines:
                        print(f"   {line}")
            else:
                print(f"❌ {package}")
                # Show full log for failed packages
                for line in log_message.split("\n"):
                    print(f"   {line}")
            print()

    print("=" * 80)
    print(f"📊 FINAL SUMMARY:")
    print(f"  ✅ Successful: {successful}")
    print(f"  ❌ Failed: {failed}")
    print(f"  📦 Total: {len(packages_to_process)}")
    print("=" * 80)


if __name__ == "__main__":
    main()
