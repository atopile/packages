"""Data persistence and analysis for benchmark results.

This module provides a JSON-based storage system for benchmark results
with query and analysis capabilities.
"""

import json
import logging
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any

from .models import BenchmarkResult, BuildPhase

logger = logging.getLogger(__name__)


class DataStore:
    """Manages benchmark result persistence and analysis.

    Results are stored in a JSON file with the structure:
    {
        "results": [
            {
                "benchmark_name": "package:command",
                "version_spec": {"type": "release", "version": "0.12.4", "date": "..."},
                "build_command": "ato build",
                "status": "success|failure",
                "total_time": 12.34,
                "phases": [...],
                "error_message": null,
                "timestamp": "2024-01-01T00:00:00",
                "start_time": 1234567890.123
            },
            ...
        ]
    }
    """

    def __init__(self, data_file: Path):
        """Initialize the data store.

        Args:
            data_file: Path to JSON file for storing results
        """
        self.data_file = Path(data_file)
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        """Create the data file if it doesn't exist."""
        if not self.data_file.exists():
            self.data_file.parent.mkdir(parents=True, exist_ok=True)
            self._save_data({"results": []})

    def _load_data(self) -> dict[str, Any]:
        """Load data from the JSON file."""
        try:
            with open(self.data_file, 'r') as f:
                data = json.load(f)
                # Ensure results key exists
                if "results" not in data:
                    data["results"] = []
                return data
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in data file: {e}")
            return {"results": []}
        except Exception as e:
            logger.error(f"Failed to load data: {e}")
            return {"results": []}

    def _save_data(self, data: dict[str, Any]):
        """Save data to the JSON file."""
        try:
            with open(self.data_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save data: {e}")

    # ==================== Write Operations ====================

    def add_result(self, result: BenchmarkResult):
        """Add a benchmark result to the store.

        Args:
            result: BenchmarkResult to store
        """
        data = self._load_data()

        # Convert result to dict, handling BuildPhase objects
        result_dict = asdict(result)

        # Ensure phases are serializable
        if result_dict.get("phases"):
            result_dict["phases"] = [
                {"name": p["name"], "duration": p["duration"]}
                for p in result_dict["phases"]
            ]

        data["results"].append(result_dict)
        self._save_data(data)
        logger.info(f"Saved result for {result.benchmark_name} ({result.status})")

    def clear_all(self):
        """Clear all stored results."""
        self._save_data({"results": []})
        logger.info("Cleared all results")

    def delete_result(self, benchmark_name: str, version_id: str) -> bool:
        """Delete a specific result.

        Args:
            benchmark_name: The benchmark name
            version_id: Version identifier (e.g., "release:0.12.4")

        Returns:
            True if a result was deleted
        """
        data = self._load_data()
        version_type, version = version_id.split(":", 1)

        initial_count = len(data["results"])
        data["results"] = [
            r for r in data["results"]
            if not (
                r["benchmark_name"] == benchmark_name and
                r["version_spec"]["type"] == version_type and
                r["version_spec"]["version"] == version
            )
        ]

        if len(data["results"]) < initial_count:
            self._save_data(data)
            return True
        return False

    # ==================== Read Operations ====================

    def get_all_results(self) -> list[dict]:
        """Get all stored results."""
        data = self._load_data()
        return data.get("results", [])

    def get_results_by_benchmark(self, benchmark_name: str) -> list[dict]:
        """Get all results for a specific benchmark.

        Args:
            benchmark_name: Name of the benchmark

        Returns:
            List of result dictionaries, sorted by timestamp
        """
        all_results = self.get_all_results()
        results = [r for r in all_results if r["benchmark_name"] == benchmark_name]
        return sorted(results, key=lambda r: r.get("timestamp", ""))

    def get_results_by_version(self, version_spec: dict) -> list[dict]:
        """Get all results for a specific atopile version.

        Args:
            version_spec: Version specification dictionary

        Returns:
            List of result dictionaries
        """
        all_results = self.get_all_results()
        return [
            r for r in all_results
            if (r["version_spec"]["type"] == version_spec["type"] and
                r["version_spec"]["version"] == version_spec["version"])
        ]

    def get_results_matrix(self) -> dict[str, dict[str, dict]]:
        """Get results organized as a matrix by benchmark and version.

        Returns:
            Dictionary with structure:
            {
                "benchmark_name": {
                    "version_id": result_dict,
                    ...
                },
                ...
            }

        Only the most recent result for each benchmark/version combo is included.
        """
        all_results = self.get_all_results()
        matrix: dict[str, dict[str, dict]] = {}

        for result in all_results:
            benchmark_name = result["benchmark_name"]
            version_spec = result["version_spec"]
            version_id = f"{version_spec['type']}:{version_spec['version']}"

            if benchmark_name not in matrix:
                matrix[benchmark_name] = {}

            # Keep only the most recent result for each benchmark/version combo
            existing = matrix[benchmark_name].get(version_id)
            if existing is None:
                matrix[benchmark_name][version_id] = result
            else:
                existing_ts = existing.get("timestamp", "")
                new_ts = result.get("timestamp", "")
                if new_ts > existing_ts:
                    matrix[benchmark_name][version_id] = result

        return matrix

    def get_benchmark_names(self) -> list[str]:
        """Get all unique benchmark names, sorted."""
        all_results = self.get_all_results()
        names = set(r["benchmark_name"] for r in all_results)
        return sorted(names)

    def get_version_specs(self) -> list[dict]:
        """Get all unique version specifications."""
        all_results = self.get_all_results()
        specs = []
        seen = set()

        for result in all_results:
            spec = result["version_spec"]
            spec_key = f"{spec['type']}:{spec['version']}"

            if spec_key not in seen:
                seen.add(spec_key)
                specs.append(spec)

        return specs

    # ==================== Analysis Operations ====================

    def get_summary_statistics(self) -> dict[str, Any]:
        """Calculate summary statistics for all results.

        Returns:
            Dictionary with:
            - total_results: Total number of results
            - success_count: Number of successful builds
            - failure_count: Number of failed builds
            - success_rate: Percentage of successful builds
            - avg_build_time: Average successful build time
            - min_build_time: Fastest successful build
            - max_build_time: Slowest successful build
            - by_version: Stats per version
            - by_benchmark: Stats per benchmark
        """
        all_results = self.get_all_results()

        if not all_results:
            return {
                "total_results": 0,
                "success_count": 0,
                "failure_count": 0,
                "success_rate": 0.0,
                "avg_build_time": None,
                "min_build_time": None,
                "max_build_time": None,
                "by_version": {},
                "by_benchmark": {},
            }

        success_results = [r for r in all_results if r["status"] == "success"]
        failure_results = [r for r in all_results if r["status"] == "failure"]
        stub_results = [r for r in all_results if r["status"] == "stub"]
        incompatible_results = [r for r in all_results if r["status"] == "incompatible"]
        success_times = [r["total_time"] for r in success_results if r.get("total_time")]
        # Only count results that actually ran (success + failure) for pass rate
        ran_results = success_results + failure_results

        # Version-level stats
        by_version: dict[str, dict] = {}
        for result in all_results:
            version_id = f"{result['version_spec']['type']}:{result['version_spec']['version']}"
            if version_id not in by_version:
                by_version[version_id] = {"success": 0, "failure": 0, "stub": 0, "incompatible": 0, "times": []}

            if result["status"] == "success":
                by_version[version_id]["success"] += 1
                if result.get("total_time"):
                    by_version[version_id]["times"].append(result["total_time"])
            elif result["status"] == "stub":
                by_version[version_id]["stub"] += 1
            elif result["status"] == "incompatible":
                by_version[version_id]["incompatible"] += 1
            else:
                by_version[version_id]["failure"] += 1

        # Calculate averages for each version
        for version_id, stats in by_version.items():
            times = stats.pop("times")
            stats["avg_time"] = sum(times) / len(times) if times else None
            stats["total_run"] = stats["success"] + stats["failure"]
            stats["total"] = stats["success"] + stats["failure"] + stats["stub"] + stats["incompatible"]

        # Benchmark-level stats
        by_benchmark: dict[str, dict] = {}
        for result in all_results:
            benchmark = result["benchmark_name"]
            if benchmark not in by_benchmark:
                by_benchmark[benchmark] = {"success": 0, "failure": 0, "stub": 0, "incompatible": 0, "times": []}

            if result["status"] == "success":
                by_benchmark[benchmark]["success"] += 1
                if result.get("total_time"):
                    by_benchmark[benchmark]["times"].append(result["total_time"])
            elif result["status"] == "stub":
                by_benchmark[benchmark]["stub"] += 1
            elif result["status"] == "incompatible":
                by_benchmark[benchmark]["incompatible"] += 1
            else:
                by_benchmark[benchmark]["failure"] += 1

        for benchmark, stats in by_benchmark.items():
            times = stats.pop("times")
            stats["avg_time"] = sum(times) / len(times) if times else None
            stats["total_run"] = stats["success"] + stats["failure"]
            stats["total"] = stats["success"] + stats["failure"] + stats["stub"] + stats["incompatible"]

        return {
            "total_results": len(all_results),
            "success_count": len(success_results),
            "failure_count": len(failure_results),
            "stub_count": len(stub_results),
            "incompatible_count": len(incompatible_results),
            "success_rate": (len(success_results) / len(ran_results) * 100) if ran_results else 0.0,
            "avg_build_time": sum(success_times) / len(success_times) if success_times else None,
            "min_build_time": min(success_times) if success_times else None,
            "max_build_time": max(success_times) if success_times else None,
            "by_version": by_version,
            "by_benchmark": by_benchmark,
        }

    def get_version_comparison(self) -> list[dict]:
        """Compare performance across versions.

        Returns:
            List of version comparison data, sorted by average build time.
            Each entry contains:
            - version_id: Version identifier
            - version_spec: Full version spec
            - avg_time: Average build time
            - min_time: Minimum build time
            - max_time: Maximum build time
            - success_rate: Success rate percentage
            - benchmark_count: Number of benchmarks run
        """
        all_results = self.get_all_results()
        version_data: dict[str, dict] = {}

        for result in all_results:
            version_spec = result["version_spec"]
            version_id = f"{version_spec['type']}:{version_spec['version']}"

            if version_id not in version_data:
                version_data[version_id] = {
                    "version_id": version_id,
                    "version_spec": version_spec,
                    "times": [],
                    "success_count": 0,
                    "failure_count": 0,
                    "total_count": 0,
                }

            version_data[version_id]["total_count"] += 1
            if result["status"] == "success":
                version_data[version_id]["success_count"] += 1
                if result.get("total_time"):
                    version_data[version_id]["times"].append(result["total_time"])
            elif result["status"] == "failure":
                version_data[version_id]["failure_count"] += 1
            # stub and incompatible are not counted as successes or failures

        comparisons = []
        for version_id, data in version_data.items():
            times = data["times"]
            ran_count = data["success_count"] + data["failure_count"]
            comparisons.append({
                "version_id": version_id,
                "version_spec": data["version_spec"],
                "avg_time": sum(times) / len(times) if times else None,
                "min_time": min(times) if times else None,
                "max_time": max(times) if times else None,
                "success_rate": (data["success_count"] / ran_count * 100) if ran_count else 0,
                "benchmark_count": data["total_count"],
            })

        # Sort by average time (None values at the end)
        return sorted(comparisons, key=lambda x: (x["avg_time"] is None, x["avg_time"] or float("inf")))

    def get_version_analysis(self, version_type: str, version_value: str, baseline_type: str | None = None, baseline_value: str | None = None) -> dict[str, Any]:
        """Get aggregate analysis for a specific version.

        Returns phase timing averages across all successful builds,
        and exception type frequency from failed builds.

        Args:
            version_type: Version type (e.g., "release", "branch")
            version_value: Version value (e.g., "0.12.5", "main")
            baseline_type: Optional baseline version type for normalization
            baseline_value: Optional baseline version value for normalization

        Returns:
            Dictionary with:
            - phase_averages: List of {name, avg_duration, count} sorted by avg_duration desc
            - exceptions: List of {type, count, examples} sorted by count desc
            - total_builds: Total number of builds for this version
            - successful_builds: Number of successful builds
            - failed_builds: Number of failed builds
            - normalized_phase_averages: Optional, if baseline provided
        """
        all_results = self.get_all_results()

        # Filter results for this version (most recent per benchmark)
        version_results: dict[str, dict] = {}
        for result in all_results:
            spec = result["version_spec"]
            if spec["type"] == version_type and spec["version"] == version_value:
                bname = result["benchmark_name"]
                existing = version_results.get(bname)
                if existing is None or result.get("timestamp", "") > existing.get("timestamp", ""):
                    version_results[bname] = result

        results_list = list(version_results.values())

        success_results = [r for r in results_list if r["status"] == "success"]
        failure_results = [r for r in results_list if r["status"] == "failure"]

        # Aggregate phase timings from successful builds
        phase_sums: dict[str, float] = {}
        phase_counts: dict[str, int] = {}
        for result in success_results:
            for phase in result.get("phases", []):
                name = phase["name"]
                duration = phase["duration"]
                phase_sums[name] = phase_sums.get(name, 0.0) + duration
                phase_counts[name] = phase_counts.get(name, 0) + 1

        phase_averages = [
            {
                "name": name,
                "avg_duration": phase_sums[name] / phase_counts[name],
                "count": phase_counts[name],
            }
            for name in phase_sums
        ]
        phase_averages.sort(key=lambda x: x["avg_duration"], reverse=True)

        # Aggregate exception types from failed builds
        exception_counts: dict[str, int] = {}
        exception_examples: dict[str, list[str]] = {}
        for result in failure_results:
            error_msg = result.get("error_message", "") or ""
            exc_type = _extract_exception_type(error_msg)
            exception_counts[exc_type] = exception_counts.get(exc_type, 0) + 1
            if exc_type not in exception_examples:
                exception_examples[exc_type] = []
            if len(exception_examples[exc_type]) < 3:
                # Store benchmark name as example
                exception_examples[exc_type].append(result["benchmark_name"])

        exceptions = [
            {
                "type": exc_type,
                "count": count,
                "examples": exception_examples.get(exc_type, []),
            }
            for exc_type, count in exception_counts.items()
        ]
        exceptions.sort(key=lambda x: x["count"], reverse=True)

        analysis: dict[str, Any] = {
            "phase_averages": phase_averages,
            "exceptions": exceptions,
            "total_builds": len(results_list),
            "successful_builds": len(success_results),
            "failed_builds": len(failure_results),
        }

        # Compute normalized phase averages if baseline is provided
        if baseline_type and baseline_value:
            baseline_results: dict[str, dict] = {}
            for result in all_results:
                spec = result["version_spec"]
                if spec["type"] == baseline_type and spec["version"] == baseline_value:
                    bname = result["benchmark_name"]
                    existing = baseline_results.get(bname)
                    if existing is None or result.get("timestamp", "") > existing.get("timestamp", ""):
                        baseline_results[bname] = result

            # Compute baseline phase averages
            baseline_phase_sums: dict[str, float] = {}
            baseline_phase_counts: dict[str, int] = {}
            for result in baseline_results.values():
                if result["status"] == "success":
                    for phase in result.get("phases", []):
                        name = phase["name"]
                        duration = phase["duration"]
                        baseline_phase_sums[name] = baseline_phase_sums.get(name, 0.0) + duration
                        baseline_phase_counts[name] = baseline_phase_counts.get(name, 0) + 1

            normalized = []
            for pa in phase_averages:
                name = pa["name"]
                if name in baseline_phase_sums and baseline_phase_counts.get(name, 0) > 0:
                    baseline_avg = baseline_phase_sums[name] / baseline_phase_counts[name]
                    if baseline_avg > 0:
                        normalized.append({
                            "name": name,
                            "normalized_duration": (pa["avg_duration"] / baseline_avg) * 100,
                            "avg_duration": pa["avg_duration"],
                            "baseline_avg_duration": baseline_avg,
                            "count": pa["count"],
                        })
                    else:
                        normalized.append({
                            "name": name,
                            "normalized_duration": None,
                            "avg_duration": pa["avg_duration"],
                            "baseline_avg_duration": 0,
                            "count": pa["count"],
                        })
            normalized.sort(key=lambda x: (x["normalized_duration"] is None, -(x["normalized_duration"] or 0)))
            analysis["normalized_phase_averages"] = normalized

        return analysis

    # ==================== Export Operations ====================

    def export_csv(self, output_file: Path):
        """Export results to CSV format.

        Args:
            output_file: Path to output CSV file
        """
        import csv

        all_results = self.get_all_results()

        if not all_results:
            logger.warning("No results to export")
            return

        columns = [
            "benchmark_name",
            "version_type",
            "version",
            "version_date",
            "build_command",
            "status",
            "total_time",
            "timestamp",
            "error_message",
        ]

        output_file = Path(output_file)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=columns)
            writer.writeheader()

            for result in all_results:
                row = {
                    "benchmark_name": result["benchmark_name"],
                    "version_type": result["version_spec"]["type"],
                    "version": result["version_spec"]["version"],
                    "version_date": result["version_spec"].get("date", ""),
                    "build_command": result["build_command"],
                    "status": result["status"],
                    "total_time": result.get("total_time"),
                    "timestamp": result["timestamp"],
                    "error_message": result.get("error_message", ""),
                }
                writer.writerow(row)

        logger.info(f"Exported {len(all_results)} results to {output_file}")

    def export_json(self, output_file: Path):
        """Export results to a formatted JSON file.

        Args:
            output_file: Path to output JSON file
        """
        output_file = Path(output_file)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        data = self._load_data()
        data["exported_at"] = datetime.now().isoformat()
        data["summary"] = self.get_summary_statistics()

        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2, default=str)

        logger.info(f"Exported data to {output_file}")


