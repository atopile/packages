# Human Input For Package Review Station

## Overview
The Package Review Station is a web dashboard for reviewing, building, and publishing atopile packages. It provides a centralized interface for managing package updates across a large monorepo.

---

## 0. Main Workflow
* When the app opens
    * Get the latest code from origin/main from https://github.com/atopile/packages
    * Identify all available packages by parsing the ato.yaml files in packages/packages
    * For each identified package
    * Check the package server for the latest published version of the package, and the latest version of the package
    * Check if there are any open branches or PRs related to this package
    * Run ato build for every available package
* The most important indicator flag is the 'pass' or 'fail' flag that will show the result of the latest ato build
* Based on this latest build status, we can identify which packages need attention.

## 1. Frontend Display

### 1.1 Package List (Left Sidebar)
- [ ] Package name display
- [ ] Status icon/badge per package (queued, building, verifying, error, warning, review, pr_opened, published)
- [ ] Error count badge (red)
- [ ] Warning count badge (yellow)
- [ ] CI status indicator (passing/failing/pending)
- [ ] "Requires 0.14.x" tag for packages updated to new compiler
- [ ] "Published" tag for packages already in registry
- [ ] Filter text input
- [ ] Sort toggle (A-Z / recent activity)
- [ ] Status filter buttons (All, Recent, Build, Err, Warn, Review, PR, CI ✗, Done, Queue, Agent, Help)
- [ ] Visual highlight for selected package
- [ ] Live update of status as builds progress

### 1.2 Header Bar
- [ ] Package title (currently selected)
- [ ] Package subtitle (path/identifier)
- [ ] Tab buttons: Viewer / Diff
- [ ] Theme toggle (Auto/Dark/Light)
- [ ] Reviewer name input
- [ ] Target atopile version input (e.g., ^0.14.0)
- [ ] GitHub refresh button with sync status indicator
- [ ] Frozen build mode indicator

### 1.3 Status & Summary Pane
- [ ] Build stage progress indicator (stages: queued → building → verifying → review → pr_opened → ci_running → published)
- [ ] Per-build-target status table:
  - Build name
  - Return code (pass/fail)
  - Error count
  - Warning count
  - Build duration (seconds)
- [ ] Live elapsed timer during active builds
- [ ] Current build step display (e.g., "picker", "post-instantiation-setup")
- [ ] Verify stage status and duration
- [ ] Overall timing: start time, end time, total duration
- [ ] PR URL link (if published)
- [ ] CI status and conclusion

### 1.4 Layout Pane (KiCanvas)
- [ ] KiCanvas PCB viewer embed
- [ ] Build target dropdown selector
- [ ] Auto-load `.kicad_pcb` file for selected build
- [ ] Zoom/pan controls

### 1.5 Issues Pane
- [ ] Aggregated list of errors and warnings from all logs
- [ ] Issue type indicator (error/warning)
- [ ] Source label (which log/build step)
- [ ] Line number reference
- [ ] Click-to-jump to log entry
- [ ] Filter dropdown (All / Errors only / Warnings only / CI only)
- [ ] Search input for filtering issues
- [ ] CI logs download progress indicator
- [ ] "Show Logs" toggle button

### 1.6 Raw Logs Pane (hidden by default)
- [ ] Stage selector dropdown (build/verify/other)
- [ ] Log file selector dropdown
- [ ] Search input for filtering log content
- [ ] Pre-formatted log content display
- [ ] JSONL logs formatted for readability (timestamp, level, logger, message)
- [ ] ANSI color code stripping
- [ ] Truncation for very large logs (>1MB)

### 1.7 Feedback/TODO Pane
- [ ] Textarea for reviewer notes
- [ ] Autosave functionality
- [ ] "Open Notes" button to open in Cursor
- [ ] "Copy Agent Instructions" button
- [ ] Agent messages display area
- [ ] Clear messages button
- [ ] Resolve Help button (for help-flagged packages)

### 1.8 3D Model Pane
- [ ] model-viewer embed for STEP files
- [ ] Auto-load `.glb`/`.step` file for selected build
- [ ] Camera controls

### 1.9 Diff Pane (alternate view)
- [ ] Git diff display between working tree and main branch
- [ ] Syntax-highlighted diff rendering
- [ ] Diff metadata (files changed, insertions, deletions)
- [ ] Refresh button

---

## 2. Backend Service Connections

### 2.1 Build System (`ato build`)
- [ ] Execute `ato build -t all` for package builds
- [ ] Support `--frozen` flag (fail if layout changes needed)
- [ ] Support `--keep-picked-parts` flag (use existing part picks)
- [ ] Support `--verbose` for detailed logging
- [ ] Support `--jobs N` for parallel build targets
- [ ] Support `--exclude-target datasheets`
- [ ] Parse build output logs (JSONL format)
- [ ] Extract errors/warnings from logs
- [ ] Track per-target build times from `summary.json`

### 2.2 Verify System (`ato package verify`)
- [ ] Execute `ato package verify -s` (strict mode)
- [ ] Parse verify output for errors/warnings
- [ ] Track verify duration and return code

### 2.3 Log Management
- [ ] Store logs in `build/logs/` directory structure:
  - `archive/<timestamp>/<build_name>/*.jsonl` (per-stage logs)
  - `latest/` symlink to most recent archive
  - `summary.json` with build statistics
