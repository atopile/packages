"""Manages different atopile versions in isolated virtual environments.

This module provides version management for atopile, supporting:
- PyPI releases (e.g., "0.12.4")
- GitHub branches (e.g., "main")
- Git commits (specific hashes)
- Local development directories

Uses 'uv' for fast venv creation and package installation with Python version support.
"""

import logging
import os
import shutil
import subprocess
import sys
import threading
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Global lock for version installation to prevent race conditions
_install_locks: dict[str, threading.Lock] = {}
_install_locks_lock = threading.Lock()

# Timeout constants
VENV_CREATE_TIMEOUT = 120  # seconds (may need to download Python)
PIP_UPGRADE_TIMEOUT = 120  # seconds
INSTALL_TIMEOUT = 300  # 5 minutes
VERSION_CHECK_TIMEOUT = 10  # seconds

# Default Python versions for different version types
# stage/0.14.x and related commits require Python 3.14+
DEFAULT_PYTHON_VERSIONS = {
    "stage/0.14.x": "3.14",
    # Commits from stage/0.14.x branch that require Python 3.14
    "1e3f824": "3.14",
}


class VersionManager:
    """Manages atopile installations across different versions.

    Each version is installed in an isolated virtual environment.
    Venvs are cached to avoid reinstallation on subsequent runs.

    Supported version types:
    - release: PyPI release versions (e.g., "0.12.4")
    - branch: GitHub branches (e.g., "main")
    - commit: Specific git commits (short or full hash)
    - local: Local development directories (supports ~ expansion)
    """

    # GitHub repository URL
    GITHUB_REPO = "https://github.com/atopile/atopile.git"

    def __init__(self, cache_dir: Path):
        """Initialize the version manager.

        Args:
            cache_dir: Directory to cache virtual environments
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.venvs_dir = self.cache_dir / "venvs"
        self.venvs_dir.mkdir(exist_ok=True)
        self.clones_dir = self.cache_dir / "clones"
        self.clones_dir.mkdir(exist_ok=True)

    def _get_venv_name(self, version_spec: dict[str, Any]) -> str:
        """Generate a unique name for a version's venv.

        Args:
            version_spec: Dictionary with 'type' and 'version' keys

        Returns:
            Unique venv directory name

        Raises:
            ValueError: If version type is unknown
        """
        version_type = version_spec["type"]
        version = version_spec["version"]

        if version_type == "release":
            return f"release_{version}"
        elif version_type == "branch":
            # Sanitize branch name for filesystem
            safe_branch = version.replace("/", "_").replace("\\", "_")
            return f"branch_{safe_branch}"
        elif version_type == "commit":
            # Use short hash for readability
            short_hash = version[:8] if len(version) > 8 else version
            return f"commit_{short_hash}"
        elif version_type == "local":
            # Use hash of path for uniqueness
            import hashlib

            path_hash = hashlib.md5(version.encode()).hexdigest()[:8]
            return f"local_{path_hash}"
        else:
            raise ValueError(f"Unknown version type: {version_type}")

    def _get_venv_path(self, version_spec: dict[str, Any]) -> Path:
        """Get the path to a venv for this version."""
        venv_name = self._get_venv_name(version_spec)
        return self.venvs_dir / venv_name

    def _get_python_path(self, venv_path: Path) -> Path:
        """Get the path to Python in a venv."""
        return venv_path / "bin" / "python"

    def _get_pip_path(self, venv_path: Path) -> Path:
        """Get the path to pip in a venv."""
        return venv_path / "bin" / "pip"

    def _get_ato_path(self, venv_path: Path) -> Path:
        """Get the path to ato command in a venv."""
        return venv_path / "bin" / "ato"

    def is_installed(self, version_spec: dict[str, Any]) -> bool:
        """Check if a version is already installed.

        Args:
            version_spec: Dictionary with version information

        Returns:
            True if the version is installed and functional
        """
        venv_path = self._get_venv_path(version_spec)
        python_path = self._get_python_path(venv_path)

        if not python_path.exists():
            return False

        # Verify atopile is actually installed using uv
        try:
            result = subprocess.run(
                ["uv", "pip", "show", "--python", str(python_path), "atopile"],
                capture_output=True,
                text=True,
                timeout=VERSION_CHECK_TIMEOUT,
            )
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            logger.warning("Version check timed out")
            return False
        except Exception as e:
            logger.warning(f"Error checking installation: {e}")
            return False

    def _create_venv(self, venv_path: Path, python_version: str | None = None) -> None:
        """Create a new virtual environment using uv.

        Args:
            venv_path: Path where venv should be created
            python_version: Optional Python version to use (e.g., "3.14")

        Raises:
            RuntimeError: If venv creation fails
        """
        cmd = ["uv", "venv", str(venv_path)]
        if python_version:
            cmd.extend(["--python", python_version])
            logger.info(f"Creating venv with Python {python_version}")

        try:
            result = subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True,
                timeout=VENV_CREATE_TIMEOUT,
            )
            logger.debug(f"Venv created: {result.stderr}")
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to create venv: {e.stderr}")
        except subprocess.TimeoutExpired:
            raise RuntimeError("Venv creation timed out")

    def _upgrade_pip(self, venv_path: Path) -> None:
        """Upgrade pip in a venv (no-op with uv, kept for compatibility)."""
        # uv manages pip internally, no need to upgrade
        logger.debug("Using uv - pip upgrade not needed")

    def _install_package(self, venv_path: Path, package_spec: str) -> None:
        """Install a package in a venv using uv.

        Args:
            venv_path: Path to the virtual environment
            package_spec: Package specification (e.g., "atopile==0.12.4")

        Raises:
            RuntimeError: If installation fails
        """
        logger.info(f"Installing: {package_spec}")
        try:
            result = subprocess.run(
                ["uv", "pip", "install", "--python", str(venv_path / "bin" / "python"), package_spec],
                check=True,
                capture_output=True,
                text=True,
                timeout=INSTALL_TIMEOUT,
            )
            logger.debug(f"Installation output: {result.stdout}")
        except subprocess.CalledProcessError as e:
            logger.error(f"Installation failed: {e.stderr}")
            raise RuntimeError(f"Failed to install {package_spec}: {e.stderr}")
        except subprocess.TimeoutExpired:
            raise RuntimeError(f"Installation timed out after {INSTALL_TIMEOUT}s")

    def _get_install_lock(self, version_spec: dict[str, Any]) -> threading.Lock:
        """Get a lock for installing a specific version.

        This prevents race conditions when multiple threads try to install
        the same version simultaneously.
        """
        venv_name = self._get_venv_name(version_spec)
        with _install_locks_lock:
            if venv_name not in _install_locks:
                _install_locks[venv_name] = threading.Lock()
            return _install_locks[venv_name]

    def _get_python_version(self, version_spec: dict[str, Any]) -> str | None:
        """Determine the Python version required for a version spec.

        Args:
            version_spec: Dictionary with version information

        Returns:
            Python version string (e.g., "3.14") or None for default
        """
        # Check if python_version is explicitly specified
        if "python_version" in version_spec:
            return version_spec["python_version"]

        version_type = version_spec["type"]
        version = version_spec["version"]

        # Check default versions for known branches and commits
        if version_type in ("branch", "commit") and version in DEFAULT_PYTHON_VERSIONS:
            return DEFAULT_PYTHON_VERSIONS[version]

        # Also check short commit hashes (first 7-8 chars)
        if version_type == "commit":
            for known_version, python_ver in DEFAULT_PYTHON_VERSIONS.items():
                if version.startswith(known_version) or known_version.startswith(version):
                    return python_ver

        # For local paths, try to detect Python version from pyproject.toml
        if version_type == "local":
            return self._detect_python_version_from_path(version)

        return None

    def _detect_python_version_from_path(self, local_path: str) -> str | None:
        """Detect required Python version from a local project's pyproject.toml.

        Args:
            local_path: Path to the local project (may contain ~)

        Returns:
            Python version string (e.g., "3.14") or None if not detected
        """
        import re

        path = Path(os.path.expanduser(local_path))
        pyproject_path = path / "pyproject.toml"

        if not pyproject_path.exists():
            return None

        try:
            content = pyproject_path.read_text()

            # Look for requires-python in pyproject.toml
            # Common patterns:
            # requires-python = ">=3.14"
            # requires-python = ">=3.14,<3.15"
            # requires-python = "^3.14"
            match = re.search(r'requires-python\s*=\s*["\']([^"\']+)["\']', content)
            if match:
                version_constraint = match.group(1)

                # Extract the minimum version number
                # Handle patterns like >=3.14, ^3.14, ==3.14, ~=3.14
                version_match = re.search(r'(\d+\.\d+)', version_constraint)
                if version_match:
                    detected_version = version_match.group(1)
                    logger.info(f"Detected Python {detected_version} requirement from {pyproject_path}")
                    return detected_version

        except Exception as e:
            logger.debug(f"Failed to read pyproject.toml from {path}: {e}")

        return None

    def install_version(self, version_spec: dict[str, Any]) -> Path:
        """Install a specific version of atopile.

        Args:
            version_spec: Dictionary with 'type' and 'version' keys
                         Optional 'python_version' for specific Python version

        Returns:
            Path to the virtual environment

        Raises:
            RuntimeError: If installation fails
            ValueError: If version type is unknown or local path doesn't exist
        """
        venv_path = self._get_venv_path(version_spec)

        # Check if already installed (quick check without lock)
        if self.is_installed(version_spec):
            logger.info(f"Version already installed at {venv_path}")
            return venv_path

        # Acquire lock to prevent race conditions during installation
        install_lock = self._get_install_lock(version_spec)
        with install_lock:
            # Double-check after acquiring lock (another thread may have installed)
            if self.is_installed(version_spec):
                logger.info(f"Version already installed at {venv_path} (installed by another thread)")
                return venv_path

            version_type = version_spec["type"]
            version = version_spec["version"]

            logger.info(f"Installing atopile {version_type}:{version}")

            # Remove existing broken venv if present
            if venv_path.exists():
                logger.info(f"Removing broken venv at {venv_path}")
                shutil.rmtree(venv_path)

            # Determine Python version for this version
            python_version = self._get_python_version(version_spec)

            try:
                # Create new venv with appropriate Python version
                self._create_venv(venv_path, python_version)

                # Upgrade pip (no-op with uv)
                self._upgrade_pip(venv_path)

                # Determine package spec based on version type
                if version_type == "release":
                    package_spec = f"atopile=={version}"

                    # Also clone the source code for access to examples
                    clone_dir = self.clones_dir / self._get_venv_name(version_spec)
                    if clone_dir.exists():
                        shutil.rmtree(clone_dir)

                    # Clone using the version tag (v<version>)
                    tag_name = f"v{version}"
                    logger.info(f"Cloning release tag {tag_name} to {clone_dir} for examples")
                    try:
                        subprocess.run(
                            ["git", "clone", "--depth", "1", "--branch", tag_name,
                             self.GITHUB_REPO, str(clone_dir)],
                            check=True,
                            capture_output=True,
                            text=True,
                            timeout=INSTALL_TIMEOUT,
                        )
                        logger.info(f"Successfully cloned source for release {version}")
                    except subprocess.CalledProcessError as e:
                        # Log warning but continue - examples won't be available but build will work
                        logger.warning(f"Failed to clone source for release {version}: {e.stderr}")
                    except subprocess.TimeoutExpired:
                        logger.warning(f"Clone timed out for release {version}")

                elif version_type == "branch":
                    # For branches, we need to clone and install in editable mode
                    # to trigger zig compilation for the correct architecture
                    clone_dir = self.clones_dir / self._get_venv_name(version_spec)

                    if clone_dir.exists():
                        shutil.rmtree(clone_dir)

                    logger.info(f"Cloning branch {version} to {clone_dir}")
                    try:
                        # Do initial shallow clone for speed
                        subprocess.run(
                            ["git", "clone", "--depth", "1", "--branch", version,
                             self.GITHUB_REPO, str(clone_dir)],
                            check=True,
                            capture_output=True,
                            text=True,
                            timeout=INSTALL_TIMEOUT,
                        )

                        # Fetch tags for version detection (setuptools-scm/hatch-vcs needs them)
                        logger.info("Fetching tags for version detection")
                        subprocess.run(
                            ["git", "fetch", "--tags", "--depth=1"],
                            cwd=str(clone_dir),
                            check=True,
                            capture_output=True,
                            text=True,
                            timeout=60,
                        )

                        # Unshallow to get enough history for git describe to work
                        logger.info("Fetching history for version detection")
                        subprocess.run(
                            ["git", "fetch", "--unshallow", "origin", version],
                            cwd=str(clone_dir),
                            check=True,
                            capture_output=True,
                            text=True,
                            timeout=INSTALL_TIMEOUT,
                        )

                    except subprocess.CalledProcessError as e:
                        raise RuntimeError(f"Failed to clone branch {version}: {e.stderr}")

                    # Install ziglang first for zig compilation
                    python_path = self._get_python_path(venv_path)
                    logger.info("Installing ziglang for zig compilation support")
                    try:
                        subprocess.run(
                            ["uv", "pip", "install", "--python", str(python_path), "ziglang==0.14.1"],
                            check=True,
                            capture_output=True,
                            text=True,
                            timeout=INSTALL_TIMEOUT,
                        )
                    except subprocess.CalledProcessError as e:
                        logger.warning(f"Failed to install ziglang: {e.stderr}")

                    # Install in editable mode to trigger zig compilation
                    logger.info(f"Installing from cloned branch in editable mode")
                    try:
                        result = subprocess.run(
                            ["uv", "pip", "install", "--python", str(python_path), "-e", str(clone_dir)],
                            check=True,
                            capture_output=True,
                            text=True,
                            timeout=INSTALL_TIMEOUT * 2,
                        )
                        logger.debug(f"Install output: {result.stdout}")
                    except subprocess.CalledProcessError as e:
                        raise RuntimeError(f"Failed to install from branch {version}: {e.stderr}")

                    logger.info(f"Successfully installed atopile from branch {version}")
                    return venv_path

                elif version_type == "commit":
                    # For commits, we need to clone and install in editable mode
                    # to trigger zig compilation for the correct architecture
                    clone_dir = self.clones_dir / self._get_venv_name(version_spec)

                    if clone_dir.exists():
                        shutil.rmtree(clone_dir)

                    logger.info(f"Cloning repo for commit {version} to {clone_dir}")
                    try:
                        # Clone the repo (need full clone to checkout arbitrary commit)
                        subprocess.run(
                            ["git", "clone", self.GITHUB_REPO, str(clone_dir)],
                            check=True,
                            capture_output=True,
                            text=True,
                            timeout=INSTALL_TIMEOUT,
                        )

                        # Checkout the specific commit
                        logger.info(f"Checking out commit {version}")
                        subprocess.run(
                            ["git", "checkout", version],
                            cwd=str(clone_dir),
                            check=True,
                            capture_output=True,
                            text=True,
                            timeout=60,
                        )

                        # Fetch tags for version detection
                        logger.info("Fetching tags for version detection")
                        subprocess.run(
                            ["git", "fetch", "--tags"],
                            cwd=str(clone_dir),
                            check=True,
                            capture_output=True,
                            text=True,
                            timeout=60,
                        )

                    except subprocess.CalledProcessError as e:
                        raise RuntimeError(f"Failed to clone/checkout commit {version}: {e.stderr}")

                    # Install ziglang first for zig compilation
                    python_path = self._get_python_path(venv_path)
                    logger.info("Installing ziglang for zig compilation support")
                    try:
                        subprocess.run(
                            ["uv", "pip", "install", "--python", str(python_path), "ziglang==0.14.1"],
                            check=True,
                            capture_output=True,
                            text=True,
                            timeout=INSTALL_TIMEOUT,
                        )
                    except subprocess.CalledProcessError as e:
                        logger.warning(f"Failed to install ziglang: {e.stderr}")

                    # Install in editable mode to trigger zig compilation
                    logger.info(f"Installing from cloned commit in editable mode")
                    try:
                        result = subprocess.run(
                            ["uv", "pip", "install", "--python", str(python_path), "-e", str(clone_dir)],
                            check=True,
                            capture_output=True,
                            text=True,
                            timeout=INSTALL_TIMEOUT * 2,
                        )
                        logger.debug(f"Install output: {result.stdout}")
                    except subprocess.CalledProcessError as e:
                        raise RuntimeError(f"Failed to install from commit {version}: {e.stderr}")

                    logger.info(f"Successfully installed atopile from commit {version}")
                    return venv_path

                elif version_type == "local":
                    local_path = os.path.expanduser(version)
                    if not os.path.exists(local_path):
                        raise ValueError(f"Local path does not exist: {local_path}")

                    # For local development of atopile, we need to:
                    # 1. Install ziglang (required for zig compilation at runtime)
                    # 2. Install the package in editable mode

                    python_path = self._get_python_path(venv_path)
                    logger.info(f"Installing from local path: {local_path}")

                    try:
                        # Step 1: Install ziglang first (required for zig compilation)
                        # The atopile package requires ziglang to compile zig extensions at import time
                        logger.info("Installing ziglang for zig compilation support")
                        result = subprocess.run(
                            ["uv", "pip", "install", "--python", str(python_path), "ziglang==0.14.1"],
                            check=True,
                            capture_output=True,
                            text=True,
                            timeout=INSTALL_TIMEOUT,
                        )
                        logger.debug(f"ziglang install output: {result.stdout}")
                    except subprocess.CalledProcessError as e:
                        logger.warning(f"Failed to install ziglang: {e.stderr}")
                        # Continue anyway - might work without it for some versions
                    except subprocess.TimeoutExpired:
                        logger.warning("ziglang installation timed out")

                    try:
                        # Step 2: Install with uv in editable mode
                        # This will also trigger zig compilation since ziglang is now available
                        logger.info(f"Running uv pip install -e {local_path}")
                        result = subprocess.run(
                            ["uv", "pip", "install", "--python", str(python_path), "-e", local_path],
                            check=True,
                            capture_output=True,
                            text=True,
                            timeout=INSTALL_TIMEOUT * 2,  # Extra time for zig compilation
                        )
                        logger.debug(f"uv pip install output: {result.stdout}")
                    except subprocess.CalledProcessError as e:
                        raise RuntimeError(
                            f"Failed to install from {local_path}: {e.stderr}"
                        )
                    except subprocess.TimeoutExpired:
                        raise RuntimeError("Local installation timed out")

                    logger.info(f"Successfully installed atopile from {local_path}")
                    return venv_path
                else:
                    raise ValueError(f"Unknown version type: {version_type}")

                # Install the package
                self._install_package(venv_path, package_spec)

                logger.info(f"Successfully installed atopile at {venv_path}")
                return venv_path

            except Exception as e:
                # Clean up failed installation
                if venv_path.exists():
                    try:
                        shutil.rmtree(venv_path)
                    except Exception as cleanup_err:
                        logger.warning(f"Failed to cleanup after error: {cleanup_err}")
                raise

    def get_ato_command(self, version_spec: dict[str, Any]) -> list[str]:
        """Get the command to invoke ato for a specific version.

        Uses ``python -m atopile`` instead of the ``ato`` console-script so
        the command keeps working even when the venv has been relocated
        (the console-script shebang bakes in an absolute path).

        Args:
            version_spec: Dictionary with version information

        Returns:
            Command list, e.g. ["/path/to/python", "-m", "atopile"]

        Raises:
            RuntimeError: If version is not installed
        """
        if not self.is_installed(version_spec):
            raise RuntimeError(
                f"atopile not installed for {version_spec['type']}:{version_spec['version']}. "
                f"Run install_version() first."
            )

        venv_path = self._get_venv_path(version_spec)
        python_path = self._get_python_path(venv_path)

        return [str(python_path.absolute()), "-m", "atopile"]

    def get_version_info(self, version_spec: dict[str, Any]) -> dict[str, Any] | None:
        """Get information about an installed version.

        Args:
            version_spec: Dictionary with version information

        Returns:
            Dictionary with version info, or None if not installed
        """
        if not self.is_installed(version_spec):
            return None

        venv_path = self._get_venv_path(version_spec)
        python_path = self._get_python_path(venv_path)

        try:
            result = subprocess.run(
                ["uv", "pip", "show", "--python", str(python_path), "atopile"],
                capture_output=True,
                text=True,
                timeout=VERSION_CHECK_TIMEOUT,
            )

            if result.returncode == 0:
                # Parse pip show output
                info = {}
                for line in result.stdout.split("\n"):
                    if ":" in line:
                        key, value = line.split(":", 1)
                        info[key.strip()] = value.strip()

                return {
                    "version": info.get("Version"),
                    "location": info.get("Location"),
                    "venv_path": str(venv_path),
                    "requires": info.get("Requires", "").split(", ")
                    if info.get("Requires")
                    else [],
                }

        except Exception as e:
            logger.warning(f"Error getting version info: {e}")

        return None

    def cleanup_version(self, version_spec: dict[str, Any]) -> None:
        """Remove a version's virtual environment.

        Args:
            version_spec: Dictionary with version information
        """
        venv_path = self._get_venv_path(version_spec)
        if venv_path.exists():
            logger.info(f"Removing venv at {venv_path}")
            shutil.rmtree(venv_path)

    def cleanup_all(self) -> int:
        """Remove all cached virtual environments.

        Returns:
            Number of venvs removed
        """
        count = 0
        if self.venvs_dir.exists():
            for venv_dir in self.venvs_dir.iterdir():
                if venv_dir.is_dir():
                    logger.info(f"Removing venv: {venv_dir.name}")
                    shutil.rmtree(venv_dir)
                    count += 1
        return count

    def list_installed_versions(self) -> list[dict[str, Any]]:
        """List all installed versions with their info.

        Returns:
            List of dictionaries with venv name and path
        """
        if not self.venvs_dir.exists():
            return []

        versions = []
        for venv_dir in self.venvs_dir.iterdir():
            if venv_dir.is_dir():
                # Check if it's a valid venv
                python_path = self._get_python_path(venv_dir)
                if python_path.exists():
                    versions.append(
                        {
                            "name": venv_dir.name,
                            "path": str(venv_dir),
                            "valid": True,
                        }
                    )
                else:
                    versions.append(
                        {
                            "name": venv_dir.name,
                            "path": str(venv_dir),
                            "valid": False,
                        }
                    )

        return sorted(versions, key=lambda v: v["name"])

    def get_cache_size(self) -> int:
        """Get total size of cached venvs in bytes."""
        total = 0
        if self.venvs_dir.exists():
            for path in self.venvs_dir.rglob("*"):
                if path.is_file():
                    total += path.stat().st_size
        return total

    def get_cache_size_human(self) -> str:
        """Get total size of cached venvs in human-readable format."""
        size = self.get_cache_size()
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"

    def get_source_path(self, version_spec: dict[str, Any]) -> Path | None:
        """Get the path to the source code for a version.

        This is used to access example projects and other source files.

        Args:
            version_spec: Dictionary with version information

        Returns:
            Path to the source directory, or None if not available
        """
        version_type = version_spec["type"]
        version = version_spec["version"]

        if version_type == "local":
            # For local versions, the path is the source
            local_path = Path(os.path.expanduser(version))
            if local_path.exists():
                return local_path
            return None

        # For release, branch, and commit types, check the clones directory
        clone_dir = self.clones_dir / self._get_venv_name(version_spec)
        if clone_dir.exists():
            return clone_dir

        return None

    def get_examples(self, version_spec: dict[str, Any]) -> list[dict[str, Any]]:
        """Discover example projects in a version's source code.

        Looks for subdirectories in the examples/ directory that contain ato.yaml.

        Args:
            version_spec: Dictionary with version information

        Returns:
            List of dictionaries with example info:
            - name: Example project name (e.g., "blinky")
            - path: Full path to the example directory
            - entry: Entry point from ato.yaml (if found)
        """
        source_path = self.get_source_path(version_spec)
        if source_path is None:
            logger.debug(f"No source path found for {version_spec['type']}:{version_spec['version']}")
            return []

        examples_dir = source_path / "examples"
        if not examples_dir.exists():
            logger.debug(f"No examples directory found at {examples_dir}")
            return []

        examples = []
        for item in sorted(examples_dir.iterdir()):
            if item.is_dir():
                ato_yaml = item / "ato.yaml"
                if ato_yaml.exists():
                    example_info = {
                        "name": item.name,
                        "path": str(item),
                    }

                    # Try to parse the ato.yaml to get entry point
                    try:
                        import yaml
                        with open(ato_yaml, "r") as f:
                            config = yaml.safe_load(f)
                            if config and "builds" in config:
                                # Get the default build entry or first available
                                builds = config["builds"]
                                if "default" in builds and "entry" in builds["default"]:
                                    example_info["entry"] = builds["default"]["entry"]
                                elif builds:
                                    first_build = next(iter(builds.values()))
                                    if "entry" in first_build:
                                        example_info["entry"] = first_build["entry"]
                    except Exception as e:
                        logger.debug(f"Failed to parse ato.yaml for {item.name}: {e}")

                    examples.append(example_info)
                    logger.debug(f"Found example: {item.name}")

        logger.info(f"Discovered {len(examples)} examples for {version_spec['type']}:{version_spec['version']}")
        return examples

    def has_examples(self, version_spec: dict[str, Any]) -> bool:
        """Check if a version has example projects available.

        Args:
            version_spec: Dictionary with version information

        Returns:
            True if examples are available
        """
        source_path = self.get_source_path(version_spec)
        if source_path is None:
            return False

        examples_dir = source_path / "examples"
        return examples_dir.exists() and any(
            (item / "ato.yaml").exists()
            for item in examples_dir.iterdir()
            if item.is_dir()
        )

    def ensure_source_cloned(self, version_spec: dict[str, Any]) -> bool:
        """Ensure source code is cloned for a version.

        For release and branch types, clones the source if not already present.
        Useful for versions that were installed before source cloning was added.

        Args:
            version_spec: Dictionary with version information

        Returns:
            True if source is available after this call
        """
        version_type = version_spec["type"]
        version = version_spec["version"]

        # Local versions already have source
        if version_type == "local":
            local_path = Path(os.path.expanduser(version))
            return local_path.exists()

        # Check if already cloned
        clone_dir = self.clones_dir / self._get_venv_name(version_spec)
        if clone_dir.exists():
            return True

        # Clone based on version type
        if version_type == "release":
            tag_name = f"v{version}"
            logger.info(f"Cloning release tag {tag_name} to {clone_dir}")
            try:
                subprocess.run(
                    ["git", "clone", "--depth", "1", "--branch", tag_name,
                     self.GITHUB_REPO, str(clone_dir)],
                    check=True,
                    capture_output=True,
                    text=True,
                    timeout=INSTALL_TIMEOUT,
                )
                logger.info(f"Successfully cloned source for release {version}")
                return True
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to clone source for release {version}: {e.stderr}")
                return False
            except subprocess.TimeoutExpired:
                logger.error(f"Clone timed out for release {version}")
                return False

        elif version_type == "branch":
            logger.info(f"Cloning branch {version} to {clone_dir}")
            try:
                # Initial shallow clone
                subprocess.run(
                    ["git", "clone", "--depth", "1", "--branch", version,
                     self.GITHUB_REPO, str(clone_dir)],
                    check=True,
                    capture_output=True,
                    text=True,
                    timeout=INSTALL_TIMEOUT,
                )

                # Fetch tags for version detection
                logger.info("Fetching tags for version detection")
                subprocess.run(
                    ["git", "fetch", "--tags", "--depth=1"],
                    cwd=str(clone_dir),
                    check=True,
                    capture_output=True,
                    text=True,
                    timeout=60,
                )

                # Unshallow to get enough history for git describe to work
                logger.info("Fetching history for version detection")
                subprocess.run(
                    ["git", "fetch", "--unshallow", "origin", version],
                    cwd=str(clone_dir),
                    check=True,
                    capture_output=True,
                    text=True,
                    timeout=INSTALL_TIMEOUT,
                )

                logger.info(f"Successfully cloned source for branch {version}")
                return True
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to clone source for branch {version}: {e.stderr}")
                return False
            except subprocess.TimeoutExpired:
                logger.error(f"Clone timed out for branch {version}")
                return False

        elif version_type == "commit":
            # For commits, we need to do a full clone then checkout
            logger.info(f"Cloning commit {version} to {clone_dir}")
            try:
                subprocess.run(
                    ["git", "clone", self.GITHUB_REPO, str(clone_dir)],
                    check=True,
                    capture_output=True,
                    text=True,
                    timeout=INSTALL_TIMEOUT,
                )
                subprocess.run(
                    ["git", "checkout", version],
                    cwd=str(clone_dir),
                    check=True,
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                logger.info(f"Successfully cloned source for commit {version}")
                return True
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to clone source for commit {version}: {e.stderr}")
                if clone_dir.exists():
                    shutil.rmtree(clone_dir)
                return False
            except subprocess.TimeoutExpired:
                logger.error(f"Clone timed out for commit {version}")
                if clone_dir.exists():
                    shutil.rmtree(clone_dir)
                return False

        return False
