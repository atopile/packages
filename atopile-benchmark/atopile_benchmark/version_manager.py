"""Manages different atopile versions in isolated virtual environments.

This module provides version management for atopile, supporting:
- PyPI releases (e.g., "0.12.4")
- GitHub branches (e.g., "main")
- Git commits (specific hashes)
- Local development directories
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
VENV_CREATE_TIMEOUT = 60  # seconds
PIP_UPGRADE_TIMEOUT = 120  # seconds
INSTALL_TIMEOUT = 300  # 5 minutes
VERSION_CHECK_TIMEOUT = 10  # seconds


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

        # Verify atopile is actually installed
        try:
            result = subprocess.run(
                [str(python_path), "-m", "pip", "show", "atopile"],
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

    def _create_venv(self, venv_path: Path) -> None:
        """Create a new virtual environment.

        Args:
            venv_path: Path where venv should be created

        Raises:
            RuntimeError: If venv creation fails
        """
        try:
            subprocess.run(
                [sys.executable, "-m", "venv", str(venv_path)],
                check=True,
                capture_output=True,
                text=True,
                timeout=VENV_CREATE_TIMEOUT,
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to create venv: {e.stderr}")
        except subprocess.TimeoutExpired:
            raise RuntimeError("Venv creation timed out")

    def _upgrade_pip(self, venv_path: Path) -> None:
        """Upgrade pip in a venv."""
        python_path = self._get_python_path(venv_path)
        try:
            subprocess.run(
                [str(python_path), "-m", "pip", "install", "--upgrade", "pip"],
                check=True,
                capture_output=True,
                text=True,
                timeout=PIP_UPGRADE_TIMEOUT,
            )
        except subprocess.CalledProcessError as e:
            logger.warning(f"Failed to upgrade pip: {e.stderr}")
        except subprocess.TimeoutExpired:
            logger.warning("Pip upgrade timed out")

    def _install_package(self, venv_path: Path, package_spec: str) -> None:
        """Install a package in a venv.

        Args:
            venv_path: Path to the virtual environment
            package_spec: Package specification (e.g., "atopile==0.12.4")

        Raises:
            RuntimeError: If installation fails
        """
        pip_path = self._get_pip_path(venv_path)

        logger.info(f"Installing: {package_spec}")
        try:
            result = subprocess.run(
                [str(pip_path), "install", package_spec],
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

    def install_version(self, version_spec: dict[str, Any]) -> Path:
        """Install a specific version of atopile.

        Args:
            version_spec: Dictionary with 'type' and 'version' keys

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

            try:
                # Create new venv
                self._create_venv(venv_path)

                # Upgrade pip
                self._upgrade_pip(venv_path)

                # Determine package spec based on version type
                if version_type == "release":
                    package_spec = f"atopile=={version}"
                elif version_type == "branch":
                    package_spec = f"git+{self.GITHUB_REPO}@{version}"
                elif version_type == "commit":
                    package_spec = f"git+{self.GITHUB_REPO}@{version}"
                elif version_type == "local":
                    local_path = os.path.expanduser(version)
                    if not os.path.exists(local_path):
                        raise ValueError(f"Local path does not exist: {local_path}")

                    # For local development of atopile, we need to:
                    # 1. Install ziglang (required for zig compilation at runtime)
                    # 2. Install the package in editable mode

                    pip_path = self._get_pip_path(venv_path)
                    python_path = self._get_python_path(venv_path)
                    logger.info(f"Installing from local path: {local_path}")

                    try:
                        # Step 1: Install ziglang first (required for zig compilation)
                        # The atopile package requires ziglang to compile zig extensions at import time
                        logger.info("Installing ziglang for zig compilation support")
                        result = subprocess.run(
                            [str(pip_path), "install", "ziglang==0.14.1"],
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
                        # Step 2: Install with pip in editable mode
                        # This will also trigger zig compilation since ziglang is now available
                        logger.info(f"Running pip install -e {local_path}")
                        result = subprocess.run(
                            [str(pip_path), "install", "-e", local_path],
                            check=True,
                            capture_output=True,
                            text=True,
                            timeout=INSTALL_TIMEOUT * 2,  # Extra time for zig compilation
                        )
                        logger.debug(f"pip install output: {result.stdout}")
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

    def get_ato_command(self, version_spec: dict[str, Any]) -> str:
        """Get the path to the ato command for a specific version.

        Args:
            version_spec: Dictionary with version information

        Returns:
            Absolute path to the ato executable

        Raises:
            RuntimeError: If version is not installed
        """
        venv_path = self._get_venv_path(version_spec)
        ato_path = self._get_ato_path(venv_path)

        if not ato_path.exists():
            raise RuntimeError(
                f"atopile not installed for {version_spec['type']}:{version_spec['version']}. "
                f"Run install_version() first."
            )

        return str(ato_path.absolute())

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
                [str(python_path), "-m", "pip", "show", "atopile"],
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
