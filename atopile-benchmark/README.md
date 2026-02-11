# atopile Build Speed Benchmark Dashboard

A comprehensive benchmarking suite for measuring and visualizing atopile build performance across different versions.

## Features

- **Multi-Version Testing**: Benchmark different atopile versions (PyPI releases, git branches, or specific commits)
- **Package Benchmarks**: Test real-world packages from the atopile ecosystem
- **Multiple Build Modes**: Compare `ato build`, `ato build --keep-picked-parts`, and `ato build -t all`
- **Live Dashboard**: Real-time web interface with auto-refreshing results via WebSocket
- **Interactive Visualizations**:
  - Toggle between linear/log scales
  - Normalize times or show absolute values
  - Chronological or discrete version ordering
  - Enable/disable specific benchmarks
- **Isolated Environments**: Each atopile version runs in its own cached virtual environment
- **Persistent Results**: All benchmark results saved to JSON for historical analysis

## Quick Start

```bash
# Clone the repository
git clone https://github.com/your-org/atopile-benchmark.git
cd atopile-benchmark

# Install dependencies
uv sync

# Run the dashboard
uv run python -m atopile_benchmark
```

The dashboard will be available at `http://127.0.0.1:8080`

## Configuration

Edit `config/benchmarks.yaml` to customize:

### atopile Versions

```yaml
atopile_versions:
  - type: release
    version: "0.12.4"
    date: "2024-11-15"

  - type: branch
    version: "main"
    date: "2024-11-20"

  - type: commit
    version: "abc123def456"
    date: "2024-11-18"

  - type: local
    version: "~/dev/atopile"
    date: "2024-11-20"
```

### Package Benchmarks

```yaml
package_benchmarks:
  - name: indicator-leds
    package: atopile/indicator-leds
    source: https://github.com/atopile/packages
    enabled: true

  - name: my-package
    package: atopile/my-package
    enabled: false  # Disabled benchmarks are skipped
```

### Build Commands

```yaml
build_commands:
  - name: "default"
    command: "ato build"
    description: "Standard build"

  - name: "keep-picked-parts"
    command: "ato build --keep-picked-parts"
    description: "Skip part picking (faster rebuilds)"
```

## Usage

### Command-Line Interface

```bash
# Basic usage (uses config/benchmarks.yaml)
python -m atopile_benchmark

# Custom configuration file
python -m atopile_benchmark --config my_benchmarks.yaml

# Different port
python -m atopile_benchmark --port 9000

# Verbose logging
python -m atopile_benchmark --verbose

# Development mode with auto-reload
python -m atopile_benchmark --reload
```

