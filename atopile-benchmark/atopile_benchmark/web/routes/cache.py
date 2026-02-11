"""Cache management routes.

This module provides API routes for managing the benchmark cache.
"""

import logging
import shutil
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["cache"])


def setup_routes(orchestrator: Any, workspace_dir: Path) -> APIRouter:
    """Configure routes with the orchestrator instance.

    Args:
        orchestrator: BenchmarkOrchestrator instance
        workspace_dir: Path to the workspace directory

    Returns:
        Configured router
    """

    @router.get("/cache/info")
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

        return JSONResponse({
            "venvs": venvs,
            "venv_cache_size": cache_size,
            "workspace_size": workspace_size_human,
            "configured_venv_names": list(configured_venvs),
        })

    @router.post("/cache/cleanup")
    async def cleanup_cache(remove_unused_venvs: bool = True, clear_workspaces: bool = True):
        """Clean up cache to free disk space.

        Args:
            remove_unused_venvs: Remove venvs not in current config
            clear_workspaces: Clear temporary workspace directories
        """
        if orchestrator.is_running():
            raise HTTPException(
                status_code=409,
                detail="Cannot cleanup while benchmarks are running"
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

        return JSONResponse({
            "status": "cleaned",
            "removed_venvs": removed_venvs,
            "cleared_workspace": cleared_workspace,
        })

    @router.delete("/cache/venv/{venv_name}")
    async def remove_venv(venv_name: str):
        """Remove a specific venv from cache."""
        if orchestrator.is_running():
            raise HTTPException(
                status_code=409,
                detail="Cannot remove venv while benchmarks are running"
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

    return router
