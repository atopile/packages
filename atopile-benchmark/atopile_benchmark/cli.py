"""Command-line interface for the benchmark dashboard.

Usage:
    # Start the dashboard server
    python -m atopile_benchmark

    # Start with custom config
    python -m atopile_benchmark --config config/my-benchmarks.yaml

    # Start on a different port
    python -m atopile_benchmark --port 3000

    # Show help
    python -m atopile_benchmark --help
"""

import argparse
import logging
import sys
from pathlib import Path

import uvicorn

from .web.app import create_app

# Default values - use new directory structure
DEFAULT_CONFIG = Path("config/benchmarks.yaml")
DEFAULT_DATA_FILE = Path("data/benchmark_results.json")
DEFAULT_CACHE_DIR = Path("data/cache")
DEFAULT_PORT = 8080
DEFAULT_HOST = "127.0.0.1"

# Legacy paths for backwards compatibility
LEGACY_CONFIG = Path("benchmarks.yaml")
LEGACY_DATA_FILE = Path("benchmark_results.json")
LEGACY_CACHE_DIR = Path("benchmark_cache")


def setup_logging(verbose: bool = False, quiet: bool = False) -> None:
    """Configure logging based on verbosity settings.

    Args:
        verbose: Enable debug-level logging
        quiet: Suppress all but error messages
    """
    if quiet:
        level = logging.ERROR
    elif verbose:
        level = logging.DEBUG
    else:
        level = logging.INFO

    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def print_banner(
    host: str, port: int, config: Path, data_file: Path, cache_dir: Path
) -> None:
    """Print the startup banner."""
    print()
    print("  atopile Benchmark Dashboard")
    print("  " + "=" * 30)
    print()
    print(f"  Dashboard:  http://{host}:{port}")
    print(f"  Config:     {config}")
    print(f"  Data file:  {data_file}")
    print(f"  Cache dir:  {cache_dir}")
    print()
    print("  Press Ctrl+C to stop")
    print()


def find_config_file(specified: Path | None) -> Path:
    """Find the configuration file, checking new and legacy paths.

    Args:
        specified: User-specified config path, or None for default

    Returns:
        Path to the configuration file

    Raises:
        FileNotFoundError: If no configuration file is found
    """
    if specified is not None:
        if specified.exists():
            return specified
        raise FileNotFoundError(f"Config file not found: {specified}")

    # Check new structure first
    if DEFAULT_CONFIG.exists():
        return DEFAULT_CONFIG

    # Fall back to legacy path
    if LEGACY_CONFIG.exists():
        return LEGACY_CONFIG

    raise FileNotFoundError(
        f"Config file not found. Expected at {DEFAULT_CONFIG} or {LEGACY_CONFIG}"
    )


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser."""
    parser = argparse.ArgumentParser(
        prog="atopile-benchmark",
        description="atopile Build Speed Benchmark Dashboard - Track and compare build performance across atopile versions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start the dashboard with default settings
  python -m atopile_benchmark

  # Use a custom config file
  python -m atopile_benchmark --config config/my-benchmarks.yaml

  # Run on a different port
  python -m atopile_benchmark --port 3000

  # Enable verbose logging
  python -m atopile_benchmark -v

  # Development mode with auto-reload
  python -m atopile_benchmark --reload
""",
    )

    # Configuration options
    config_group = parser.add_argument_group("Configuration")
    config_group.add_argument(
        "--config",
        "-c",
        type=Path,
        default=None,
        metavar="FILE",
        help=f"Path to benchmarks configuration file (default: {DEFAULT_CONFIG})",
    )
    config_group.add_argument(
        "--data-file",
        "-d",
        type=Path,
        default=None,
        metavar="FILE",
        help=f"Path to results JSON file (default: {DEFAULT_DATA_FILE})",
    )
    config_group.add_argument(
        "--cache-dir",
        type=Path,
        default=None,
        metavar="DIR",
        help=f"Directory for caching virtual environments (default: {DEFAULT_CACHE_DIR})",
    )
    config_group.add_argument(
        "--workspace-dir",
        type=Path,
        default=None,
        metavar="DIR",
        help="Directory for benchmark workspaces (default: <cache-dir>/workspaces)",
    )

    # Server options
    server_group = parser.add_argument_group("Server")
    server_group.add_argument(
        "--port",
        "-p",
        type=int,
        default=DEFAULT_PORT,
        metavar="PORT",
        help=f"Port to run the web server on (default: {DEFAULT_PORT})",
    )
    server_group.add_argument(
        "--host",
        "-H",
        type=str,
        default=DEFAULT_HOST,
        metavar="HOST",
        help=f"Host to bind to (default: {DEFAULT_HOST})",
    )
    server_group.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development",
    )

    # Logging options
    log_group = parser.add_argument_group("Logging")
    log_group.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose (debug) logging",
    )
    log_group.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Suppress all but error messages",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    """Main entry point for the CLI.

    Args:
        argv: Command-line arguments (defaults to sys.argv[1:])

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    parser = create_parser()
    args = parser.parse_args(argv)

    # Setup logging
    setup_logging(verbose=args.verbose, quiet=args.quiet)
    logger = logging.getLogger(__name__)

    # Find config file (handles new and legacy paths)
    try:
        config_file = find_config_file(args.config)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        print(
            f"Create a config file or use --config to specify a different path.",
            file=sys.stderr,
        )
        return 1

    # Determine data file and cache dir
    # Use new paths if config is in new location, otherwise use legacy
    using_new_structure = str(config_file).startswith("config/")

    if args.data_file is not None:
        data_file = args.data_file
    elif using_new_structure:
        data_file = DEFAULT_DATA_FILE
    elif LEGACY_DATA_FILE.exists():
        data_file = LEGACY_DATA_FILE
    else:
        data_file = DEFAULT_DATA_FILE

    if args.cache_dir is not None:
        cache_dir = args.cache_dir
    elif using_new_structure:
        cache_dir = DEFAULT_CACHE_DIR
    elif LEGACY_CACHE_DIR.exists():
        cache_dir = LEGACY_CACHE_DIR
    else:
        cache_dir = DEFAULT_CACHE_DIR

    # Set workspace dir if not specified
    workspace_dir = args.workspace_dir
    if workspace_dir is None:
        workspace_dir = cache_dir / "workspaces"

    # Ensure directories exist
    data_file.parent.mkdir(parents=True, exist_ok=True)
    cache_dir.mkdir(parents=True, exist_ok=True)

    # Create the FastAPI app
    try:
        app = create_app(
            config_file=config_file,
            data_file=data_file,
            cache_dir=cache_dir,
            workspace_dir=workspace_dir,
        )
    except Exception as e:
        logger.error(f"Failed to create application: {e}")
        return 1

    # Print banner
    if not args.quiet:
        print_banner(args.host, args.port, config_file, data_file, cache_dir)

    # Configure uvicorn logging
    if args.quiet:
        log_level = "error"
    elif args.verbose:
        log_level = "debug"
    else:
        log_level = "info"

    # Run the server
    try:
        uvicorn.run(
            app,
            host=args.host,
            port=args.port,
            log_level=log_level,
            reload=args.reload,
            access_log=not args.quiet,
        )
    except KeyboardInterrupt:
        if not args.quiet:
            print("\nShutting down...")
    except Exception as e:
        logger.error(f"Server error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
