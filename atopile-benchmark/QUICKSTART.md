# Quick Start Guide

## Getting Started in 3 Steps

### 1. Install Dependencies

```bash
uv sync
```

### 2. Start the Dashboard

```bash
uv run python main.py
```

The dashboard will be available at: http://127.0.0.1:8080

### 3. Run Benchmarks

Open your browser to http://127.0.0.1:8080 and click "Run All Benchmarks"

## What Happens Next?

The system will:

1. **Install atopile versions** - Creates isolated virtual environments for each version
2. **Run benchmarks** - Tests each package with different build commands
3. **Display results** - Updates the table and chart in real-time

## Understanding the Dashboard

### Results Table
- **Rows**: Each benchmark (package + build command)
- **Columns**: Each atopile version
- **Green numbers**: Build succeeded (time in seconds)
- **Red ❌**: Build failed (hover for error details)
- **Spinner**: Currently building

### Interactive Chart
- **Enable/Disable Benchmarks**: Check/uncheck boxes above the chart
- **Y-Axis Controls**:
  - Linear/Log Scale: Toggle Y-axis scale
  - Seconds/Normalized: Show absolute time or percentage of baseline
- **X-Axis Controls**:
  - Discrete/Chronological: Evenly spaced versions or timeline view
  - Linear/Log Scale: X-axis scale (for chronological mode)

## Customizing Benchmarks

Edit `benchmarks.yaml` to:

### Add a new package:
```yaml
package_benchmarks:
  - name: my-new-package
    package: atopile/my-new-package
    source: https://github.com/atopile/packages
    enabled: true
```

### Add a new version:
```yaml
atopile_versions:
  - type: release
    version: "0.13.0"
    date: "2024-12-01"

  - type: branch
    version: "development"
    date: "2024-12-15"

  - type: commit
    version: "abc123def456789"
    date: "2024-12-10"

  # Local development checkout (installed into the benchmark venv with `pip install -e`)
  - type: local
    version: "/Users/you/repos/atopile"
    # date is optional
```

### Add a new build command:
```yaml
build_commands:
  - name: "verbose"
    command: "ato build --verbose"
    description: "Build with verbose output"
```

### Optional: skip `ato add` and use a local packages checkout

If you already have the `atopile/packages` repo checked out locally (or you’re offline / behind a firewall),
you can copy packages directly from disk instead of downloading them via `ato add`:

```yaml
skip_ato_add: true
local_packages_root: "/Users/you/repos/packages/packages"
```

## Troubleshooting

**Dashboard won't start**: Check that port 8080 is available
```bash
# Use a different port
uv run python main.py --port 9000
```

**Benchmarks fail**: Check logs with verbose mode
```bash
uv run python main.py --verbose
```

**Out of disk space**: Clean cached environments
```bash
rm -rf benchmark_cache/venvs/
# Results are preserved in benchmark_results.json
```

## Advanced Usage

### Export Results
Results are automatically saved to `benchmark_results.json`. You can process this file with any JSON tool.

### Run Specific Benchmarks
Click the "Run" button on any empty cell in the results table to run that specific benchmark/version combination.

### Clear Results
```bash
rm benchmark_results.json
```

Then restart the dashboard for a fresh start.

## Next Steps

- Monitor build times across versions
- Identify performance regressions
- Test new packages before release
- Validate optimization efforts

For full documentation, see [README.md](README.md)
