"""Version management routes.

This module provides API routes for managing atopile versions.
"""

import asyncio
import logging
import shutil
import threading
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from starlette.requests import Request

from ...utils.git import get_version_date
from ...utils.config import save_config

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["versions"])


def setup_routes(orchestrator: Any) -> APIRouter:
    """Configure routes with the orchestrator instance.

    Args:
        orchestrator: BenchmarkOrchestrator instance

    Returns:
        Configured router
    """

    @router.get("/versions")
    async def get_versions():
        """Get list of configured atopile versions."""
        return JSONResponse(orchestrator.get_versions())

    @router.get("/versions/installed")
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

    @router.post("/versions")
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
        date_str = get_version_date(version_type, version_value)

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
        save_config(orchestrator.config_file, orchestrator.config)

        return JSONResponse({"status": "added", "version": new_version})

    @router.delete("/versions/{version_type}/{version_value:path}")
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
        save_config(orchestrator.config_file, orchestrator.config)

        return JSONResponse({"status": "removed"})

    @router.patch("/versions/{version_type}/{version_value:path}")
    async def toggle_version(version_type: str, version_value: str, request: Request):
        """Toggle the enabled state of a version and save to file."""
        data = await request.json()
        enabled = data.get("enabled")

        if enabled is None:
            raise HTTPException(status_code=400, detail="enabled field is required")

        versions = orchestrator.config.get("atopile_versions", [])
        found = False
        for v in versions:
            if v["type"] == version_type and v["version"] == version_value:
                if enabled:
                    v.pop("enabled", None)  # Remove field when enabled (default)
                else:
                    v["enabled"] = False
                found = True
                break

        if not found:
            raise HTTPException(status_code=404, detail="Version not found")

        save_config(orchestrator.config_file, orchestrator.config)

        return JSONResponse({"status": "updated", "enabled": enabled})

    @router.put("/versions/reorder")
    async def reorder_versions(request: Request):
        """Reorder the versions list and save to config.

        The first version in the list becomes the baseline for comparisons.
        """
        data = await request.json()
        new_versions = data.get("versions")

        if not new_versions or not isinstance(new_versions, list):
            raise HTTPException(status_code=400, detail="versions list is required")

        orchestrator.config["atopile_versions"] = new_versions

        # Save to file
        save_config(orchestrator.config_file, orchestrator.config)

        return JSONResponse({"status": "reordered", "versions": new_versions})

    @router.get("/versions/date/{version_type}/{version_value:path}")
    async def get_version_date_route(version_type: str, version_value: str):
        """Get the commit date for a version (useful for preview before adding)."""
        date_str = get_version_date(version_type, version_value)
        return JSONResponse({"date": date_str})

    @router.get("/versions/env-status")
    async def get_env_status():
        """Get environment install status and sync time for each configured version."""
        statuses = []
        for version_spec in orchestrator.get_versions():
            venv_path = orchestrator.version_manager._get_venv_path(version_spec)
            installed = orchestrator.version_manager.is_installed(version_spec)
            sync_time = None
            if installed and venv_path.exists():
                sync_time = venv_path.stat().st_mtime
            statuses.append({
                "type": version_spec["type"],
                "version": version_spec["version"],
                "installed": installed,
                "sync_time": sync_time,
                "env_created_at": version_spec.get("env_created_at"),
            })
        return JSONResponse(statuses)

    @router.post("/versions/{version_type}/{version_value:path}/rebuild-env")
    async def rebuild_env(version_type: str, version_value: str):
        """Delete and reinstall the environment for a specific version."""
        version_spec = None
        for v in orchestrator.get_versions():
            if v["type"] == version_type and v["version"] == version_value:
                version_spec = v
                break
        if not version_spec:
            raise HTTPException(status_code=404, detail="Version not found")

        vm = orchestrator.version_manager
        venv_path = vm._get_venv_path(version_spec)
        clone_dir = vm.clones_dir / vm._get_venv_name(version_spec)

        # Delete existing venv and clone
        if venv_path.exists():
            shutil.rmtree(venv_path)
        if clone_dir.exists():
            shutil.rmtree(clone_dir)

        # Reinstall in background thread
        loop = asyncio.get_event_loop()

        def _rebuild():
            try:
                vm.install_version(version_spec)
                # Persist env_created_at
                from datetime import datetime
                version_spec["env_created_at"] = datetime.now().isoformat(timespec="seconds")
                save_config(orchestrator.config_file, orchestrator.config)
                asyncio.run_coroutine_threadsafe(
                    orchestrator.connection_manager.broadcast({
                        "type": "env_rebuilt",
                        "version": version_spec,
                        "status": "success",
                    }),
                    loop,
                )
            except Exception as e:
                logger.error(f"Rebuild failed for {version_spec}: {e}")
                asyncio.run_coroutine_threadsafe(
                    orchestrator.connection_manager.broadcast({
                        "type": "env_rebuilt",
                        "version": version_spec,
                        "status": "failed",
                        "error": str(e),
                    }),
                    loop,
                )

        thread = threading.Thread(target=_rebuild, daemon=True)
        thread.start()

        return JSONResponse({"status": "rebuilding"})

    return router