- [ ] Review station logs in run directory:
  - `build.log` (combined stdout/stderr)
  - `verify.log`
- [ ] CI logs downloaded to `build/ci_logs/latest/<target>/`

### 2.4 Package Registry
- [ ] Query `packages.atopileapi.com` for package metadata
- [ ] Check if package is published
- [ ] Get latest published version
- [ ] Get `requires_atopile` version from registry
- [ ] Detect packages updated to 0.14.x

### 2.5 GitHub Integration
- [ ] `gh pr list` to find existing PRs for packages
- [ ] `gh pr view` to get PR details (state, URL, checks)
- [ ] `gh pr checks` to get CI status
- [ ] `gh run download` to fetch CI artifacts/logs
- [ ] `gh pr create` to create new PRs
- [ ] `gh workflow run` to trigger CI re-runs (if supported)
- [ ] Cache PR data with periodic refresh
- [ ] Manual refresh button

---

## 3. Backend Version Control (Git Operations)

### 3.1 Worktree Management
- [ ] Create temporary worktrees for publishing (`_publish_worktrees/`)
- [ ] Reuse existing worktrees when possible
- [ ] Handle "cannot force update branch" errors gracefully
- [ ] Cleanup worktrees after operations
- [ ] `git worktree prune` for stale metadata

### 3.2 Branch Operations
- [ ] Create/reset branch: `package-update-<series>-<package>`
- [ ] Checkout from `origin/main` or `main`
- [ ] Force-push with `--force-with-lease`

### 3.3 Sync from Main
- [ ] `git fetch origin`
- [ ] `git show origin/main:packages/<pkg>/` to read files
- [ ] Copy files from main branch to working tree
- [ ] Preserve local `build/` and `review.todo.md`

### 3.4 Pull from PR
- [ ] Fetch PR branch
- [ ] Checkout package files from PR branch to working tree

### 3.5 Push to PR
- [ ] Fetch existing PR branch
- [ ] Create worktree on PR branch
- [ ] Copy updated package files
- [ ] Commit and force-push

### 3.6 Diff Operations
- [ ] `git diff origin/main -- packages/<pkg>/` for changes
- [ ] `git diff --stat` for summary

### 3.7 Timeout Handling
- [ ] 60 second timeout for git commands
- [ ] 120 second timeout for gh commands
- [ ] Graceful error messages on timeout

---

## 4. User Interface Commands (Buttons/Actions)

### 4.1 Package Actions
- [ ] **Restart (frozen)**: Rebuild with `--frozen --keep-picked-parts` (fail if layout changes)
- [ ] **Rebuild**: Rebuild without frozen (allow layout changes, re-pick parts)
- [ ] **Open in Cursor**: Open package directory in Cursor IDE
- [ ] **Open in KiCad**: Open PCB file in KiCad
- [ ] **Approve**: Mark package as reviewed/approved
- [ ] **Unapprove**: Remove approval

### 4.2 Publishing Actions
- [ ] **Publish**: Create new PR branch, commit, push, create/update PR
- [ ] **Uprev**: Bump version and create PR (quick publish)
- [ ] **Push to PR**: Push local changes to existing PR branch
- [ ] **Pull from PR**: Pull PR branch changes to local working tree
- [ ] **GitHub**: Open PR URL in browser

### 4.3 Sync Actions
- [ ] **Sync from Main**: Checkout package files from origin/main
- [ ] **Rerun CI**: Trigger CI workflow re-run for PR

### 4.4 View Actions
- [ ] **Show Logs / Hide Logs**: Toggle raw logs pane
- [ ] **Refresh Diff**: Reload diff from git
- [ ] **Theme Toggle**: Cycle through Auto/Dark/Light themes

### 4.5 List Actions
- [ ] **Filter**: Text search in package list
- [ ] **Sort Toggle**: Switch between A-Z and recent activity
- [ ] **Status Filters**: Filter by package status category

### 4.6 GitHub Sync
- [ ] **⟳ GitHub**: Manual refresh of PR cache and registry data

---

## 5. State Management

### 5.1 Per-Package Job State
- [ ] Package name and directory path
- [ ] Build target names
- [ ] Build status per target (return code, errors, warnings, duration)
- [ ] Verify status (return code, errors, warnings, duration)
- [ ] Overall status (queued, building, verifying, error, warning, review, pr_opened, published)
- [ ] Timestamps (started_at, finished_at)
- [ ] Current build step (for live display)
- [ ] Approval info (approved_by, approved_at)
- [ ] Publish info (branch, PR URL, error)
- [ ] CI status and conclusion
- [ ] Registry info (published, latest_version, requires_atopile)

### 5.2 Global State
- [ ] Selected package
- [ ] Selected build target
- [ ] Frozen mode flag
- [ ] Publish anyway flag
- [ ] Server origin URL
- [ ] Build queue order

### 5.3 Persistence
- [ ] State saved to `state.json` in run directory
- [ ] Todo notes saved per-package to `review.todo.md`
- [ ] Auto-section in todo with build status

---

## 6. Known Issues / TODO

### 6.1 Currently Broken
- [ ] (List any known broken features here)

### 6.2 Missing Features
- [ ] (List any desired features not yet implemented)

### 6.3 Performance Issues
- [ ] (List any performance concerns)

---

## 7. Notes

(Add any additional notes, context, or decisions here)
