# atopile Build Speed Benchmark Dashboard

A comprehensive benchmarking suite for measuring and visualizing atopile build performance across different versions.

## Features

- **Multi-Version Testing**: Benchmark different atopile versions (PyPI releases, git branches, or specific commits)
- **Package Benchmarks**: Test real-world packages from the atopile ecosystem
- **Multiple Build Modes**: Compare `ato build`, `ato build --keep-picked-parts`, and `ato build -t all`
- **Live Dashboard**: Real-time web interface with auto-refreshing results
- **Interactive Visualizations**:
  - Toggle between linear/log scales
  - Normalize times or show absolute values
  - Chronological or discrete version ordering
  - Enable/disable specific benchmarks
- **Isolated Environments**: Each atopile version runs in its own cached virtual environment
- **Persistent Results**: All benchmark results saved to JSON for historical analysis

## Quick Start

### Installation

```bash
# Clone or navigate to the repository
cd atopile-benchmark

# Install dependencies
uv sync

# Run the dashboard
uv run python main.py
```

The dashboard will be available at `http://127.0.0.1:8080`

### Configuration

Edit `benchmarks.yaml` to customize:

1. **atopile Versions**: Add/remove versions to test
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
       version: "/Users/you/repos/atopile"
       # date is optional; if omitted the dashboard will infer it where possible
   ```

2. **Package Benchmarks**: Add/remove packages
   ```yaml
   package_benchmarks:
     - name: indicator-leds
       package: atopile/indicator-leds
       source: https://github.com/atopile/packages
       enabled: true
   ```

3. **Build Commands**: Customize build variations
   ```yaml
   build_commands:
     - name: "default"
       command: "ato build"
       description: "Standard build"
   ```

4. **Optional: skip `ato add` and use a local packages checkout**

If you already have the `atopile/packages` repo checked out locally (or you’re offline / behind a firewall),
you can copy packages directly from disk instead of downloading them via `ato add`:

```yaml
skip_ato_add: true
local_packages_root: "/Users/you/repos/packages/packages"
```

## Usage

### Starting the Dashboard

```bash
# Basic usage
uv run python main.py

# Custom configuration
uv run python main.py --config my_benchmarks.yaml --port 9000

# Verbose logging
uv run python main.py --verbose

# Development mode with auto-reload
uv run python main.py --reload
```

### Command-Line Options

- `--config PATH`: Path to benchmarks configuration (default: `benchmarks.yaml`)
- `--data-file PATH`: Path to results JSON file (default: `benchmark_results.json`)
- `--cache-dir PATH`: Directory for cached venvs (default: `benchmark_cache`)
- `--workspace-dir PATH`: Directory for build workspaces (default: `benchmark_cache/workspaces`)
- `--port PORT`: Web server port (default: `8080`)
- `--host HOST`: Host to bind to (default: `127.0.0.1`)
- `--verbose, -v`: Enable verbose logging
- `--reload`: Enable auto-reload for development

### Running Benchmarks

1. **Run All Benchmarks**: Click "Run All Benchmarks" in the dashboard
2. **Run Individual Benchmark**: Click "Run" button in the results table for a specific benchmark/version combination
3. **Monitor Progress**: Running benchmarks show a spinner and elapsed time
4. **View Results**: Completed benchmarks show build time (green) or error (red ❌)

### Interpreting Results

**Results Table**:
- Rows: Each benchmark (package + build command combination)
- Columns: Each atopile version
- Green values: Successful build time in seconds
- Red ❌: Failed build (hover for error message)
- Spinner: Currently running benchmark

**Chart Controls**:
- **Y-Axis**:
  - Linear/Log Scale: Toggle between linear and logarithmic Y-axis
  - Show Seconds/Normalized: Toggle between absolute time and percentage of baseline
- **X-Axis**:
  - Discrete/Chronological: Toggle between evenly-spaced versions or chronological timeline
  - Linear/Log Scale: Toggle X-axis scale (when in chronological mode)

## Architecture

### Components

1. **Version Manager** (`version_manager.py`): Manages isolated virtual environments for each atopile version
2. **Benchmark Runner** (`benchmark_runner.py`): Executes builds and collects timing data
3. **Data Store** (`data_store.py`): Persists results to JSON and provides query interface
4. **Dashboard** (`dashboard.py`): FastAPI web server with WebSocket support for live updates
5. **CLI** (`cli.py`): Command-line interface and configuration

### Data Flow

1. Configuration loaded from `benchmarks.yaml`
2. Version Manager ensures atopile versions are installed in isolated venvs
3. Benchmark Runner creates temporary workspaces, installs packages, and runs builds
4. Results stored in JSON file and broadcast to connected clients via WebSocket
5. Dashboard updates table and charts in real-time

### Caching

- **Virtual Environments**: Cached in `benchmark_cache/venvs/` (one per atopile version)
- **Workspaces**: Temporary, cleaned up after each benchmark
- **Results**: Persisted in `benchmark_results.json`

## Development

### Project Structure

```
atopile-benchmark/
├── atopile_benchmark/
│   ├── __init__.py
│   ├── version_manager.py    # Virtual environment management
│   ├── benchmark_runner.py   # Benchmark execution
│   ├── data_store.py          # Data persistence
│   ├── dashboard.py           # Web server and API
│   ├── cli.py                 # Command-line interface
│   └── templates/
│       └── index.html         # Dashboard UI
├── benchmarks.yaml            # Configuration
├── benchmark_results.json     # Results (generated)
├── benchmark_cache/           # Cached venvs (generated)
├── main.py                    # Entry point
├── pyproject.toml            # Dependencies
└── README.md
```

### Adding New Features

**New Build Command**:
Edit `benchmarks.yaml` and add to `build_commands`:
```yaml
- name: "custom-flag"
  command: "ato build --my-custom-flag"
  description: "Build with custom flag"
```

**New Package**:
Edit `benchmarks.yaml` and add to `package_benchmarks`:
```yaml
- name: my-package
  package: atopile/my-package
  source: https://github.com/atopile/packages
  enabled: true
```

**New atopile Version**:
Edit `benchmarks.yaml` and add to `atopile_versions`:
```yaml
- type: release
  version: "0.13.0"
  date: "2024-12-01"
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
- Clean up cached venvs: `rm -rf benchmark_cache/venvs/`
- Results are safe in `benchmark_results.json`

**Build timing seems wrong**:
- First build of a version may be slower (package downloads)
- Ensure no other processes are consuming CPU
- Check if network latency affects package installation

## License

MIT License
