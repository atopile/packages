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
- Can publish via git/gh once builds + verify succeeded (guarded by default)
- Shows **Published ✅** status by polling the packages registry for the latest version (marks published when `0.14.x`)

## Requirements

- Python with [`uv`](https://github.com/astral-sh/uv)
- `ato` available on PATH **or** a sibling `../atopile/.venv` with `python -m atopile` available
- (Optional) GitHub CLI `gh` for publish automation
- (Optional) KiCad installed (for “Open in KiCad”)

## How the flow works

The review station runs a **multi-stage pipeline per package**, while keeping a cap on how many
packages are waiting for human attention.

### States (high-level)

- **queue**: waiting to be processed
- **building**: running `ato build` (single invocation; ato handles per-target concurrency internally)
- **verifying**: running `ato package verify -s`
- **awaiting_review**: build + verify finished (pass or fail) and the package is “ready for human”
- **approved**: reviewer clicked Approve (metadata only; does not stop background work)
- **pushing_branch / branch_pushed / pr_opened**: publish flow stages (git/gh)
- **error**: unexpected exception while processing

### “max-ready” throttle

`--max-ready` limits how many packages can be in “awaiting_review/approved” at once, so the UI doesn’t
fill up with hundreds of completed items while your machine keeps churning.

### Pause/Resume and “Do next”

- **Pause**: stops (or prevents) processing for that package until resumed
- **Do next**: pins the package to the front of the queue (useful when you want to review something now)

### What Publish does (safe by default)

Publishing is **server-side guarded** and only allowed once:

- **all build targets** finished with **rc=0**
- **verify** finished with **rc=0**

When you click **Publish**, the server will:

- Create/reset a branch named `package-update-<compiler-series>-<package>`
- Use a **git worktree** (so your current working branch is untouched)
- Copy **only** `packages/<package>/` into the worktree
- Rewrite `requires-atopile` to the chosen target (UI “Target atopile” field)
- Bump the package version (minor bump policy)
- Commit and **force-push** the branch (overwrites if it already exists)
- If `gh` is available and authenticated: open a PR to merge into `main` (no auto-merge)

### Unsafe override

If you need to test the git/gh plumbing even when builds are failing/incomplete, start the server with
`--publish-anyway`. This bypasses the publish guard.

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

### Auto-rebuilding CI-failing packages (enabled by default)

**By default**, the review station automatically rebuilds packages with failing CI.

On startup, the PR/CI poller:
- Queries GitHub once for all open PRs and their CI status
- Packages with `ci_conclusion == "failure"` that aren't queued/building are added to the build queue
- Packages are marked with `rebuilding_for_ci = true` for visual feedback
- **Runs once** to avoid GitHub API rate limiting

**Visual indicators:**
- 🔴 Red pulsing dot on the "CI" step in the status bar indicates rebuilding to fix CI failure
- Blue sliding animation appears when downloading CI logs from GitHub
- Package status follows normal flow: queue → building → verifying → awaiting_review

To **disable** this behavior:

```bash
uv run scripts/review_station/review_webui.py \
  --packages-root /Users/narayanpowderly/projects/packages/packages \
  --no-auto-enqueue-ci-failures \
  --jobs 4 \
  --max-ready 10 \
  --port 8787 \
  --kill-existing
```

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

### Publishing

Publishing is **enabled by default**, but the server blocks publish unless **all build targets**
and **verify** completed successfully (rc=0).

If you really need to bypass this guard (unsafe), start the server with `--publish-anyway`.

```bash
uv run scripts/review_station/review_webui.py \
  --packages-root /Users/narayanpowderly/projects/packages/packages \
  --jobs 4 \
  --max-ready 10 \
  --port 8787 \
  --publish-anyway \
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
