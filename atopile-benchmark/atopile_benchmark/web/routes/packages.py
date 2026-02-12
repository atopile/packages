"""Package sync status routes.

This module provides API routes for checking whether packages in the
ato registry are in sync with the local git repo (origin/main).
"""

import asyncio
import logging
from typing import Any

from fastapi import APIRouter
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/packages", tags=["packages"])


def setup_routes(orchestrator: Any) -> APIRouter:
    """Configure routes with the orchestrator instance.

    Args:
        orchestrator: BenchmarkOrchestrator instance

    Returns:
        Configured router
    """

    @router.get("/sync-status")
    async def get_sync_status(force: bool = False):
        """Get cached sync status for all enabled packages.

        Query params:
            force: If true, bypass cache and recheck
        """
        packages = orchestrator.get_enabled_packages()
        versions = orchestrator.get_versions()

        if not packages:
            return JSONResponse({})

        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(
            None,
            lambda: orchestrator.sync_checker.check_all_packages(
                packages, versions, force=force
            ),
        )
        return JSONResponse(results)

    @router.post("/sync-status/refresh")
    async def refresh_sync_status():
        """Force refresh the sync status cache."""
        packages = orchestrator.get_enabled_packages()
        versions = orchestrator.get_versions()

        if not packages:
            return JSONResponse({})

        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(
            None,
            lambda: orchestrator.sync_checker.check_all_packages(
                packages, versions, force=True
            ),
        )
        return JSONResponse(results)

    return router
