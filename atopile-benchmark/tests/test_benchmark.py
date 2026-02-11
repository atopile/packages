#!/usr/bin/env python3
"""Test a single benchmark end-to-end."""

import logging
from pathlib import Path

from atopile_benchmark import VersionManager, BenchmarkRunner

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def main():
    """Run a test benchmark."""
    # Use a recent working version that has the packages we need
    version_spec = {
        "type": "release",
        "version": "0.12.4",  # Latest version
        "date": "2024-11-15"
    }

    cache_dir = Path("test_benchmark_cache")
    workspace_dir = Path("test_benchmark_cache/workspaces")

    logger.info("Initializing version manager...")
    vm = VersionManager(cache_dir)

    logger.info(f"Installing atopile {version_spec['version']}...")
    if not vm.is_installed(version_spec):
        vm.install_version(version_spec)
    else:
        logger.info("  Already installed")

    logger.info("Initializing benchmark runner...")
    runner = BenchmarkRunner(vm, workspace_dir, verbose=True)

    logger.info("Running benchmark...")
    result = runner.run_benchmark(
        benchmark_name="test:default",
        package_name="atopile/indicator-leds",  # Use actual package from benchmarks
        version_spec=version_spec,
        build_command="ato build"
    )

    logger.info("=" * 60)
    logger.info("RESULT:")
    logger.info(f"  Status: {result.status}")
    logger.info(f"  Total Time: {result.total_time}s")
    logger.info(f"  Phases: {len(result.phases)}")
    for phase in result.phases:
        logger.info(f"    - {phase.name}: {phase.duration}s")

    if result.error_message:
        logger.error(f"  Error: {result.error_message}")

    logger.info("=" * 60)

    return 0 if result.status == "success" else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
