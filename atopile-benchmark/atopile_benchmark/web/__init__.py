"""Web server layer for the benchmark dashboard.

This module contains:
- app: FastAPI application factory
- websocket: WebSocket connection manager
- orchestrator: Benchmark orchestration
- routes: API route handlers
"""

from .app import create_app
from .websocket import ConnectionManager
from .orchestrator import BenchmarkOrchestrator

__all__ = [
    "create_app",
    "ConnectionManager",
    "BenchmarkOrchestrator",
]
