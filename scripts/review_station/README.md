# Package Review Station (atopile)

Local tooling to review and upgrade many packages efficiently, with a modern web UI.

## What it does

- Runs `ato build` for **all build targets** in each package
- Runs `ato package verify -s`
- Streams logs + metrics into a web dashboard
- Lets reviewers record feedback in a per-package `review.todo.md` (autosaved)
- Embeds:
  - KiCanvas board viewer
  - 3D model viewer (for `*.pcba.glb`)
- Supports sharding work across reviewers (`--shard-count/--shard-index`)
- Throttles queueing so only a limited number of packages are “ready for review” at a time (`--max-ready`)
- Can optionally publish via git/gh when enabled (`--enable-publish`)
- Shows **Published ✅** status by polling the packages registry for the latest version (marks published when `0.14.x`)

## Requirements

- Python with [`uv`](https://github.com/astral-sh/uv)
- `ato` available on PATH **or** a sibling `../atopile/.venv` with `python -m atopile` available
- (Optional) GitHub CLI `gh` for publish automation
- (Optional) KiCad installed (for “Open in KiCad”)

## Run

From the repo root (`/Users/narayanpowderly/projects/packages`):

```bash
uv run scripts/review_station/review_webui.py \
  --packages-root /Users/narayanpowderly/projects/packages/packages \
  --jobs 4 \
  --max-ready 10 \
  --port 8787 \
  --kill-existing
```

Then open `http://127.0.0.1:8787`.

### Run a single package (debug)

```bash
uv run scripts/review_station/review_webui.py \
  --packages-root /Users/narayanpowderly/projects/packages/packages \
  --package-regex '^(bosch-bme280)$' \
  --jobs 1 \
  --max-ready 1 \
  --port 8787 \
  --kill-existing
```

### Enable publish buttons

```bash
uv run scripts/review_station/review_webui.py \
  --packages-root /Users/narayanpowderly/projects/packages/packages \
  --jobs 4 \
  --max-ready 10 \
  --port 8787 \
  --enable-publish \
  --kill-existing
```

## Closed-loop perf tests (no user input)

These are “smoke/perf” regression tests that bring up the server in-process and
hammer key endpoints like `/api/state` to catch hangs and major slowdowns.

Run them using the atopile venv (it provides runtime deps like `typer`/`rich`):

```bash
cd /Users/narayanpowderly/projects/packages
source /Users/narayanpowderly/projects/atopile/.venv/bin/activate
python -W error::ResourceWarning -m unittest discover -s scripts/review_station/tests -p 'test_*.py'
```

### Sharding (multiple reviewers)

Example: split the package set into 4 shards; run shard 0:

```bash
uv run scripts/review_station/review_webui.py \
  --packages-root /Users/narayanpowderly/projects/packages/packages \
  --package-regex '.*' \
  --shard-count 4 \
  --shard-index 0
```

### Registry “Published ✅” checks

By default we poll the registry at `https://packages.atopileapi.com`.

We display both:

- The registry **published version**
- The registry **requires-atopile** (this is the important one to confirm “updated to 0.14.x”)

```bash
uv run scripts/review_station/review_webui.py --registry-refresh-seconds 60
```

### Open in Cursor

The UI has an **Open in Cursor** button which opens the build’s `.ato` entry file.
If your Cursor CLI is not `cursor`, pass:

```bash
uv run scripts/review_station/review_webui.py --cursor-cmd "open -a Cursor" ...
```

## Files / state

Each run writes a timestamped directory under `build/review_webui/<run-id>/`:

- `state.json`: live job state (polled by the UI)
- `<pkg>/review.todo.md`: reviewer notes + auto summary block (links to logs/PCBs)

## Static UI assets

The web UI files live in:

- `scripts/review_station/static/`

The server also supports the legacy path:

- `scripts/review_webui_static/` (deprecated)
