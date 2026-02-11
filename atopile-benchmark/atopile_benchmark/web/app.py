"""FastAPI application factory.

This module provides the create_app function that creates and configures
the FastAPI application with all routes, middleware, and dependencies.
"""

import logging
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request

from ..core.data_store import DataStore
from ..core.version_manager import VersionManager
from .orchestrator import BenchmarkOrchestrator
from .websocket import ConnectionManager
from .routes import benchmarks, results, config, versions, cache

logger = logging.getLogger(__name__)


def create_app(
    config_file: Path,
    data_file: Path,
    cache_dir: Path,
    workspace_dir: Path,
) -> FastAPI:
    """Create and configure the FastAPI application.

    Args:
        config_file: Path to benchmarks.yaml configuration
        data_file: Path to JSON file for storing results
        cache_dir: Directory for caching virtual environments
        workspace_dir: Directory for benchmark workspaces

    Returns:
        Configured FastAPI application
    """
    app = FastAPI(
        title="atopile Benchmark Dashboard",
        description="Dashboard for tracking atopile build performance across versions",
        version="0.2.0",
    )

    # Initialize core components
    data_store = DataStore(data_file)
    version_manager = VersionManager(cache_dir)
    connection_manager = ConnectionManager()

    orchestrator = BenchmarkOrchestrator(
        config_file=config_file,
        data_store=data_store,
        version_manager=version_manager,
        workspace_dir=workspace_dir,
        connection_manager=connection_manager,
    )

    # Setup templates
    template_dir = Path(__file__).parent.parent / "templates"
    templates = Jinja2Templates(directory=str(template_dir))

    # Setup static files if directory exists
    static_dir = Path(__file__).parent.parent / "static"
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    # ==================== HTML Routes ====================

    @app.get("/", response_class=HTMLResponse)
    async def dashboard(request: Request):
        """Serve the main dashboard page."""
        return templates.TemplateResponse("index.html", {"request": request})

    # ==================== WebSocket ====================

    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        """WebSocket endpoint for real-time updates."""
        await connection_manager.connect(websocket)
        try:
            while True:
                # Keep connection alive by receiving pings
                data = await websocket.receive_text()
                # Echo back for keep-alive
                if data == "ping":
                    await websocket.send_text("pong")
        except WebSocketDisconnect:
            connection_manager.disconnect(websocket)
        except Exception as e:
            logger.debug(f"WebSocket error: {e}")
            connection_manager.disconnect(websocket)

    # ==================== Register API Routes ====================

    # Setup and include all route modules
    app.include_router(benchmarks.setup_routes(orchestrator))
    app.include_router(results.setup_routes(orchestrator))
    app.include_router(config.setup_routes(orchestrator))
    app.include_router(versions.setup_routes(orchestrator))
    app.include_router(cache.setup_routes(orchestrator, workspace_dir))

    # Store orchestrator on app state for access from other parts if needed
    app.state.orchestrator = orchestrator

    return app


# Convenience for uvicorn - create a default app instance
# This allows running: uvicorn atopile_benchmark.web.app:app
app = FastAPI(title="atopile Benchmark Dashboard")
