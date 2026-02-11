#!/usr/bin/env python3
"""Show what's currently cached."""

import sys
from pathlib import Path
import json

from atopile_benchmark.version_manager import VersionManager
from atopile_benchmark.data_store import DataStore


def show_cache_info():
    """Display cache information."""
    cache_dir = Path("benchmark_cache")
    data_file = Path("benchmark_results.json")

    print("=" * 60)
    print("atopile Benchmark Cache Information")
    print("=" * 60)

    # Virtual environments
    vm = VersionManager(cache_dir)
    installed = vm.list_installed_versions()

    print(f"\n📦 Installed Versions ({len(installed)}):")
    if installed:
        for venv_name in sorted(installed):
            print(f"  - {venv_name}")

            # Get size
            venv_path = cache_dir / "venvs" / venv_name
            if venv_path.exists():
                # Quick size estimate (in MB)
                total_size = sum(
                    f.stat().st_size for f in venv_path.rglob("*") if f.is_file()
                )
                size_mb = total_size / (1024 * 1024)
                print(f"    Size: {size_mb:.1f} MB")
    else:
        print("  (none)")

    # Calculate total venv size
    venvs_dir = cache_dir / "venvs"
    if venvs_dir.exists():
        total_venv_size = sum(
            f.stat().st_size for f in venvs_dir.rglob("*") if f.is_file()
        )
        total_venv_mb = total_venv_size / (1024 * 1024)
        print(f"\n  Total venv cache: {total_venv_mb:.1f} MB")

    # Benchmark results
    if data_file.exists():
        ds = DataStore(data_file)
        all_results = ds.get_all_results()

        print(f"\n📊 Benchmark Results ({len(all_results)} total):")

        # Group by status
        by_status = {}
        for result in all_results:
            status = result.get("status", "unknown")
            by_status[status] = by_status.get(status, 0) + 1

        for status, count in sorted(by_status.items()):
            print(f"  - {status}: {count}")

        # Recent results
        print(f"\n🕐 Most Recent Results:")
        recent = sorted(
            all_results, key=lambda r: r.get("timestamp", ""), reverse=True
        )[:5]
        for result in recent:
            timestamp = result.get("timestamp", "unknown")[:19]  # Just the date/time
            benchmark = result.get("benchmark_name", "unknown")
            status = result.get("status", "unknown")
            total_time = result.get("total_time")
            time_str = f"{total_time:.2f}s" if total_time else "N/A"

            print(f"  - {timestamp} | {benchmark} | {status} | {time_str}")

        # Data file size
        data_size = data_file.stat().st_size / 1024
        print(f"\n  Results file size: {data_size:.1f} KB")
    else:
        print("\n📊 Benchmark Results: (no results yet)")

    print("\n" + "=" * 60)


def main():
    """Main entry point."""
    show_cache_info()
    return 0


if __name__ == "__main__":
    sys.exit(main())
