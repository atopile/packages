"""Web dashboard for visualizing benchmark results.

This module provides a FastAPI-based web dashboard for viewing and managing
atopile build benchmarks. It features:
- Real-time WebSocket updates
- REST API for benchmark management
- Interactive HTML dashboard with charts
"""

import asyncio
import logging
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request

from .benchmark_runner import BenchmarkRunner, BenchmarkResult
from .data_store import DataStore
from .version_manager import VersionManager

logger = logging.getLogger(__name__)


def _get_version_date(version_type: str, version_value: str) -> str:
    """Get the commit date for a version from git.

    For releases, fetches the tag date from the atopile repo.
    For branches, fetches the latest commit date.
    For commits, fetches the commit date.
    For local paths, uses today's date.
    """
    today = datetime.now().strftime("%Y-%m-%d")

    if version_type == "local":
        # For local paths, try to get the HEAD commit date
        local_path = Path(version_value).expanduser()
        if local_path.exists():
            try:
                result = subprocess.run(
                    ["git", "log", "-1", "--format=%ci"],
                    cwd=local_path,
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if result.returncode == 0 and result.stdout.strip():
                    # Parse "2024-01-15 10:30:00 -0800" format
                    date_str = result.stdout.strip().split()[0]
                    return date_str
            except Exception as e:
                logger.warning(
                    f"Failed to get git date for local path {local_path}: {e}"
                )
        return today

    # For remote versions (release, branch, commit), query the atopile GitHub repo
    try:
        if version_type == "release":
            # Get tag date
            result = subprocess.run(
                [
                    "git",
                    "ls-remote",
                    "--tags",
                    "https://github.com/atopile/atopile.git",
                    f"v{version_value}",
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0 and result.stdout.strip():
                # Tag exists, now get its date by cloning minimally
                # Use git log with the tag ref
                commit_hash = result.stdout.strip().split()[0]
                return _get_commit_date_from_hash(commit_hash)

        elif version_type == "branch":
            # Get latest commit on branch
            result = subprocess.run(
                [
                    "git",
                    "ls-remote",
                    "https://github.com/atopile/atopile.git",
                    f"refs/heads/{version_value}",
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0 and result.stdout.strip():
                commit_hash = result.stdout.strip().split()[0]
                return _get_commit_date_from_hash(commit_hash)

        elif version_type == "commit":
            return _get_commit_date_from_hash(version_value)

    except Exception as e:
        logger.warning(
            f"Failed to get git date for {version_type}:{version_value}: {e}"
        )

    return today


def _get_commit_date_from_hash(commit_hash: str) -> str:
    """Get the commit date for a specific hash from the atopile repo."""
    try:
        # Use GitHub API to get commit info (doesn't require clone)
        import urllib.request
        import json

        url = f"https://api.github.com/repos/atopile/atopile/commits/{commit_hash}"
        req = urllib.request.Request(url, headers={"User-Agent": "atopile-benchmark"})

        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            # Parse ISO date format
            date_str = data["commit"]["committer"]["date"][
                :10
            ]  # "2024-01-15T10:30:00Z" -> "2024-01-15"
            return date_str
    except Exception as e:
        logger.warning(f"Failed to get commit date for {commit_hash}: {e}")
        return datetime.now().strftime("%Y-%m-%d")


def _save_config(config_file: Path, config: dict) -> None:
    """Save configuration to YAML file, preserving comments where possible."""
    # Read the original file to preserve structure
    with open(config_file, "r") as f:
        original_content = f.read()

    # For simplicity, we'll rewrite the entire file with a clean structure
    # but preserve any comments at the top
    header_lines = []
    for line in original_content.split("\n"):
        if line.startswith("#") or line.strip() == "":
            header_lines.append(line)
        else:
            break

    header = "\n".join(header_lines)
    if header and not header.endswith("\n"):
        header += "\n"

    # Write the config
    with open(config_file, "w") as f:
        if header:
            f.write(header)
        yaml.dump(
            config, f, default_flow_style=False, sort_keys=False, allow_unicode=True
        )


class ConnectionManager:
    """Manages WebSocket connections for real-time updates."""

    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """Accept a new WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.debug(
            f"WebSocket connected. Total connections: {len(self.active_connections)}"
        )

    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.debug(
            f"WebSocket disconnected. Total connections: {len(self.active_connections)}"
        )

    async def broadcast(self, message: dict[str, Any]):
        """Broadcast a message to all connected clients."""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.debug(f"Failed to send to WebSocket: {e}")
                disconnected.append(connection)

        for connection in disconnected:
            self.disconnect(connection)


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
        self.runner = BenchmarkRunner(
            version_manager,
            workspace_dir,
            skip_ato_add=bool(self.config.get("skip_ato_add", False)),
            local_packages_root=self.config.get("local_packages_root"),
        )

        # Track running benchmarks: {run_key: {status, start_time, phase, ...}}
        self.running_benchmarks: dict[str, dict[str, Any]] = {}

        # Cancellation support
        self._cancel_requested = False
        self._running_tasks: list[asyncio.Task] = []

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

    async def _broadcast_update(self, message: dict[str, Any]):
        """Broadcast an update to all connected clients."""
        await self.connection_manager.broadcast(message)

    async def run_single_benchmark(
        self,
        benchmark_name: str,
        package_config: dict,
        version_spec: dict,
        build_cmd_config: dict,
    ) -> BenchmarkResult:
        """Run a single benchmark and broadcast updates.

        Args:
            benchmark_name: Unique benchmark identifier (e.g., "package:command")
            package_config: Package configuration from YAML
            version_spec: atopile version specification
            build_cmd_config: Build command configuration

        Returns:
            BenchmarkResult with the benchmark outcome
        """
        import time

        run_key = self._make_run_key(benchmark_name, version_spec)
        version_id = self._make_version_id(version_spec)

        # Mark benchmark as running
        self.running_benchmarks[run_key] = {
            "status": "running",
            "start_time": time.time(),
            "phase": "initializing",
            "benchmark_name": benchmark_name,
            "version_id": version_id,
        }

        await self._broadcast_update(
            {
                "type": "benchmark_started",
                "benchmark": benchmark_name,
                "version": version_spec,
                "version_id": version_id,
                "run_key": run_key,
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
                "result": {
                    "status": result.status,
                    "total_time": result.total_time,
                    "error_message": result.error_message,
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
    ):
        """Run all configured benchmarks for all versions.

        Args:
            max_parallel: Maximum number of versions to build in parallel (0 = unlimited)
            force: If True, rerun all benchmarks even if they already passed
            enabled_commands: List of build command names to run. If None, run all.

        Skips benchmarks that already have a passing result (unless force=True).
        Benchmarks are run in parallel, with up to max_parallel concurrent version tasks.
        Versions are installed in parallel first.
        """
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

        # Count how many benchmarks we'll actually run (excluding already passed)
        skipped = 0
        to_run = []

        for version_spec in versions:
            version_id = self._make_version_id(version_spec)
            for package_config in packages:
                for build_cmd_config in build_commands:
                    benchmark_name = (
                        f"{package_config['name']}:{build_cmd_config['name']}"
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
                            )
                        )

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

        # Install all versions first (in parallel)
        install_tasks = []
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

        if install_tasks:
            logger.info(f"Installing {len(install_tasks)} versions...")
            results = await asyncio.gather(*install_tasks, return_exceptions=True)
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Version installation failed: {result}")

        # Group benchmarks by version for parallel execution
        benchmarks_by_version: dict[str, list] = {}
        for benchmark_name, package_config, version_spec, build_cmd_config in to_run:
            version_id = self._make_version_id(version_spec)
            if version_id not in benchmarks_by_version:
                benchmarks_by_version[version_id] = []
            benchmarks_by_version[version_id].append(
                (benchmark_name, package_config, version_spec, build_cmd_config)
            )

        # Run benchmarks in parallel (one task per version)
        async def run_version_benchmarks(version_id: str, benchmarks: list):
            """Run all benchmarks for a single version sequentially."""
            for (
                benchmark_name,
                package_config,
                version_spec,
                build_cmd_config,
            ) in benchmarks:
                # Check for cancellation before each benchmark
                if self._cancel_requested:
                    logger.info(
                        f"Skipping {benchmark_name}@{version_id} due to cancellation"
                    )
                    return
                try:
                    await self.run_single_benchmark(
                        benchmark_name,
                        package_config,
                        version_spec,
                        build_cmd_config,
                    )
                except asyncio.CancelledError:
                    logger.info(f"Benchmark {benchmark_name}@{version_id} cancelled")
                    return
                except Exception as e:
                    logger.error(f"Benchmark {benchmark_name}@{version_id} failed: {e}")

        # Use semaphore to limit parallelism if max_parallel > 0
        if max_parallel > 0:
            semaphore = asyncio.Semaphore(max_parallel)

            async def run_with_semaphore(version_id: str, benchmarks: list):
                async with semaphore:
                    await run_version_benchmarks(version_id, benchmarks)

            version_tasks = [
                run_with_semaphore(vid, benchmarks)
                for vid, benchmarks in benchmarks_by_version.items()
            ]
        else:
            # Unlimited parallelism
            version_tasks = [
                run_version_benchmarks(vid, benchmarks)
                for vid, benchmarks in benchmarks_by_version.items()
            ]

        # Store tasks for cancellation
        self._running_tasks = [asyncio.create_task(coro) for coro in version_tasks]

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


# Global application state
_app: FastAPI | None = None
_orchestrator: BenchmarkOrchestrator | None = None


def create_app(
    config_file: Path,
    data_file: Path,
    cache_dir: Path,
    workspace_dir: Path,
) -> FastAPI:
    """Create and configure the FastAPI application.

    Args:
        config_file: Path to benchmarks.yaml configuration
        data_file: Path to JSON file for storing results
        cache_dir: Directory for caching virtual environments
        workspace_dir: Directory for benchmark workspaces

    Returns:
        Configured FastAPI application
    """
    global _app, _orchestrator

    app = FastAPI(
        title="atopile Benchmark Dashboard",
        description="Dashboard for tracking atopile build performance across versions",
        version="0.2.0",
    )

    # Initialize components
    data_store = DataStore(data_file)
    version_manager = VersionManager(cache_dir)
    connection_manager = ConnectionManager()

    orchestrator = BenchmarkOrchestrator(
        config_file=config_file,
        data_store=data_store,
        version_manager=version_manager,
        workspace_dir=workspace_dir,
        connection_manager=connection_manager,
    )

    _app = app
    _orchestrator = orchestrator

    # Setup templates
    template_dir = Path(__file__).parent / "templates"
    templates = Jinja2Templates(directory=str(template_dir))

    # Setup static files if directory exists
    static_dir = Path(__file__).parent / "static"
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    # ==================== HTML Routes ====================

    @app.get("/", response_class=HTMLResponse)
    async def dashboard(request: Request):
        """Serve the main dashboard page."""
        return templates.TemplateResponse("index.html", {"request": request})

    # ==================== API Routes ====================

    @app.get("/api/config")
    async def get_config():
        """Get benchmark configuration."""
        return JSONResponse(orchestrator.config)

    @app.get("/api/results")
    async def get_results():
        """Get all benchmark results."""
        return JSONResponse(orchestrator.data_store.get_all_results())

    @app.get("/api/results/matrix")
    async def get_results_matrix():
        """Get results organized as a matrix (benchmark -> version -> result)."""
        return JSONResponse(orchestrator.data_store.get_results_matrix())

    @app.get("/api/results/summary")
    async def get_results_summary():
        """Get summary statistics for all benchmarks."""
        return JSONResponse(orchestrator.data_store.get_summary_statistics())

    @app.get("/api/results/history/{benchmark_name}")
    async def get_benchmark_history(benchmark_name: str):
        """Get historical results for a specific benchmark."""
        results = orchestrator.data_store.get_results_by_benchmark(benchmark_name)
        return JSONResponse(results)

    @app.get("/api/benchmarks")
    async def get_benchmarks():
        """Get list of all benchmark names."""
        return JSONResponse(orchestrator.data_store.get_benchmark_names())

    @app.get("/api/versions")
    async def get_versions():
        """Get list of configured atopile versions."""
        return JSONResponse(orchestrator.get_versions())

    @app.get("/api/versions/installed")
    async def get_installed_versions():
        """Get list of installed atopile versions."""
        installed = []
        for version_spec in orchestrator.get_versions():
            if orchestrator.version_manager.is_installed(version_spec):
                info = orchestrator.version_manager.get_version_info(version_spec)
                installed.append(
                    {
                        "spec": version_spec,
                        "info": info,
                    }
                )
        return JSONResponse(installed)

    @app.get("/api/running")
    async def get_running():
        """Get currently running benchmarks."""
        return JSONResponse(orchestrator.running_benchmarks)

    @app.post("/api/run/all")
    async def run_all(
        max_parallel: int = 4, force: bool = False, commands: str | None = None
    ):
        """Start all benchmarks.

        Args:
            max_parallel: Maximum number of versions to build in parallel (0 = unlimited)
            force: If True, rerun all benchmarks even if they already passed
            commands: Comma-separated list of build command names to run (e.g., "default,keep-picked-parts")
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
            )
        )
        return JSONResponse(
            {
                "status": "started",
                "max_parallel": max_parallel,
                "force": force,
                "commands": enabled_commands,
            }
        )

    @app.post("/api/run/stop")
    async def stop_all():
        """Stop all running benchmarks and cancel pending ones."""
        if not orchestrator.is_running():
            return JSONResponse(
                {"status": "ok", "message": "No benchmarks running"},
            )
        stopped_count = await orchestrator.stop_all_benchmarks()
        return JSONResponse({"status": "stopped", "stopped_count": stopped_count})

    @app.post("/api/run/benchmark/{benchmark_name}/version/{version_id:path}")
    async def run_single(benchmark_name: str, version_id: str):
        """Start a single benchmark for a specific version.

        Args:
            benchmark_name: Benchmark name (e.g., "indicator-leds:default")
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

        # Parse benchmark name
        if ":" not in benchmark_name:
            raise HTTPException(status_code=400, detail="Invalid benchmark_name format")

        package_name, build_cmd_name = benchmark_name.split(":", 1)

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
            )
        )

        return JSONResponse({"status": "started", "run_key": run_key})

    @app.post("/api/config/reload")
    async def reload_config():
        """Reload configuration from file."""
        try:
            orchestrator.reload_config()
            return JSONResponse({"status": "reloaded"})
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.delete("/api/results")
    async def clear_results():
        """Clear all stored results."""
        orchestrator.data_store.clear_all()
        return JSONResponse({"status": "cleared"})

    # ==================== Version Management ====================

    @app.post("/api/versions")
    async def add_version(request: Request):
        """Add a new version to the configuration and save to file.

        Automatically fetches the commit date from git for branches/commits.
        """
        data = await request.json()
        version_type = data.get("type")
        version_value = data.get("version")

        if not version_type or not version_value:
            raise HTTPException(status_code=400, detail="type and version are required")

        # Auto-detect date from git
        date_str = _get_version_date(version_type, version_value)

        new_version = {"type": version_type, "version": version_value, "date": date_str}

        # Add to config
        if "atopile_versions" not in orchestrator.config:
            orchestrator.config["atopile_versions"] = []

        # Check if version already exists
        for v in orchestrator.config["atopile_versions"]:
            if v["type"] == version_type and v["version"] == version_value:
                raise HTTPException(status_code=400, detail="Version already exists")

        orchestrator.config["atopile_versions"].append(new_version)

        # Save to file
        _save_config(orchestrator.config_file, orchestrator.config)

        return JSONResponse({"status": "added", "version": new_version})

    @app.delete("/api/versions/{version_type}/{version_value:path}")
    async def remove_version(version_type: str, version_value: str):
        """Remove a version from the configuration and save to file."""
        versions = orchestrator.config.get("atopile_versions", [])

        # Find and remove the version
        new_versions = [
            v
            for v in versions
            if not (v["type"] == version_type and v["version"] == version_value)
        ]

        if len(new_versions) == len(versions):
            raise HTTPException(status_code=404, detail="Version not found")

        orchestrator.config["atopile_versions"] = new_versions

        # Save to file
        _save_config(orchestrator.config_file, orchestrator.config)

        return JSONResponse({"status": "removed"})

    @app.get("/api/versions/date/{version_type}/{version_value:path}")
    async def get_version_date(version_type: str, version_value: str):
        """Get the commit date for a version (useful for preview before adding)."""
        date_str = _get_version_date(version_type, version_value)
        return JSONResponse({"date": date_str})

    # ==================== Cache Management ====================

    @app.get("/api/cache/info")
    async def get_cache_info():
        """Get information about the cache (size, venvs, etc.)."""
        venvs = orchestrator.version_manager.list_installed_versions()
        cache_size = orchestrator.version_manager.get_cache_size_human()

        # Get workspace size
        workspace_size = 0
        if workspace_dir.exists():
            for path in workspace_dir.rglob("*"):
                if path.is_file():
                    workspace_size += path.stat().st_size

        # Convert to human readable
        ws_size = workspace_size
        for unit in ["B", "KB", "MB", "GB"]:
            if ws_size < 1024:
                workspace_size_human = f"{ws_size:.1f} {unit}"
                break
            ws_size /= 1024
        else:
            workspace_size_human = f"{ws_size:.1f} TB"

        # Get configured version names for comparison
        configured_venvs = set()
        for version_spec in orchestrator.get_versions():
            venv_name = orchestrator.version_manager._get_venv_name(version_spec)
            configured_venvs.add(venv_name)

        # Mark which venvs are unused
        for venv in venvs:
            venv["in_config"] = venv["name"] in configured_venvs

        return JSONResponse(
            {
                "venvs": venvs,
                "venv_cache_size": cache_size,
                "workspace_size": workspace_size_human,
                "configured_venv_names": list(configured_venvs),
            }
        )

    @app.post("/api/cache/cleanup")
    async def cleanup_cache(
        remove_unused_venvs: bool = True, clear_workspaces: bool = True
    ):
        """Clean up cache to free disk space.

        Args:
            remove_unused_venvs: Remove venvs not in current config
            clear_workspaces: Clear temporary workspace directories
        """
        import shutil

        if orchestrator.is_running():
            raise HTTPException(
                status_code=409, detail="Cannot cleanup while benchmarks are running"
            )

        removed_venvs = []
        cleared_workspace = False

        if remove_unused_venvs:
            # Get configured version names
            configured_venvs = set()
            for version_spec in orchestrator.get_versions():
                venv_name = orchestrator.version_manager._get_venv_name(version_spec)
                configured_venvs.add(venv_name)

            # Remove venvs not in config
            venvs_dir = orchestrator.version_manager.venvs_dir
            if venvs_dir.exists():
                for venv_dir in venvs_dir.iterdir():
                    if venv_dir.is_dir() and venv_dir.name not in configured_venvs:
                        try:
                            shutil.rmtree(venv_dir)
                            removed_venvs.append(venv_dir.name)
                            logger.info(f"Removed unused venv: {venv_dir.name}")
                        except Exception as e:
                            logger.error(f"Failed to remove venv {venv_dir.name}: {e}")

        if clear_workspaces:
            # Clear workspace directory
            if workspace_dir.exists():
                for item in workspace_dir.iterdir():
                    try:
                        if item.is_dir():
                            shutil.rmtree(item)
                        else:
                            item.unlink()
                        cleared_workspace = True
                    except Exception as e:
                        logger.error(f"Failed to remove workspace item {item}: {e}")

        return JSONResponse(
            {
                "status": "cleaned",
                "removed_venvs": removed_venvs,
                "cleared_workspace": cleared_workspace,
            }
        )

    @app.delete("/api/cache/venv/{venv_name}")
    async def remove_venv(venv_name: str):
        """Remove a specific venv from cache."""
        import shutil

        if orchestrator.is_running():
            raise HTTPException(
                status_code=409,
                detail="Cannot remove venv while benchmarks are running",
            )

        venv_path = orchestrator.version_manager.venvs_dir / venv_name
        if not venv_path.exists():
            raise HTTPException(status_code=404, detail="Venv not found")

        try:
            shutil.rmtree(venv_path)
            logger.info(f"Removed venv: {venv_name}")
            return JSONResponse({"status": "removed", "venv": venv_name})
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    # ==================== WebSocket ====================

    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        """WebSocket endpoint for real-time updates."""
        await connection_manager.connect(websocket)
        try:
            while True:
                # Keep connection alive by receiving pings
                data = await websocket.receive_text()
                # Echo back for keep-alive
                if data == "ping":
                    await websocket.send_text("pong")
        except WebSocketDisconnect:
            connection_manager.disconnect(websocket)
        except Exception as e:
            logger.debug(f"WebSocket error: {e}")
            connection_manager.disconnect(websocket)

    return app


# Convenience for uvicorn
app = FastAPI(title="atopile Benchmark Dashboard")
