"""Git utilities for version date retrieval.

This module provides functions to fetch commit dates from the atopile
repository for various version types (releases, branches, commits).
"""

import json
import logging
import subprocess
import urllib.request
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


def get_version_date(version_type: str, version_value: str) -> str:
    """Get the commit date for a version from git.

    For releases, fetches the tag date from the atopile repo.
    For branches, fetches the latest commit date.
    For commits, fetches the commit date.
    For local paths, uses today's date.

    Args:
        version_type: Type of version (release, branch, commit, local)
        version_value: Version value (e.g., "0.12.4", "main", commit hash, path)

    Returns:
        Date string in YYYY-MM-DD format
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
                return get_commit_date_from_hash(commit_hash)

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
                return get_commit_date_from_hash(commit_hash)

        elif version_type == "commit":
            return get_commit_date_from_hash(version_value)

    except Exception as e:
        logger.warning(
            f"Failed to get git date for {version_type}:{version_value}: {e}"
        )

    return today


def get_commit_date_from_hash(commit_hash: str) -> str:
    """Get the commit date for a specific hash from the atopile repo.

    Args:
        commit_hash: Git commit hash (short or full)

    Returns:
        Date string in YYYY-MM-DD format
    """
    try:
        # Use GitHub API to get commit info (doesn't require clone)
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
