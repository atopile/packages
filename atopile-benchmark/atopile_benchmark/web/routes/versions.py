"""Version management routes.

This module provides API routes for managing atopile versions.
"""

import logging
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

    @router.get("/versions/date/{version_type}/{version_value:path}")
    async def get_version_date_route(version_type: str, version_value: str):
        """Get the commit date for a version (useful for preview before adding)."""
        date_str = get_version_date(version_type, version_value)
        return JSONResponse({"date": date_str})

    return router
