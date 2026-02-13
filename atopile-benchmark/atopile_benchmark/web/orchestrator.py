"""Benchmark orchestration for coordinating benchmark execution.

This module provides the BenchmarkOrchestrator class that manages
configuration, benchmark execution, and state tracking.
"""

import asyncio
import json
import logging
import time
from pathlib import Path
from typing import Any

import yaml

from ..core.benchmark_runner import BenchmarkRunner, BenchmarkResult
from ..core.data_store import DataStore
from ..core.sync_checker import SyncChecker
from ..core.version_manager import VersionManager
from .websocket import ConnectionManager

logger = logging.getLogger(__name__)


class BenchmarkOrchestrator:
    """Orchestrates benchmark execution and state management.

    This class is responsible for:
    - Loading and managing configuration
    - Coordinating benchmark runs
    - Tracking running benchmarks
    - Broadcasting updates via WebSocket
    """

    def __init__(
        self,
        config_file: Path,
        data_store: DataStore,
        version_manager: VersionManager,
        workspace_dir: Path,
        connection_manager: ConnectionManager,
    ):
        self.config_file = config_file
        self.data_store = data_store
        self.version_manager = version_manager
        self.workspace_dir = workspace_dir
        self.connection_manager = connection_manager

        self.config = self._load_config()
        self.runner = BenchmarkRunner(version_manager, workspace_dir)

        # Sync checker for comparing registry vs repo packages
        # config_file is at <repo>/atopile-benchmark/config/benchmarks.yaml
        # so repo root is 3 levels up
        packages_repo_path = config_file.parent.parent.parent
        self.sync_checker = SyncChecker(
            packages_repo_path=packages_repo_path,
            cache_dir=workspace_dir.parent,
            version_manager=version_manager,
        )

        # Track running benchmarks: {run_key: {status, start_time, phase, ...}}
        self.running_benchmarks: dict[str, dict[str, Any]] = {}

        # Cache for discovered build targets: {full_package_name: [targets]}
        self._targets_cache: dict[str, list[str]] = {}
        # Store targets cache next to the data file (data/ directory)
        self._targets_cache_file = self.data_store.data_file.parent / "targets_cache.json"

        # Load persisted targets cache from disk, then supplement from results
        self._load_targets_cache()
        self._populate_targets_from_results()

        # Cancellation support
        self._cancel_requested = False
        self._running_tasks: list[asyncio.Task] = []

    def _populate_targets_from_results(self):
        """Pre-populate targets cache by scanning stored benchmark results.

        Parses benchmark names (both 2-part and 3-part format) to discover
        which build targets have been run for each package.
        """
        packages = self.get_enabled_packages()
        pkg_name_to_full = {pkg["name"]: pkg["package"] for pkg in packages}

        # Collect targets per package from stored results
        pkg_targets: dict[str, set[str]] = {}

        for result in self.data_store.get_all_results():
            bn = result.get("benchmark_name", "")
            parts = bn.split(":")
            if len(parts) == 2:
                # Old 2-part format: pkgName:target
                pkg_name, target = parts
            elif len(parts) == 3:
                # New 3-part format: pkgName:buildCmd:target
                pkg_name, _, target = parts
            else:
                continue

            if pkg_name in pkg_name_to_full:
                if pkg_name not in pkg_targets:
                    pkg_targets[pkg_name] = set()
                pkg_targets[pkg_name].add(target)

        # Populate cache using full package names
        added = 0
        for pkg_name, targets in pkg_targets.items():
            full_pkg = pkg_name_to_full[pkg_name]
            if full_pkg not in self._targets_cache:
                self._targets_cache[full_pkg] = sorted(targets)
                added += 1
                logger.info(
                    f"Discovered {len(targets)} targets for {pkg_name} from results: {sorted(targets)}"
                )

        if added > 0:
            self._save_targets_cache()

    def _load_targets_cache(self):
        """Load persisted targets cache from disk."""
        if self._targets_cache_file.exists():
            try:
                with open(self._targets_cache_file, "r") as f:
                    data = json.load(f)
                self._targets_cache = data
                logger.info(f"Loaded targets cache with {len(data)} entries from disk")
            except Exception as e:
                logger.warning(f"Failed to load targets cache: {e}")

    def _save_targets_cache(self):
        """Persist the targets cache to disk."""
        try:
            self._targets_cache_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self._targets_cache_file, "w") as f:
                json.dump(self._targets_cache, f, indent=2)
            logger.debug(f"Saved targets cache with {len(self._targets_cache)} entries")
        except Exception as e:
            logger.warning(f"Failed to save targets cache: {e}")

    def _load_config(self) -> dict[str, Any]:
        """Load benchmark configuration from YAML file."""
        with open(self.config_file, "r") as f:
            return yaml.safe_load(f)

    def reload_config(self):
        """Reload configuration from file."""
        self.config = self._load_config()
        logger.info("Configuration reloaded")

    def _make_version_id(self, version_spec: dict) -> str:
        """Create a unique identifier for a version spec."""
        return f"{version_spec['type']}:{version_spec['version']}"

    def _make_run_key(self, benchmark_name: str, version_spec: dict) -> str:
        """Create a unique key for a running benchmark."""
        version_id = self._make_version_id(version_spec)
        return f"{benchmark_name}@{version_id}"

    def get_enabled_packages(self) -> list[dict]:
        """Get list of enabled package benchmarks."""
        return [
            p
            for p in self.config.get("package_benchmarks", [])
            if p.get("enabled", True)
        ]

    def get_versions(self) -> list[dict]:
        """Get list of atopile versions to test."""
        return self.config.get("atopile_versions", [])

    def get_build_commands(self) -> list[dict]:
        """Get list of build commands to test."""
        return self.config.get("build_commands", [])

    def get_examples_for_version(self, version_spec: dict) -> list[dict]:
        """Get example projects available for a specific atopile version.

        Args:
            version_spec: Version specification dict

        Returns:
            List of example info dicts with 'name' and 'path' keys
        """
        return self.version_manager.get_examples(version_spec)

    def get_all_examples(self) -> dict[str, list[str]]:
        """Get all available examples across all versions.

        Returns:
            Dict mapping version_id to list of example names
        """
        result = {}
        for version_spec in self.get_versions():
            version_id = self._make_version_id(version_spec)
            examples = self.get_examples_for_version(version_spec)
            result[version_id] = [ex["name"] for ex in examples]
        return result

    def get_common_examples(self) -> list[str]:
        """Get examples that are available in ALL configured versions.

        Returns:
            List of example names common to all versions
        """
        versions = self.get_versions()
        if not versions:
            return []

        # Get examples for each version
        example_sets = []
        for version_spec in versions:
            examples = self.get_examples_for_version(version_spec)
            example_names = {ex["name"] for ex in examples}
            example_sets.append(example_names)

        # Find intersection
        if not example_sets:
            return []

        common = example_sets[0]
        for example_set in example_sets[1:]:
            common = common.intersection(example_set)

        return sorted(common)

    def get_all_unique_examples(self) -> list[str]:
        """Get all unique examples across all configured versions.

        Returns:
            List of all unique example names (union of all versions)
        """
        all_examples = set()
        for version_spec in self.get_versions():
            examples = self.get_examples_for_version(version_spec)
            for ex in examples:
                all_examples.add(ex["name"])

        return sorted(all_examples)

    def get_package_targets(self, package_name: str, force_refresh: bool = False) -> list[str]:
        """Get build targets for a package.

        This downloads the package if needed and parses the ato.yaml to get targets.
        Results are cached for future calls.

        Args:
            package_name: Package name (e.g., "indicator-leds")
            force_refresh: If True, re-download and parse even if cached

        Returns:
            List of build target names
        """
        # Look up the package config to get the full package identifier
        package_config = None
        for pkg in self.get_enabled_packages():
            if pkg["name"] == package_name:
                package_config = pkg
                break

        if not package_config:
            logger.warning(f"Package {package_name} not found in config")
            return ["default"]

        full_package_name = package_config["package"]

        # Check cache
        if not force_refresh and full_package_name in self._targets_cache:
            return self._targets_cache[full_package_name]

        # We need to download the package to discover targets.
        # Use the first available version to download.
        versions = self.get_versions()
        if not versions:
            logger.warning("No versions configured, cannot discover targets")
            return ["default"]

        version_spec = versions[0]

        # Create a temporary workspace to download the package
        import shutil
        import time as time_module

        # Use a unique ID for the workspace
        workspace_id = f"targets_discover_{package_name}_{int(time_module.time())}"

        try:
            # Set up workspace to download the package
            workspace, package_added, _, _ = self.runner._setup_workspace(
                full_package_name,
                version_spec,
                workspace_id,
            )

            if not package_added:
                logger.warning(f"Could not download package {full_package_name}")
                self._targets_cache[full_package_name] = ["default"]
                return ["default"]

            # Get targets from the workspace
            targets = self.runner.get_package_build_targets(workspace)

            # Cache the result and persist
            self._targets_cache[full_package_name] = targets
            self._save_targets_cache()
            logger.info(f"Discovered {len(targets)} targets for {package_name}: {targets}")

            return targets

        except Exception as e:
            logger.error(f"Failed to discover targets for {package_name}: {e}")
            return ["default"]

        finally:
            # Clean up temp workspace
            workspace_path = self.workspace_dir / workspace_id
            if workspace_path.exists():
                shutil.rmtree(workspace_path, ignore_errors=True)

    def get_all_package_targets(self) -> dict[str, list[str]]:
        """Get all discovered targets for all packages.

        Returns:
            Dict mapping package names to their build targets
        """
        result = {}
        for pkg in self.get_enabled_packages():
            pkg_name = pkg["name"]
            full_pkg = pkg["package"]
            if full_pkg in self._targets_cache:
                result[pkg_name] = self._targets_cache[full_pkg]
            else:
                result[pkg_name] = ["default"]
        return result

    async def _broadcast_update(self, message: dict[str, Any]):
        """Broadcast an update to all connected clients."""
        await self.connection_manager.broadcast(message)

    async def run_single_benchmark(
        self,
        benchmark_name: str,
        package_config: dict,
        version_spec: dict,
        build_cmd_config: dict,
        build_target: str | None = None,
    ) -> BenchmarkResult:
        """Run a single benchmark and broadcast updates.

        Args:
            benchmark_name: Unique benchmark identifier (e.g., "package:command:target")
            package_config: Package configuration from YAML
            version_spec: atopile version specification
            build_cmd_config: Build command configuration
            build_target: Optional specific target to build (e.g., "red").

        Returns:
            BenchmarkResult with the benchmark outcome
        """
        run_key = self._make_run_key(benchmark_name, version_spec)
        version_id = self._make_version_id(version_spec)

        # Mark benchmark as running
        self.running_benchmarks[run_key] = {
            "status": "running",
            "start_time": time.time(),
            "phase": "initializing",
            "benchmark_name": benchmark_name,
            "version_id": version_id,
            "build_target": build_target,
        }

        await self._broadcast_update(
            {
                "type": "benchmark_started",
                "benchmark": benchmark_name,
                "version": version_spec,
                "version_id": version_id,
                "run_key": run_key,
                "build_target": build_target,
            }
        )

        # Create a phase callback that will broadcast updates
        # We need to use call_soon_threadsafe since the callback runs in executor thread
        loop = asyncio.get_event_loop()

        def phase_callback(phase_name: str):
            """Called when build enters a new phase."""
            # Update the running benchmark's phase
            if run_key in self.running_benchmarks:
                self.running_benchmarks[run_key]["phase"] = phase_name

            # Schedule the async broadcast from the executor thread
            async def broadcast_phase():
                await self._broadcast_update(
                    {
                        "type": "benchmark_progress",
                        "benchmark": benchmark_name,
                        "version_id": version_id,
                        "run_key": run_key,
                        "phase": phase_name,
                    }
                )

            loop.call_soon_threadsafe(lambda: asyncio.create_task(broadcast_phase()))

        # Run benchmark in executor to avoid blocking
        try:
            result = await loop.run_in_executor(
                None,
                lambda: self.runner.run_benchmark(
                    benchmark_name,
                    package_config["package"],
                    version_spec,
                    build_cmd_config["command"],
                    build_target=build_target,
                    phase_callback=phase_callback,
                ),
            )
        except Exception as e:
            logger.error(f"Benchmark execution failed: {e}")
            result = BenchmarkResult(
                benchmark_name=benchmark_name,
                version_spec=version_spec,
                build_command=build_cmd_config["command"],
                status="failure",
                error_message=str(e),
            )

        # Save result
        self.data_store.add_result(result)

        # Remove from running
        self.running_benchmarks.pop(run_key, None)

        # Broadcast completion
        await self._broadcast_update(
            {
                "type": "benchmark_completed",
                "benchmark": benchmark_name,
                "version": version_spec,
                "version_id": version_id,
                "run_key": run_key,
                "build_target": build_target,
                "result": {
                    "status": result.status,
                    "total_time": result.total_time,
                    "error_message": result.error_message,
                    "build_target": result.build_target,
                    "phases": [
                        {"name": p.name, "duration": p.duration} for p in result.phases
                    ],
                },
            }
        )

        return result

    def _has_passing_result(self, benchmark_name: str, version_spec: dict) -> bool:
        """Check if a benchmark already has a passing result for a version.

        Args:
            benchmark_name: Name of the benchmark
            version_spec: Version specification dict

        Returns:
            True if there's already a successful result for this benchmark/version
        """
        matrix = self.data_store.get_results_matrix()
        version_id = self._make_version_id(version_spec)

        if benchmark_name in matrix:
            result = matrix[benchmark_name].get(version_id)
            if result and result.get("status") == "success":
                return True
        return False

    async def run_all_benchmarks(
        self,
        max_parallel: int = 4,
        force: bool = False,
        enabled_commands: list[str] | None = None,
        include_examples: bool = True,
    ):
        """Run all configured benchmarks for all versions.

        Args:
            max_parallel: Maximum number of benchmarks to build in parallel (0 = unlimited)
            force: If True, rerun all benchmarks even if they already passed
            enabled_commands: List of build command names to run. If None, run all.
            include_examples: If True, also run benchmarks for example projects

        Skips benchmarks that already have a passing result (unless force=True).
        Individual benchmarks are run in parallel (across all versions and packages),
        with up to max_parallel concurrent benchmark tasks.
        Versions are installed in parallel first.
        """
        # Reset cancellation flag from any previous stop_all call
        self._cancel_requested = False

        versions = self.get_versions()
        packages = self.get_enabled_packages()
        build_commands = self.get_build_commands()

        # Filter build commands if enabled_commands is specified
        if enabled_commands is not None:
            build_commands = [
                cmd for cmd in build_commands if cmd["name"] in enabled_commands
            ]
            logger.info(
                f"Filtering to {len(build_commands)} build commands: {enabled_commands}"
            )

        # Install all versions first (in parallel)
        install_tasks = []
        install_version_specs = []
        for version_spec in versions:
            if not self.version_manager.is_installed(version_spec):
                logger.info(
                    f"Queueing installation of {self._make_version_id(version_spec)}"
                )
                install_tasks.append(
                    asyncio.get_event_loop().run_in_executor(
                        None,
                        self.version_manager.install_version,
                        version_spec,
                    )
                )
                install_version_specs.append(version_spec)

        if install_tasks:
            logger.info(f"Installing {len(install_tasks)} versions...")
            install_results = await asyncio.gather(*install_tasks, return_exceptions=True)
            from datetime import datetime
            from ..utils.config import save_config
            for i, result in enumerate(install_results):
                if isinstance(result, Exception):
                    logger.error(f"Version installation failed: {result}")
                else:
                    # Persist env_created_at for successfully installed versions
                    install_version_specs[i]["env_created_at"] = (
                        datetime.now().isoformat(timespec="seconds")
                    )
            save_config(self.config_file, self.config)

        # Discover build targets for all packages (after versions are installed)
        for package_config in packages:
            full_pkg = package_config["package"]
            if full_pkg not in self._targets_cache:
                try:
                    self.get_package_targets(package_config["name"])
                except Exception as e:
                    logger.warning(
                        f"Failed to discover targets for {package_config['name']}: {e}"
                    )

        # Count how many benchmarks we'll actually run (excluding already passed)
        skipped = 0
        to_run = []

        for version_spec in versions:
            version_id = self._make_version_id(version_spec)
            for package_config in packages:
                for build_cmd_config in build_commands:
                    # Always expand targets for each package
                    targets = self._targets_cache.get(
                        package_config["package"], ["default"]
                    )

                    for target in targets:
                        benchmark_name = (
                            f"{package_config['name']}:{build_cmd_config['name']}:{target}"
                        )
                        if not force and self._has_passing_result(
                            benchmark_name, version_spec
                        ):
                            skipped += 1
                            logger.debug(
                                f"Skipping {benchmark_name}@{version_id} (already passed)"
                            )
                        else:
                            to_run.append(
                                (
                                    benchmark_name,
                                    package_config,
                                    version_spec,
                                    build_cmd_config,
                                    target,
                                )
                            )

        # Add example benchmarks if requested
        if include_examples:
            # Default build command for examples
            example_build_cmd = {"name": "default", "command": "ato build"}

            for version_spec in versions:
                version_id = self._make_version_id(version_spec)

                # Get examples available for this version
                examples = self.get_examples_for_version(version_spec)

                for example_info in examples:
                    example_name = example_info["name"]
                    benchmark_name = f"examples/{example_name}:default"

                    # Create a pseudo package config for the example
                    example_config = {
                        "name": f"examples/{example_name}",
                        "package": f"examples/{example_name}",
                    }

                    if not force and self._has_passing_result(benchmark_name, version_spec):
                        skipped += 1
                        logger.debug(
                            f"Skipping {benchmark_name}@{version_id} (already passed)"
                        )
                    else:
                        to_run.append(
                            (
                                benchmark_name,
                                example_config,
                                version_spec,
                                example_build_cmd,
                                None,  # No specific target for examples
                            )
                        )

            logger.info(f"Included {len([t for t in to_run if t[0].startswith('examples/')])} example benchmarks")

        mode = "force rerun" if force else "run"
        parallel_str = (
            f"max {max_parallel} parallel" if max_parallel > 0 else "unlimited parallel"
        )
        logger.info(
            f"Will {mode} {len(to_run)} benchmarks across {len(versions)} versions "
            f"({parallel_str}, skipping {skipped} already passed)"
        )

        if not to_run:
            logger.info("All benchmarks already passed, nothing to run")
            await self._broadcast_update({"type": "all_benchmarks_completed"})
            return

        # Run individual benchmarks in parallel, controlled by semaphore.
        # Each benchmark gets its own task so that e.g. 16 different packages
        # can build concurrently even when there are only 2 atopile versions.
        semaphore = asyncio.Semaphore(max_parallel) if max_parallel > 0 else None

        async def run_single_with_limit(
            benchmark_name: str,
            package_config: dict,
            version_spec: dict,
            build_cmd_config: dict,
            build_target: str | None,
        ):
            """Run a single benchmark, optionally gated by the semaphore."""
            version_id = self._make_version_id(version_spec)

            if self._cancel_requested:
                logger.info(
                    f"Skipping {benchmark_name}@{version_id} due to cancellation"
                )
                return

            async def _execute():
                try:
                    await self.run_single_benchmark(
                        benchmark_name,
                        package_config,
                        version_spec,
                        build_cmd_config,
                        build_target=build_target,
                    )
                except asyncio.CancelledError:
                    logger.info(f"Benchmark {benchmark_name}@{version_id} cancelled")
                except Exception as e:
                    logger.error(f"Benchmark {benchmark_name}@{version_id} failed: {e}")

            if semaphore:
                async with semaphore:
                    await _execute()
            else:
                await _execute()

        # Create one task per benchmark
        benchmark_tasks = [
            run_single_with_limit(
                benchmark_name, package_config, version_spec,
                build_cmd_config, build_target,
            )
            for benchmark_name, package_config, version_spec, build_cmd_config, build_target in to_run
        ]

        # Store tasks for cancellation
        self._running_tasks = [asyncio.create_task(coro) for coro in benchmark_tasks]

        try:
            await asyncio.gather(*self._running_tasks, return_exceptions=True)
        except asyncio.CancelledError:
            logger.info("Benchmark run was cancelled")
        finally:
            self._running_tasks = []

        if self._cancel_requested:
            self._cancel_requested = False
            await self._broadcast_update({"type": "benchmarks_stopped"})
            logger.info("Benchmarks stopped by user")
        else:
            await self._broadcast_update({"type": "all_benchmarks_completed"})
            logger.info("All benchmarks completed")

    async def stop_all_benchmarks(self):
        """Stop all running benchmarks and cancel pending ones."""
        self._cancel_requested = True
        logger.info("Stopping all benchmarks...")

        # Cancel all running tasks
        for task in self._running_tasks:
            if not task.done():
                task.cancel()

        # Clear running benchmarks tracking
        stopped_count = len(self.running_benchmarks)
        for run_key in list(self.running_benchmarks.keys()):
            await self._broadcast_update(
                {
                    "type": "benchmark_stopped",
                    "run_key": run_key,
                }
            )
        self.running_benchmarks.clear()

        # Kill any running ato processes
        try:
            import subprocess

            subprocess.run(
                ["pkill", "-f", "ato.*build"], capture_output=True, timeout=5
            )
        except Exception as e:
            logger.debug(f"Failed to kill ato processes: {e}")

        logger.info(f"Stopped {stopped_count} benchmarks")
        return stopped_count

    def is_running(self) -> bool:
        """Check if any benchmarks are currently running."""
        return len(self.running_benchmarks) > 0 or len(self._running_tasks) > 0
