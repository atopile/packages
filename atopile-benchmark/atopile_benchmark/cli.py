"""Command-line interface for the benchmark dashboard.

Usage:
    # Start the dashboard server
    python -m atopile_benchmark

    # Start with custom config
    python -m atopile_benchmark --config my-benchmarks.yaml

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

from .dashboard import create_app

# Default values
DEFAULT_CONFIG = Path("benchmarks.yaml")
DEFAULT_DATA_FILE = Path("benchmark_results.json")
DEFAULT_CACHE_DIR = Path("benchmark_cache")
DEFAULT_PORT = 8080
DEFAULT_HOST = "127.0.0.1"


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
  python -m atopile_benchmark --config my-benchmarks.yaml

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
        default=DEFAULT_CONFIG,
        metavar="FILE",
        help=f"Path to benchmarks configuration file (default: {DEFAULT_CONFIG})",
    )
    config_group.add_argument(
        "--data-file",
        "-d",
        type=Path,
        default=DEFAULT_DATA_FILE,
        metavar="FILE",
        help=f"Path to results JSON file (default: {DEFAULT_DATA_FILE})",
    )
    config_group.add_argument(
        "--cache-dir",
        type=Path,
        default=DEFAULT_CACHE_DIR,
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

    # Validate config file exists
    if not args.config.exists():
        print(f"Error: Config file not found: {args.config}", file=sys.stderr)
        print(
            f"Create a benchmarks.yaml file or use --config to specify a different path.",
            file=sys.stderr,
        )
        return 1

    # Set workspace dir if not specified
    workspace_dir = args.workspace_dir
    if workspace_dir is None:
        workspace_dir = args.cache_dir / "workspaces"

    # Create the FastAPI app
    try:
        app = create_app(
            config_file=args.config,
            data_file=args.data_file,
            cache_dir=args.cache_dir,
            workspace_dir=workspace_dir,
        )
    except Exception as e:
        logger.error(f"Failed to create application: {e}")
        return 1

    # Print banner
    if not args.quiet:
        print_banner(args.host, args.port, args.config, args.data_file, args.cache_dir)

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
