"""Runs benchmarks for different atopile versions and packages.

This module handles the execution of benchmarks, including:
- Setting up isolated workspaces
- Running build commands
- Parsing build output for timing data
- Collecting results
"""

import logging
import re
import shutil
import subprocess
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from .version_manager import VersionManager

logger = logging.getLogger(__name__)

# Build timeout in seconds (60 seconds)
BUILD_TIMEOUT = 60

# Package installation timeout in seconds (5 minutes)
PACKAGE_TIMEOUT = 300


@dataclass
class BuildPhase:
    """Timing information for a build phase."""

    name: str
    duration: float  # seconds


@dataclass
class BenchmarkResult:
    """Result of a single benchmark run."""

    benchmark_name: str
    version_spec: dict[str, Any]
    build_command: str
    status: str  # "success", "failure", "stub" (package not available)
    total_time: float | None = None  # seconds
    phases: list[BuildPhase] = field(default_factory=list)
    error_message: str | None = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    start_time: float | None = None  # Unix timestamp when benchmark started
    package_available: bool = True  # False if fell back to stub project
    package_version: str | None = None  # Version of the package that was built


class BenchmarkRunner:
    """Runs benchmarks and collects timing data.

    Each benchmark:
    1. Creates an isolated workspace directory
    2. Sets up a minimal ato project
    3. Optionally adds a package
    4. Runs the build command
    5. Collects timing data
    6. Cleans up the workspace
    """

    def __init__(
        self,
        version_manager: VersionManager,
        workspace_dir: Path,
        verbose: bool = False,
    ):
        """Initialize the benchmark runner.

        Args:
            version_manager: VersionManager instance for version handling
            workspace_dir: Directory for benchmark workspaces
            verbose: Enable verbose logging
        """
        self.version_manager = version_manager
        self.workspace_dir = Path(workspace_dir)
        self.workspace_dir.mkdir(parents=True, exist_ok=True)
        self.verbose = verbose

    def _make_workspace_id(self, benchmark_name: str, version_spec: dict) -> str:
        """Generate a unique workspace ID."""
        venv_name = self.version_manager._get_venv_name(version_spec)
        timestamp = int(time.time())
        # Sanitize benchmark name for use in path
        safe_name = benchmark_name.replace(":", "_").replace("/", "_")
        return f"{safe_name}_{venv_name}_{timestamp}"

    def _parse_build_output(self, output: str) -> list[BuildPhase]:
        """Parse ato build output to extract phase timings.

        Looks for patterns like:
        - "✓ Initializing app [0.0s]"
        - "✓ Loading PCB [0.1s]"
        - "⚠ Picking components (1 warning) 0/0 [0.0s]"

        Args:
            output: Combined stdout/stderr from build

        Returns:
            List of BuildPhase objects
        """
        phases = []
        seen_phases = set()  # Avoid duplicates

        # Primary pattern: matches ato build output like "✓ Phase name [0.1s]"
        # Status symbols: ✓ (success), ⚠ (warning), ✗ (error)
        # Example: "✓ Loading PCB [0.1s]" or "⚠ Picking components (1 warning) 0/0 [0.0s]"
        pattern = r"[✓⚠✗]\s+(.+?)\s+\[([\d.]+)s\]"

        for match in re.finditer(pattern, output):
            phase_name = match.group(1).strip()
            # Clean up phase name - remove warning counts like "(1 warning)"
            phase_name = re.sub(r"\s*\(\d+\s+warnings?\)\s*", " ", phase_name)
            # Remove progress indicators like "0/0"
            phase_name = re.sub(r"\s*\d+/\d+\s*", "", phase_name)
            phase_name = phase_name.strip()

            if not phase_name:
                continue

            try:
                duration = float(match.group(2))
                # Avoid duplicate phases (take first occurrence)
                if phase_name not in seen_phases:
                    seen_phases.add(phase_name)
                    phases.append(BuildPhase(name=phase_name, duration=duration))
            except ValueError:
                continue

        return phases

    def _setup_workspace(
        self,
        package_name: str,
        version_spec: dict,
        workspace_id: str,
    ) -> tuple[Path, bool, str | None]:
        """Set up a workspace by downloading/cloning the package directly.

        Instead of creating a shell project and importing the package,
        we download the package files and build from its root directory.
        This gives accurate build times for the actual package.

        Args:
            package_name: Package name (e.g., "atopile/indicator-leds")
            version_spec: atopile version specification
            workspace_id: Unique ID for this workspace

        Returns:
            Tuple of (workspace_path, package_setup_successfully, package_version)
        """
        workspace = self.workspace_dir / workspace_id

        # Clean up existing workspace
        if workspace.exists():
            shutil.rmtree(workspace)
        workspace.mkdir(parents=True)

        # Use the TARGET atopile version to download packages
        # This ensures packages are selected based on compatibility with the target version
        # e.g., local v0.14.0 will get packages compatible with ^0.14.0

        # Ensure target version is installed first
        if not self.version_manager.is_installed(version_spec):
            logger.info(
                f"Installing {version_spec['type']}:{version_spec['version']} for package download"
            )
            self.version_manager.install_version(version_spec)

        # Get the ato command for the target version
        target_ato_cmd = self.version_manager.get_ato_command(version_spec)

        # Create a temp project to use ato add
        temp_project = workspace / "_temp_project"
        temp_project.mkdir()

        # Create minimal ato.yaml for temp project
        (temp_project / "ato.yaml").write_text("""requires-atopile: '>=0.0.0'
paths:
    src: '.'
builds:
    default:
        entry: main.ato:App
""")
        (temp_project / "main.ato").write_text("module App:\n    pass\n")

        package_setup = False
        package_version = None
        try:
            # Use the TARGET version's ato command to download the package
            # This ensures packages are selected based on compatibility with the target version
            # Use --upgrade to always fetch the latest compatible version of the package
            logger.info(f"Downloading package {package_name} using {target_ato_cmd}")
            result = subprocess.run(
                [
                    target_ato_cmd,
                    "--non-interactive",
                    "add",
                    "--upgrade",
                    package_name,
                ],
                capture_output=True,
                text=True,
                timeout=PACKAGE_TIMEOUT,
                cwd=str(temp_project),
            )

            if result.returncode == 0:
                # Try to get package version from ato.yaml dependencies
                ato_yaml_file = temp_project / "ato.yaml"
                if ato_yaml_file.exists():
                    try:
                        import yaml

                        ato_data = yaml.safe_load(ato_yaml_file.read_text())
                        if ato_data and "dependencies" in ato_data:
                            for dep in ato_data.get("dependencies", []):
                                dep_id = dep.get("identifier", "")
                                if dep_id == package_name:
                                    package_version = dep.get("release")
                                    logger.info(
                                        f"Package {package_name} version: {package_version}"
                                    )
                                    break
                    except Exception as e:
                        logger.debug(f"Could not read ato.yaml: {e}")

                # Find the downloaded package
                package_path = temp_project / ".ato" / "modules" / package_name
                if package_path.exists() and package_path.is_dir():
                    # Copy package contents to workspace root
                    for item in package_path.iterdir():
                        dest = workspace / item.name
                        if item.is_dir():
                            shutil.copytree(item, dest)
                        else:
                            shutil.copy2(item, dest)
                    package_setup = True
                    logger.debug(f"Package {package_name} set up in workspace")
                else:
                    logger.warning(f"Package directory not found at {package_path}")
            else:
                logger.warning(
                    f"Could not download package {package_name}: {result.stderr[:200]}"
                )
                if self.verbose:
                    logger.debug(f"Package add stderr: {result.stderr}")

        except subprocess.TimeoutExpired:
            logger.warning(f"Package add timed out for {package_name}")
        except Exception as e:
            logger.warning(f"Package setup failed: {e}")
        finally:
            # Clean up temp project
            if temp_project.exists():
                shutil.rmtree(temp_project)

        # If package setup failed, create a minimal fallback project
        if not package_setup:
            (workspace / "ato.yaml").write_text("""requires-atopile: '>=0.0.0'
paths:
    src: '.'
    layout: ./layouts
builds:
    default:
        entry: main.ato:App
""")
            (workspace / "layouts").mkdir(exist_ok=True)
            (
                workspace / "main.ato"
            ).write_text(f"""# Package {package_name} not available
module App:
    pass
""")

        return workspace, package_setup, package_version

    def _parse_phase_from_line(self, line: str) -> str | None:
        """Extract phase name from a single line of build output.

        Args:
            line: A single line of build output

        Returns:
            Phase name if found, None otherwise
        """
        # Match lines like "✓ Loading PCB [0.1s]" or "⚠ Picking components (1 warning) [0.0s]"
        # Also match in-progress lines without timing like "  Picking components..."
        import re

        # Completed phase pattern
        match = re.search(r"[✓⚠✗]\s+(.+?)\s+\[[\d.]+s\]", line)
        if match:
            phase_name = match.group(1).strip()
            # Clean up phase name
            phase_name = re.sub(r"\s*\(\d+\s+warnings?\)\s*", " ", phase_name)
            phase_name = re.sub(r"\s*\d+/\d+\s*", "", phase_name)
            return phase_name.strip()

        # In-progress pattern (no timing yet)
        match = re.search(r"[✓⚠✗⋯●]\s+(.+?)(?:\s*\.\.\.|\s*$)", line)
        if match:
            phase_name = match.group(1).strip()
            phase_name = re.sub(r"\s*\(\d+\s+warnings?\)\s*", " ", phase_name)
            phase_name = re.sub(r"\s*\d+/\d+\s*", "", phase_name)
            if phase_name:
                return phase_name.strip()

        return None

    def run_benchmark(
        self,
        benchmark_name: str,
        package_name: str,
        version_spec: dict,
        build_command: str,
        phase_callback: callable = None,
    ) -> BenchmarkResult:
        """Run a single benchmark.

        Args:
            benchmark_name: Name of the benchmark (e.g., "indicator-leds:default")
            package_name: Package to build (e.g., "atopile/indicator-leds")
            version_spec: atopile version specification
            build_command: Build command to run (e.g., "ato build")
            phase_callback: Optional callback(phase_name) called when a new build phase starts

        Returns:
            BenchmarkResult with timing and status information
        """
        workspace_id = self._make_workspace_id(benchmark_name, version_spec)
        workspace = self.workspace_dir / workspace_id

        result = BenchmarkResult(
            benchmark_name=benchmark_name,
            version_spec=version_spec,
            build_command=build_command,
            status="failure",  # Default to failure, set success on completion
            start_time=time.time(),
        )

        try:
            # Ensure version is installed
            if not self.version_manager.is_installed(version_spec):
                logger.info(
                    f"Installing {version_spec['type']}:{version_spec['version']}"
                )
                self.version_manager.install_version(version_spec)

            # Setup workspace
            workspace, package_added, pkg_version = self._setup_workspace(
                package_name, version_spec, workspace_id
            )

            # Track if we're building actual package or stub
            result.package_available = package_added
            result.package_version = pkg_version
            if not package_added:
                logger.warning(
                    f"Package {package_name} not available for this version, building stub"
                )
            elif pkg_version:
                logger.info(f"Building package {package_name} version {pkg_version}")

            # Get ato command
            ato_cmd = self.version_manager.get_ato_command(version_spec)

            # Parse and construct the build command
            cmd_parts = build_command.split()
            if cmd_parts[0] == "ato":
                cmd_parts[0] = ato_cmd
            else:
                cmd_parts.insert(0, ato_cmd)

            # Add --non-interactive flag after ato command
            cmd_parts.insert(1, "--non-interactive")

            logger.info(f"Running: {' '.join(cmd_parts)} in {workspace}")

            # Run the build with real-time output streaming
            build_start = time.time()
            stdout_lines = []
            stderr_lines = []
            current_phase = None

            try:
                # Use Popen for real-time output streaming
                process = subprocess.Popen(
                    cmd_parts,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,  # Merge stderr into stdout
                    text=True,
                    cwd=str(workspace),
                    bufsize=1,  # Line buffered
                )

                # Read output line by line
                for line in iter(process.stdout.readline, ""):
                    stdout_lines.append(line)

                    # Try to extract phase from line
                    phase = self._parse_phase_from_line(line)
                    if phase and phase != current_phase:
                        current_phase = phase
                        if phase_callback:
                            try:
                                phase_callback(phase)
                            except Exception as e:
                                logger.debug(f"Phase callback error: {e}")

                # Wait for process to complete
                process.wait(timeout=BUILD_TIMEOUT)
                build_end = time.time()

                result.total_time = build_end - build_start
                combined_output = "".join(stdout_lines)

                if process.returncode == 0:
                    # Mark as "stub" if package wasn't available (built empty project)
                    if not result.package_available:
                        result.status = "stub"
                        logger.info(
                            f"Stub build completed in {result.total_time:.2f}s (package not available)"
                        )
                    else:
                        result.status = "success"
                        logger.info(f"Build succeeded in {result.total_time:.2f}s")
                    # Parse output for phase timings
                    result.phases = self._parse_build_output(combined_output)

                    if self.verbose:
                        logger.debug(f"Build output:\n{combined_output}")
                else:
                    result.status = "failure"
                    # Keep last 2000 chars of error for readability
                    result.error_message = combined_output[-2000:].strip()
                    logger.error(f"Build failed with return code {process.returncode}")
                    if self.verbose:
                        logger.error(f"Error output:\n{result.error_message}")

            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
                result.status = "failure"
                result.error_message = f"Build timed out after {BUILD_TIMEOUT} seconds"
                result.total_time = float(BUILD_TIMEOUT)
                logger.error(result.error_message)
            except Exception as e:
                if "process" in locals():
                    process.kill()
                    process.wait()
                raise

        except Exception as e:
            result.status = "failure"
            result.error_message = str(e)
            logger.error(f"Benchmark failed with exception: {e}", exc_info=True)

        finally:
            # Cleanup workspace
            if workspace.exists():
                try:
                    shutil.rmtree(workspace)
                except Exception as e:
                    logger.warning(f"Failed to cleanup workspace {workspace}: {e}")

        return result

    def run_package_benchmark(
        self,
        package_config: dict,
        version_spec: dict,
        build_commands: list[dict],
    ) -> list[BenchmarkResult]:
        """Run all build command variations for a package.

        Args:
            package_config: Package configuration from YAML
            version_spec: atopile version specification
            build_commands: List of build command configurations

        Returns:
            List of BenchmarkResult objects
        """
        results = []
        version_id = f"{version_spec['type']}:{version_spec['version']}"

        for build_cmd_config in build_commands:
            benchmark_name = f"{package_config['name']}:{build_cmd_config['name']}"
            package_name = package_config["package"]
            build_command = build_cmd_config["command"]

            logger.info(f"Running benchmark: {benchmark_name} with {version_id}")

            result = self.run_benchmark(
                benchmark_name=benchmark_name,
                package_name=package_name,
                version_spec=version_spec,
                build_command=build_command,
            )

            results.append(result)

            logger.info(
                f"Benchmark {benchmark_name}@{version_id}: "
                f"{result.status} "
                f"({result.total_time:.2f}s)"
                if result.total_time
                else ""
            )

        return results
