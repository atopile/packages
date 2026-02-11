"""Core data models for benchmark results.

This module defines the fundamental data structures used throughout
the benchmark system for tracking build phases and results.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class BuildPhase:
    """Timing information for a build phase."""

    name: str
    duration: float  # seconds


@dataclass
class BenchmarkResult:
    """Result of a single benchmark run."""

    benchmark_name: str
    version_spec: dict[str, Any]
    build_command: str
    status: str  # "success", "failure", "stub", "incompatible"
    total_time: float | None = None  # seconds
    phases: list[BuildPhase] = field(default_factory=list)
    error_message: str | None = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    start_time: float | None = None  # Unix timestamp when benchmark started
    package_available: bool = True  # False if fell back to stub project
    package_version: str | None = None  # Version of the package that was built
    incompatible_reason: str | None = None  # Reason for version incompatibility
    build_target: str | None = None  # Specific build target (e.g., "red", "green")
