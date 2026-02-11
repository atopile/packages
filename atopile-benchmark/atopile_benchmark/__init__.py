"""atopile build speed benchmarking suite.

This package provides a comprehensive benchmarking dashboard for tracking
atopile build performance across different versions.

Usage:
    # Start the dashboard
    python -m atopile_benchmark

    # Or import components directly
    from atopile_benchmark import BenchmarkRunner, DataStore, VersionManager
"""

__version__ = "0.2.0"
__author__ = "atopile Benchmark Team"

# Re-export core components for backwards compatibility
from .core.models import BuildPhase, BenchmarkResult
from .core.benchmark_runner import BenchmarkRunner
from .core.data_store import DataStore
from .core.version_manager import VersionManager

__all__ = [
    "BenchmarkResult",
    "BenchmarkRunner",
    "BuildPhase",
    "DataStore",
    "VersionManager",
    "__version__",
]
