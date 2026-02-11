"""Results retrieval and analysis routes.

This module provides API routes for accessing benchmark results.
"""

import logging
from typing import Any

from fastapi import APIRouter
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["results"])


def setup_routes(orchestrator: Any) -> APIRouter:
    """Configure routes with the orchestrator instance.

    Args:
        orchestrator: BenchmarkOrchestrator instance

    Returns:
        Configured router
    """

    @router.get("/results")
    async def get_results():
        """Get all benchmark results."""
        return JSONResponse(orchestrator.data_store.get_all_results())

    @router.get("/results/matrix")
    async def get_results_matrix():
        """Get results organized as a matrix (benchmark -> version -> result)."""
        return JSONResponse(orchestrator.data_store.get_results_matrix())

    @router.get("/results/summary")
    async def get_results_summary():
        """Get summary statistics for all benchmarks."""
        return JSONResponse(orchestrator.data_store.get_summary_statistics())

    @router.get("/results/history/{benchmark_name}")
    async def get_benchmark_history(benchmark_name: str):
        """Get historical results for a specific benchmark."""
        results = orchestrator.data_store.get_results_by_benchmark(benchmark_name)
        return JSONResponse(results)

    @router.delete("/results")
    async def clear_results():
        """Clear all stored results."""
        orchestrator.data_store.clear_all()
        return JSONResponse({"status": "cleared"})

    return router
