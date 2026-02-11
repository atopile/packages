"""Benchmark execution routes.

This module provides API routes for running and managing benchmarks.
"""

import asyncio
import logging
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["benchmarks"])


def setup_routes(orchestrator: Any) -> APIRouter:
    """Configure routes with the orchestrator instance.

    Args:
        orchestrator: BenchmarkOrchestrator instance

    Returns:
        Configured router
    """

    @router.get("/running")
    async def get_running():
        """Get currently running benchmarks."""
        return JSONResponse(orchestrator.running_benchmarks)

    @router.post("/run/all")
    async def run_all(
        max_parallel: int = 4,
        force: bool = False,
        commands: str | None = None,
        include_examples: bool = True,
    ):
        """Start all benchmarks.

        Args:
            max_parallel: Maximum number of benchmarks to build in parallel (0 = unlimited)
            force: If True, rerun all benchmarks even if they already passed
            commands: Comma-separated list of build command names to run
            include_examples: If True, also run example project benchmarks
        """
        if orchestrator.running_benchmarks:
            return JSONResponse(
                {"status": "error", "message": "Benchmarks already running"},
                status_code=409,
            )

        # Parse enabled commands
        enabled_commands = None
        if commands:
            enabled_commands = [c.strip() for c in commands.split(",") if c.strip()]

        asyncio.create_task(
            orchestrator.run_all_benchmarks(
                max_parallel=max_parallel,
                force=force,
                enabled_commands=enabled_commands,
                include_examples=include_examples,
            )
        )
        return JSONResponse(
            {
                "status": "started",
                "max_parallel": max_parallel,
                "force": force,
                "commands": enabled_commands,
                "include_examples": include_examples,
            }
        )

    @router.post("/run/stop")
    async def stop_all():
        """Stop all running benchmarks and cancel pending ones."""
        if not orchestrator.is_running():
            return JSONResponse(
                {"status": "ok", "message": "No benchmarks running"},
            )
        stopped_count = await orchestrator.stop_all_benchmarks()
        return JSONResponse({"status": "stopped", "stopped_count": stopped_count})

    @router.post("/run/benchmark/{benchmark_name:path}/version/{version_id:path}")
    async def run_single(benchmark_name: str, version_id: str):
        """Start a single benchmark for a specific version.

        Args:
            benchmark_name: Benchmark name. Formats:
                - "package:command" - builds default target
                - "package:command:target" - builds specific target
                - "examples/<name>:default" - builds an example project
            version_id: Version identifier (e.g., "release:0.12.4")
        """
        # Parse version_id
        if ":" not in version_id:
            raise HTTPException(status_code=400, detail="Invalid version_id format")

        version_type, version = version_id.split(":", 1)

        # Find version spec
        version_spec = None
        for spec in orchestrator.get_versions():
            if spec["type"] == version_type and spec["version"] == version:
                version_spec = spec
                break

        if not version_spec:
            raise HTTPException(status_code=404, detail="Version not found")

        # Parse benchmark name - can be "package:command", "package:command:target", or "examples/<name>:default"
        parts = benchmark_name.split(":")
        if len(parts) < 2:
            raise HTTPException(status_code=400, detail="Invalid benchmark_name format")

        package_name = parts[0]
        build_cmd_name = parts[1]
        build_target = parts[2] if len(parts) > 2 else None

        # Check if this is an example benchmark
        is_example = package_name.startswith("examples/")

        if is_example:
            # Create pseudo package config for example
            package_config = {
                "name": package_name,
                "package": package_name,
            }
            build_cmd_config = {"name": "default", "command": "ato build"}
        else:
            # Find package config
            package_config = None
            for pkg in orchestrator.get_enabled_packages():
                if pkg["name"] == package_name:
                    package_config = pkg
                    break

            if not package_config:
                raise HTTPException(status_code=404, detail="Package not found")

            # Find build command config
            build_cmd_config = None
            for cmd in orchestrator.get_build_commands():
                if cmd["name"] == build_cmd_name:
                    build_cmd_config = cmd
                    break

            if not build_cmd_config:
                raise HTTPException(status_code=404, detail="Build command not found")

        # Check if already running
        run_key = orchestrator._make_run_key(benchmark_name, version_spec)
        if run_key in orchestrator.running_benchmarks:
            return JSONResponse(
                {"status": "error", "message": "Benchmark already running"},
                status_code=409,
            )

        # Start benchmark
        asyncio.create_task(
            orchestrator.run_single_benchmark(
                benchmark_name,
                package_config,
                version_spec,
                build_cmd_config,
                build_target=build_target,
            )
        )

        return JSONResponse({"status": "started", "run_key": run_key})

    @router.get("/benchmarks")
    async def get_benchmarks():
        """Get list of all benchmark names."""
        return JSONResponse(orchestrator.data_store.get_benchmark_names())

    @router.get("/targets/{package_name}")
    async def get_package_targets(package_name: str, refresh: bool = False):
        """Get build targets for a package.

        This discovers the targets by downloading and parsing the package's ato.yaml.
        Results are cached for performance.

        Args:
            package_name: Package name (e.g., "indicator-leds")
            refresh: If True, re-download and parse even if cached
        """
        loop = asyncio.get_event_loop()
        targets = await loop.run_in_executor(
            None,
            lambda: orchestrator.get_package_targets(package_name, force_refresh=refresh)
        )
        return JSONResponse({"package": package_name, "targets": targets})

    @router.get("/targets")
    async def get_all_targets():
        """Get all discovered targets for all packages.

        Only returns targets that have been previously discovered.
        Use GET /api/targets/{package_name} to discover targets for a specific package.
        """
        return JSONResponse(orchestrator.get_all_package_targets())

    @router.post("/targets/discover")
    async def discover_all_targets():
        """Discover targets for all enabled packages.

        This can take a while as it downloads each package.
        """
        packages = orchestrator.get_enabled_packages()
        loop = asyncio.get_event_loop()
        results = {}

        for pkg in packages:
            try:
                targets = await loop.run_in_executor(
                    None,
                    lambda p=pkg["name"]: orchestrator.get_package_targets(p, force_refresh=True)
                )
                results[pkg["name"]] = targets
            except Exception as e:
                logger.error(f"Failed to discover targets for {pkg['name']}: {e}")
                results[pkg["name"]] = ["default"]

        return JSONResponse({"status": "completed", "targets": results})

    @router.get("/examples")
    async def get_all_examples():
        """Get all available examples across all versions.

        Returns a dict mapping version_id to list of example names.
        """
        return JSONResponse(orchestrator.get_all_examples())

    @router.get("/examples/common")
    async def get_common_examples():
        """Get examples that are available in ALL configured versions.

        These are the examples that can be benchmarked across all versions.
        """
        return JSONResponse(orchestrator.get_common_examples())

    @router.get("/examples/all")
    async def get_all_unique_examples():
        """Get all unique examples across all versions.

        Returns examples that exist in at least one version.
        """
        return JSONResponse(orchestrator.get_all_unique_examples())

    @router.post("/examples/ensure-sources")
    async def ensure_example_sources():
        """Ensure source code is cloned for all versions.

        This is needed to access examples for versions that were installed
        before source cloning was added.
        """
        results = {}
        loop = asyncio.get_event_loop()

        for version_spec in orchestrator.get_versions():
            version_id = f"{version_spec['type']}:{version_spec['version']}"
            try:
                success = await loop.run_in_executor(
                    None,
                    orchestrator.version_manager.ensure_source_cloned,
                    version_spec
                )
                results[version_id] = "ok" if success else "failed"
            except Exception as e:
                logger.error(f"Failed to ensure source for {version_id}: {e}")
                results[version_id] = f"error: {str(e)}"

        return JSONResponse({"status": "completed", "results": results})

    @router.get("/examples/{version_id:path}")
    async def get_examples_for_version(version_id: str):
        """Get examples available for a specific version.

        Args:
            version_id: Version identifier (e.g., "release:0.12.4")
        """
        if ":" not in version_id:
            raise HTTPException(status_code=400, detail="Invalid version_id format")

        version_type, version = version_id.split(":", 1)

        # Find version spec
        version_spec = None
        for spec in orchestrator.get_versions():
            if spec["type"] == version_type and spec["version"] == version:
                version_spec = spec
                break

        if not version_spec:
            raise HTTPException(status_code=404, detail="Version not found")

        examples = orchestrator.get_examples_for_version(version_spec)
        return JSONResponse({
            "version_id": version_id,
            "examples": [ex["name"] for ex in examples],
            "details": examples,
        })

    @router.post("/run/example/{example_name}/version/{version_id:path}")
    async def run_example_benchmark(example_name: str, version_id: str):
        """Start a benchmark for an example project.

        Args:
            example_name: Example name (e.g., "blinky")
            version_id: Version identifier (e.g., "release:0.12.4")
        """
        if ":" not in version_id:
            raise HTTPException(status_code=400, detail="Invalid version_id format")

        version_type, version = version_id.split(":", 1)

        # Find version spec
        version_spec = None
        for spec in orchestrator.get_versions():
            if spec["type"] == version_type and spec["version"] == version:
                version_spec = spec
                break

        if not version_spec:
            raise HTTPException(status_code=404, detail="Version not found")

        # Create example package config
        package_config = {
            "name": f"examples/{example_name}",
            "package": f"examples/{example_name}",
        }

        # Use default build command
        build_cmd_config = {"name": "default", "command": "ato build"}

        benchmark_name = f"examples/{example_name}:default"
        run_key = orchestrator._make_run_key(benchmark_name, version_spec)

        if run_key in orchestrator.running_benchmarks:
            return JSONResponse(
                {"status": "error", "message": "Benchmark already running"},
                status_code=409,
            )

        asyncio.create_task(
            orchestrator.run_single_benchmark(
                benchmark_name,
                package_config,
                version_spec,
                build_cmd_config,
            )
        )

        return JSONResponse({"status": "started", "run_key": run_key})

    return router
