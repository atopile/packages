#!/usr/bin/env python3
"""Test script to verify the benchmarking infrastructure."""

import logging
from pathlib import Path
import sys

from atopile_benchmark.version_manager import VersionManager
from atopile_benchmark.benchmark_runner import BenchmarkRunner
from atopile_benchmark.data_store import DataStore

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_version_manager():
    """Test the version manager."""
    logger.info("Testing version manager...")

    cache_dir = Path("test_cache")
    vm = VersionManager(cache_dir)

    # Test with a recent release
    version_spec = {
        "type": "release",
        "version": "0.2.62",  # Use a known working version
        "date": "2024-01-01",
    }

    logger.info(f"Checking if {version_spec['version']} is installed...")
    if vm.is_installed(version_spec):
        logger.info("  Already installed")
    else:
        logger.info("  Installing...")
        try:
            venv_path = vm.install_version(version_spec)
            logger.info(f"  Installed at {venv_path}")
        except Exception as e:
            logger.error(f"  Installation failed: {e}")
            return False

    # Get version info
    info = vm.get_version_info(version_spec)
    logger.info(f"  Version info: {info}")

    return True


def test_benchmark_runner():
    """Test running a simple benchmark."""
    logger.info("\nTesting benchmark runner...")

    cache_dir = Path("test_cache")
    workspace_dir = Path("test_cache/workspaces")

    vm = VersionManager(cache_dir)
    runner = BenchmarkRunner(vm, workspace_dir, verbose=True)

    version_spec = {"type": "release", "version": "0.2.62", "date": "2024-01-01"}

    # Ensure version is installed
    if not vm.is_installed(version_spec):
        logger.info("Installing atopile version...")
        try:
            vm.install_version(version_spec)
        except Exception as e:
            logger.error(f"Failed to install: {e}")
            return False

    # Run a simple benchmark
    logger.info("Running benchmark...")
    try:
        result = runner.run_benchmark(
            benchmark_name="test:default",
            package_name="atopile/generics",  # Use a simple, stable package
            version_spec=version_spec,
            build_command="ato build",
        )

        logger.info(f"  Status: {result.status}")
        logger.info(f"  Total time: {result.total_time}s")
        if result.error_message:
            logger.error(f"  Error: {result.error_message}")

        return result.status == "success"

    except Exception as e:
        logger.error(f"Benchmark failed: {e}", exc_info=True)
        return False


def test_data_store():
    """Test the data store."""
    logger.info("\nTesting data store...")

    data_file = Path("test_results.json")
    if data_file.exists():
        data_file.unlink()

    ds = DataStore(data_file)

    # Create a mock result
    from atopile_benchmark.benchmark_runner import BenchmarkResult

    result = BenchmarkResult(
        benchmark_name="test:default",
        version_spec={"type": "release", "version": "0.2.62"},
        build_command="ato build",
        status="success",
        total_time=5.5,
    )

    ds.add_result(result)
    logger.info("  Added test result")

    # Retrieve results
    all_results = ds.get_all_results()
    logger.info(f"  Retrieved {len(all_results)} results")

    matrix = ds.get_results_matrix()
    logger.info(f"  Matrix has {len(matrix)} benchmarks")

    return len(all_results) == 1


def main():
    """Run all tests."""
    print("=" * 60)
    print("atopile Benchmark Infrastructure Test")
    print("=" * 60)

    tests = [
        ("Version Manager", test_version_manager),
        ("Data Store", test_data_store),
        # ("Benchmark Runner", test_benchmark_runner),  # Skip for now - requires actual atopile
    ]

    results = {}
    for name, test_func in tests:
        try:
            results[name] = test_func()
        except Exception as e:
            logger.error(f"{name} failed with exception: {e}", exc_info=True)
            results[name] = False

    print("\n" + "=" * 60)
    print("Test Results:")
    print("=" * 60)
    for name, passed in results.items():
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"  {name}: {status}")

    all_passed = all(results.values())
    print("=" * 60)
    if all_passed:
        print("All tests passed!")
        return 0
    else:
        print("Some tests failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
