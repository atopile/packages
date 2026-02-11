"""Configuration management routes.

This module provides API routes for managing benchmark configuration.
"""

import logging
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["config"])


def setup_routes(orchestrator: Any) -> APIRouter:
    """Configure routes with the orchestrator instance.

    Args:
        orchestrator: BenchmarkOrchestrator instance

    Returns:
        Configured router
    """

    @router.get("/config")
    async def get_config():
        """Get benchmark configuration."""
        return JSONResponse(orchestrator.config)

    @router.post("/config/reload")
    async def reload_config():
        """Reload configuration from file."""
        try:
            orchestrator.reload_config()
            return JSONResponse({"status": "reloaded"})
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    return router