### CLI Options

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--config` | `-c` | `config/benchmarks.yaml` | Path to configuration file |
| `--data-file` | `-d` | `data/benchmark_results.json` | Path to results JSON |
| `--cache-dir` | | `data/cache` | Directory for cached venvs |
| `--workspace-dir` | | `<cache-dir>/workspaces` | Directory for build workspaces |
| `--port` | `-p` | `8080` | Web server port |
| `--host` | `-H` | `127.0.0.1` | Host to bind to |
| `--verbose` | `-v` | | Enable debug logging |
| `--quiet` | `-q` | | Suppress non-error output |
| `--reload` | | | Enable auto-reload (dev) |

### Running Benchmarks

1. **Run All Benchmarks**: Click "Run All Benchmarks" in the dashboard
2. **Run Individual Benchmark**: Click "Run" button in the results table
3. **Monitor Progress**: Running benchmarks show a spinner and current phase
4. **Stop Benchmarks**: Click "Stop" to cancel running benchmarks
5. **View Results**: Completed benchmarks show build time or error

### Interpreting Results

**Results Table**:
- Rows: Each benchmark (package + build command combination)
- Columns: Each atopile version
- Green values: Successful build time in seconds
- Red: Failed build (hover for error message)
- Gray: Version incompatible with package
- Spinner: Currently running benchmark

**Result Statuses**:
- `success`: Build completed successfully
- `failure`: Build failed with error
- `stub`: Package not available, ran minimal build
- `incompatible`: Package requires different atopile version

## Architecture

```
atopile-benchmark/
├── atopile_benchmark/           # Main package
│   ├── __init__.py              # Public API exports
│   ├── __main__.py              # Entry point
│   ├── cli.py                   # CLI argument parsing
│   │
│   ├── core/                    # Core domain logic
│   │   ├── models.py            # BuildPhase, BenchmarkResult
│   │   ├── version_manager.py   # Version/venv management
│   │   ├── benchmark_runner.py  # Build execution
│   │   └── data_store.py        # Results persistence
│   │
│   ├── web/                     # Web server layer
│   │   ├── app.py               # FastAPI app factory
│   │   ├── websocket.py         # WebSocket manager
│   │   ├── orchestrator.py      # Benchmark orchestration
│   │   └── routes/              # API route handlers
│   │       ├── benchmarks.py    # /api/run/*, /api/running
│   │       ├── results.py       # /api/results/*
│   │       ├── config.py        # /api/config
│   │       ├── versions.py      # /api/versions/*
│   │       └── cache.py         # /api/cache/*
│   │
│   ├── utils/                   # Shared utilities
│   │   ├── config.py            # Config loading/saving
│   │   └── git.py               # Git date utilities
│   │
│   └── templates/               # Jinja2 templates
│       └── index.html
│
├── config/                      # Configuration files
│   └── benchmarks.yaml
│
├── data/                        # Runtime data (gitignored)
│   ├── benchmark_results.json
│   └── cache/
│       ├── venvs/               # Virtual environments
│       └── workspaces/          # Temporary workspaces
│
├── scripts/                     # Utility scripts
│   ├── check_status.sh
│   ├── open_dashboard.sh
│   ├── validate_config.py
│   └── show_cache.py
│
├── tests/                       # Test suite
│   ├── test_benchmark.py
│   └── test_infrastructure.py
│
├── pyproject.toml
└── README.md
```

### Data Flow

1. Configuration loaded from `config/benchmarks.yaml`
2. Version Manager ensures atopile versions are installed in isolated venvs
3. Benchmark Runner creates temporary workspaces, installs packages, and runs builds
4. Results stored in JSON file and broadcast to connected clients via WebSocket
5. Dashboard updates table and charts in real-time

## API Reference

### Benchmark Execution

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/run/all` | POST | Start all benchmarks |
| `/api/run/stop` | POST | Stop all running benchmarks |
| `/api/run/benchmark/{name}/version/{id}` | POST | Run single benchmark |
| `/api/running` | GET | Get currently running benchmarks |
| `/api/benchmarks` | GET | Get list of all benchmark names |

### Results

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/results` | GET | Get all results |
| `/api/results` | DELETE | Clear all results |
| `/api/results/matrix` | GET | Get results as benchmark x version matrix |
| `/api/results/summary` | GET | Get summary statistics |
| `/api/results/history/{name}` | GET | Get history for specific benchmark |

### Configuration

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/config` | GET | Get current configuration |
| `/api/config/reload` | POST | Reload config from file |
| `/api/versions` | GET | Get configured versions |
| `/api/versions` | POST | Add new version |
| `/api/versions/{type}/{value}` | DELETE | Remove version |

### Cache Management

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/cache/info` | GET | Get cache size and venv info |
| `/api/cache/cleanup` | POST | Clean up unused venvs |
| `/api/cache/venv/{name}` | DELETE | Remove specific venv |

## Development

### Running Tests

```bash
# Run all tests
uv run pytest

# Run specific test
uv run pytest tests/test_infrastructure.py

# Verbose output
uv run pytest -v
```

### Adding a New Package Benchmark

Edit `config/benchmarks.yaml`:

```yaml
package_benchmarks:
  - name: my-new-package
    package: atopile/my-new-package
    source: https://github.com/atopile/packages
    enabled: true
```

### Adding a New Build Command

```yaml
build_commands:
  - name: "my-custom-build"
    command: "ato build --my-custom-flag"
    description: "Build with custom options"
```

## Troubleshooting

**Benchmark fails with "version not found"**:
- Ensure the version exists on PyPI or GitHub
- Check the version string is correct
- Try running with `--verbose` to see installation logs

**Dashboard not updating**:
- Check browser console for WebSocket connection errors
- Ensure no firewall is blocking the port
- Try refreshing the page

**Out of disk space**:
- Use the cache cleanup API: `POST /api/cache/cleanup`
- Or manually: `rm -rf data/cache/venvs/`
- Results are safe in `data/benchmark_results.json`

**Build timing seems wrong**:
- First build of a version may be slower (package downloads)
- Ensure no other processes are consuming CPU
- Check if network latency affects package installation

**Package incompatible**:
- Some packages require specific atopile versions
- Check the package's `ato.yaml` for `requires-atopile` field
- Incompatible builds are marked separately from failures

## License

MIT License
