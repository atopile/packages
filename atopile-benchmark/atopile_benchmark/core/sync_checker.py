"""Package registry vs repo sync checker.

Compares package files downloaded from the ato registry (via `ato add`)
against the local git repo (origin/main) to determine if packages are
in sync with what's published.
"""

import hashlib
import json
import logging
import subprocess
import tempfile
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

# Only compare files with these extensions
SYNC_EXTENSIONS = {".ato", ".kicad_pcb"}

# Cache TTL in seconds (1 hour)
CACHE_TTL = 3600

# Timeout for ato add command
ATO_ADD_TIMEOUT = 300


REGISTRY_API_URL = "https://packages.atopileapi.com/v1/packages/all"


@dataclass
class PackageSyncResult:
    """Result of comparing a package between registry and repo."""

    synced: bool
    repo_version: str | None = None
    registry_version: str | None = None
    mismatched_files: list[str] | None = None
    error: str | None = None
    registry_only: bool = False


class SyncChecker:
    """Compares packages between the local git repo and the ato registry."""

    def __init__(
        self,
        packages_repo_path: Path,
        cache_dir: Path,
        version_manager: Any,
    ):
        self.packages_repo_path = packages_repo_path.resolve()
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.version_manager = version_manager
        self._cache_file = cache_dir / "sync_status.json"
        self._checking = False
        logger.info(f"SyncChecker initialized: packages_repo_path={self.packages_repo_path}")

    def _should_include(self, relpath: str) -> bool:
        """Check if a file should be included in the sync comparison."""
        return Path(relpath).suffix.lower() in SYNC_EXTENSIONS

    def _hash_file(self, filepath: Path) -> str:
        """Compute a git-compatible SHA1 blob hash for a file."""
        content = filepath.read_bytes()
        header = f"blob {len(content)}\0".encode()
        return hashlib.sha1(header + content).hexdigest()

    def _fetch_origin_main(self) -> bool:
        """Fetch origin/main to update the remote ref."""
        try:
            result = subprocess.run(
                ["git", "fetch", "origin", "main"],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=str(self.packages_repo_path),
            )
            if result.returncode != 0:
                logger.warning(f"git fetch failed: {result.stderr}")
                return False
            return True
        except Exception as e:
            logger.error(f"Failed to fetch origin/main: {e}")
            return False

    def _fetch_registry_packages(self) -> list[str]:
        """Fetch all package names from the ato registry API.

        Returns:
            List of full package names like 'atopile/adi-ad1938'.
        """
        import urllib.request

        try:
            with urllib.request.urlopen(REGISTRY_API_URL, timeout=30) as resp:
                data = json.loads(resp.read())
            return [p["name"] for p in data if isinstance(p, dict) and "name" in p]
        except Exception as e:
            logger.warning(f"Failed to fetch registry packages: {e}")
            return []

    def _get_repo_files(self, package_name: str) -> dict[str, str] | None:
        """Get file tree with git object hashes from origin/main for a package.

        Args:
            package_name: Short package name (e.g., "adi-ad1938")

        Returns:
            Dict mapping relative paths to git blob hashes,
            empty dict if path doesn't exist in repo,
            or None on unexpected error
        """
        tree_path = f"packages/{package_name}"
        try:
            result = subprocess.run(
                ["git", "ls-tree", "--full-tree", "-r", f"origin/main:{tree_path}"],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=str(self.packages_repo_path),
            )
            if result.returncode != 0:
                # Path doesn't exist in repo - return empty dict (not None)
                if "not a tree object" in result.stderr or "Not a valid object" in result.stderr:
                    return {}
                logger.warning(
                    f"git ls-tree failed for {package_name}: {result.stderr[:200]}"
                )
                return None

            files = {}
            for line in result.stdout.strip().split("\n"):
                if not line:
                    continue
                # Format: mode type hash\tpath
                parts = line.split("\t", 1)
                if len(parts) != 2:
                    continue
                meta, filepath = parts
                blob_hash = meta.split()[2]
                if self._should_include(filepath):
                    files[filepath] = blob_hash
            return files
        except Exception as e:
            logger.error(f"Failed to get repo files for {package_name}: {e}")
            return None

    def _get_registry_files(self, package_dir: Path) -> dict[str, str]:
        """Get file tree with computed git-compatible hashes from a downloaded package.

        Args:
            package_dir: Path to the downloaded package directory

        Returns:
            Dict mapping relative paths to computed blob hashes
        """
        files = {}
        if not package_dir.exists():
            return files

        for filepath in package_dir.rglob("*"):
            if not filepath.is_file():
                continue
            relpath = str(filepath.relative_to(package_dir))
            if not self._should_include(relpath):
                continue
            files[relpath] = self._hash_file(filepath)
        return files

    def _get_version_from_ato_yaml(self, directory: Path) -> str | None:
        """Extract package version from ato.yaml."""
        ato_yaml = directory / "ato.yaml"
        if not ato_yaml.exists():
            return None
        try:
            with open(ato_yaml) as f:
                data = yaml.safe_load(f)
            return data.get("package", {}).get("version")
        except Exception:
            return None

    def _get_repo_version(self, package_name: str) -> str | None:
        """Get the version from origin/main's ato.yaml for a package."""
        tree_path = f"packages/{package_name}/ato.yaml"
        try:
            result = subprocess.run(
                ["git", "show", f"origin/main:{tree_path}"],
                capture_output=True,
                text=True,
                timeout=10,
                cwd=str(self.packages_repo_path),
            )
            if result.returncode != 0:
                return None
            data = yaml.safe_load(result.stdout)
            return data.get("package", {}).get("version") if data else None
        except Exception:
            return None

    def check_package(
        self, name: str, registry_dir: Path
    ) -> PackageSyncResult:
        """Compare a single package between repo and registry.

        Args:
            name: Short package name (e.g., "adi-ad1938")
            registry_dir: Path to the registry-downloaded package files

        Returns:
            PackageSyncResult with comparison details
        """
        repo_files = self._get_repo_files(name)
        if repo_files is None:
            return PackageSyncResult(
                synced=False,
                error=f"Could not read repo files for {name}",
            )

        registry_files = self._get_registry_files(registry_dir)
        if not registry_files:
            return PackageSyncResult(
                synced=False,
                error=f"No registry files found for {name}",
            )

        # Get versions
        repo_version = self._get_repo_version(name)
        registry_version = self._get_version_from_ato_yaml(registry_dir)

        # Compare only .ato and .kicad_pcb files present in both sets
        all_files = set(repo_files.keys()) | set(registry_files.keys())
        mismatched = []
        for f in sorted(all_files):
            repo_hash = repo_files.get(f)
            reg_hash = registry_files.get(f)
            if repo_hash != reg_hash:
                if repo_hash is None:
                    mismatched.append(f"+ {f} (only in registry)")
                elif reg_hash is None:
                    mismatched.append(f"- {f} (only in repo)")
                else:
                    mismatched.append(f"~ {f} (content differs)")

        return PackageSyncResult(
            synced=len(mismatched) == 0,
            repo_version=repo_version,
            registry_version=registry_version,
            mismatched_files=mismatched if mismatched else None,
        )

    def _load_cache(self) -> dict[str, Any] | None:
        """Load cached sync results if still valid."""
        if not self._cache_file.exists():
            return None
        try:
            with open(self._cache_file) as f:
                data = json.load(f)
            if time.time() - data.get("timestamp", 0) < CACHE_TTL:
                return data.get("results")
            return None
        except Exception:
            return None

    def _save_cache(self, results: dict[str, Any]) -> None:
        """Save sync results to cache."""
        try:
            with open(self._cache_file, "w") as f:
                json.dump(
                    {"timestamp": time.time(), "results": results},
                    f,
                    indent=2,
                )
        except Exception as e:
            logger.warning(f"Failed to save sync cache: {e}")

    def check_all_packages(
        self,
        package_configs: list[dict],
        version_specs: list[dict],
        force: bool = False,
    ) -> dict[str, dict]:
        """Check sync status for all packages.

        Downloads packages from registry in a single temp workspace,
        then compares each against origin/main.

        Args:
            package_configs: List of package config dicts with 'name' and 'package' keys
            version_specs: List of version spec dicts to find an installed version from
            force: If True, bypass cache

        Returns:
            Dict mapping package name to sync result dict
        """
        if self._checking:
            logger.info("Sync check already in progress, returning cache")
            cached = self._load_cache()
            if cached:
                return cached
            return {}

        if not force:
            cached = self._load_cache()
            if cached:
                logger.info("Returning cached sync status")
                return cached

        self._checking = True
        results = {}

        try:
            # Fetch latest origin/main
            if not self._fetch_origin_main():
                logger.warning("Could not fetch origin/main, using existing refs")

            # Find the latest installed version to use for ato add
            version_spec = None
            for vs in reversed(version_specs):
                if vs.get("type") != "branch" and self.version_manager.is_installed(vs):
                    version_spec = vs
                    break
            if version_spec is None:
                for vs in version_specs:
                    if self.version_manager.is_installed(vs):
                        version_spec = vs
                        break

            if version_spec is None:
                logger.error("No installed atopile versions, cannot check sync")
                return {}

            ato_cmd = self.version_manager.get_ato_command(version_spec)

            # Create temp workspace for registry downloads
            with tempfile.TemporaryDirectory(prefix="sync_check_") as tmpdir:
                tmp_path = Path(tmpdir)

                for pkg_config in package_configs:
                    pkg_name = pkg_config["name"]
                    full_package = pkg_config["package"]

                    try:
                        # Set up a mini project to download the package
                        pkg_workspace = tmp_path / pkg_name
                        pkg_workspace.mkdir(parents=True)

                        (pkg_workspace / "ato.yaml").write_text(
                            "requires-atopile: '>=0.0.0'\n"
                            "paths:\n    src: '.'\n"
                            "builds:\n    default:\n        entry: main.ato:App\n"
                        )
                        (pkg_workspace / "main.ato").write_text(
                            "module App:\n    pass\n"
                        )

                        # Download package using ato add --upgrade
                        result = subprocess.run(
                            [*ato_cmd, "--non-interactive", "add", "--upgrade", full_package],
                            capture_output=True,
                            text=True,
                            timeout=ATO_ADD_TIMEOUT,
                            cwd=str(pkg_workspace),
                        )

                        if result.returncode != 0:
                            results[pkg_name] = asdict(
                                PackageSyncResult(
                                    synced=False,
                                    error=f"ato add failed: {result.stderr[:200]}",
                                )
                            )
                            continue

                        # Find the downloaded package directory
                        # Packages are downloaded to .ato/modules/<full_package>/
                        registry_dir = pkg_workspace / ".ato" / "modules" / full_package
                        if not registry_dir.exists():
                            # Try alternative location
                            for candidate in (pkg_workspace / ".ato" / "modules").rglob("ato.yaml"):
                                if candidate.parent.name == pkg_name:
                                    registry_dir = candidate.parent
                                    break

                        if not registry_dir.exists():
                            results[pkg_name] = asdict(
                                PackageSyncResult(
                                    synced=False,
                                    error="Could not find downloaded package",
                                )
                            )
                            continue

                        sync_result = self.check_package(pkg_name, registry_dir)
                        results[pkg_name] = asdict(sync_result)

                    except Exception as e:
                        logger.error(f"Error checking {pkg_name}: {e}")
                        results[pkg_name] = asdict(
                            PackageSyncResult(synced=False, error=str(e))
                        )

            # Discover registry-only packages
            try:
                registry_packages = self._fetch_registry_packages()
                config_package_set = {pc["package"] for pc in package_configs}

                for reg_pkg in registry_packages:
                    if reg_pkg in config_package_set:
                        continue  # Already checked above

                    # Extract short name: "atopile/sd-card" -> "sd-card"
                    short_name = reg_pkg.split("/", 1)[-1] if "/" in reg_pkg else reg_pkg

                    # Also skip if we already have a result under the short name
                    if short_name in results:
                        continue

                    # Check if it exists in the repo at all
                    repo_files = self._get_repo_files(short_name)
                    if repo_files is None or len(repo_files) == 0:
                        results[short_name] = asdict(PackageSyncResult(
                            synced=False,
                            registry_only=True,
                            error="Published in registry but not in repo",
                        ))
                    else:
                        results[short_name] = asdict(PackageSyncResult(
                            synced=False,
                            registry_only=True,
                            error="In registry and repo but not in benchmark config",
                        ))
            except Exception as e:
                logger.warning(f"Failed to discover registry packages: {e}")

            # Save to cache
            self._save_cache(results)

        finally:
            self._checking = False

        return results