def _extract_exception_type(error_message: str) -> str:
    """Extract the exception type from an error message.

    Tries atopile CLI bullet-point errors first, then Python exception
    patterns, then falls back to categorizing by known error keywords.

    Args:
        error_message: The raw error message string

    Returns:
        A categorized exception type string
    """
    import re

    if not error_message:
        return "Unknown Error"

    # Try atopile CLI bullet-point errors (e.g., "• Offset not resolved")
    bullet_matches = re.findall(r"[•·]\s*(.+)", error_message)
    if bullet_matches:
        # Return the first error bullet, cleaned up
        msg = bullet_matches[0].strip().rstrip("│").strip()
        if len(msg) > 100:
            msg = msg[:97] + "..."
        return msg

    # Try "Failed to install" pattern
    install_match = re.search(r"(Failed to install\s+\S+)", error_message)
    if install_match:
        return install_match.group(1)

    # Try to find Python exception class names (e.g., "ValueError: ...")
    exc_match = re.search(r"(\w+Error|\w+Exception|\w+Warning):\s*(.{0,80})", error_message)
    if exc_match:
        exc_type = exc_match.group(1)
        detail = exc_match.group(2).strip()
        if detail:
            return f"{exc_type}: {detail}"
        return exc_type

    # Try "raise <ExceptionName>" pattern
    raise_match = re.search(r"raise\s+(\w+)", error_message)
    if raise_match:
        return raise_match.group(1)

    # Categorize by keywords
    msg_lower = error_message.lower()
    if "timeout" in msg_lower or "timed out" in msg_lower:
        return "Timeout"
    if "version mismatch" in msg_lower or "incompatible" in msg_lower:
        return "VersionMismatch"
    if "not found" in msg_lower or "no such file" in msg_lower:
        return "FileNotFound"
    if "permission denied" in msg_lower:
        return "PermissionDenied"
    if "syntax error" in msg_lower or "parse error" in msg_lower:
        return "SyntaxError"
    if "import" in msg_lower and "error" in msg_lower:
        return "ImportError"
    if "connection" in msg_lower:
        return "ConnectionError"
    if "memory" in msg_lower:
        return "MemoryError"

    # Try to find a line with "error" in it
    for line in error_message.strip().split("\n"):
        line = line.strip().strip("│").strip()
        if line and "error" in line.lower() and len(line) > 5 and len(line) < 120:
            # Skip timestamp-only lines
            if not re.match(r"^\d{2}:\d{2}:\d{2}", line):
                return line

    return "Unknown Error"
