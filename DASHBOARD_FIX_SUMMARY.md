# Dashboard Build Queue Fix - Summary

## Problem Diagnosed

The Dashboard stopped building packages after only 29 out of 150 packages were processed. Investigation revealed two issues:

### Issue 1: Aggressive PR/Registry Checker (Primary Issue)
The background PR checker thread was **prematurely marking packages as "published" or "pr_opened"** when it found existing PRs or registry entries, **removing them from the build queue** before they could be built locally.

**Root Cause:**
- Packages start with status "not_started"
- Background thread `_check_existing_prs_background` runs continuously
- It queries GitHub for existing PRs and the registry for published packages
- When found, it **immediately** changes status to "published"/"pr_opened" and removes from queue
- The orchestrator only dispatches packages with status "not_started"
- Result: 121 packages were never built because they were marked as already done

**Code Location:** Lines 3136-3205 in `scripts/review_webui.py`

### Issue 2: Stuck Agent Without Timeout (Secondary Issue)
The ti-ina3221 package had an agent that was marked as `agent_working=True` since 7:45PM, even though the build finished (and failed) at 7:46PM. The agent never sent a "finished" message, leaving it in a stuck state indefinitely.

**Root Cause:**
- Agent sends "started" message when beginning work
- Agent should send "finished" message when done
- If agent encounters an error or exception, it may not send "finished"
- No timeout mechanism existed to detect and clear stuck agents
- While this didn't block other packages (contrary to initial hypothesis), it's still a problem

**Code Location:** Lines 3576-3580 in `scripts/review_webui.py`

## Solutions Implemented

### Solution 1: Don't Skip Unbuilt Packages (Lines 3136-3230)

**Changed Behavior:**
- PR/registry information is **always stored** when discovered
- Status is **only changed** if the package has been built locally at least once (`job.build_rc` is populated)
- Packages with status "not_started" are **never** removed from the queue by the PR checker
- Exception: Packages currently "building" or "verifying" can still be cancelled if already published

**Code Changes:**
```python
# BEFORE: Changed status immediately if PR found
if job.status in ("not_started", "building", "verifying"):
    job.status = "published"
    remove_from_queue()

# AFTER: Only change status if already built locally
if job.status in ("building", "verifying"):
    # Cancel ongoing builds if already published
    job.status = "published"
    remove_from_queue()
elif job.status not in ("not_started") and job.build_rc:
    # Package has been built locally, safe to mark as published
    job.status = "published"
    remove_from_queue()
# else: Keep in "not_started" and let it build
```

### Solution 2: Agent Watchdog Thread (Lines 2605-2660)

**New Feature:**
- New background thread `_agent_watchdog` runs every 30 seconds
- Monitors all packages for stuck agents
- An agent is considered stuck if:
  - `agent_working` is True
  - `agent_working_since` is more than 10 minutes ago
  - Package has `finished_at` timestamp (build is done)
- Automatically times out stuck agents by sending a "timeout" message

**Code Changes:**
```python
# New watchdog thread
def _agent_watchdog(self) -> None:
    AGENT_TIMEOUT_SECONDS = 600  # 10 minutes
    while not self._stop:
        # Find stuck agents
        for pkg_name, job in self._jobs.items():
            if job.agent_working and elapsed > AGENT_TIMEOUT_SECONDS:
                if job.finished_at:  # Build finished but agent still working
                    timeout_agent(pkg_name)
        time.sleep(30)

# Updated message handler to clear agent_working on timeout
if msg_type in ("finished", "error", "timeout"):
    job.agent_working = False
    job.agent_working_since = None
```

## Expected Results

1. **All 150 packages will now be built locally** before being marked as published
2. **Each package will have a health status** from the local build
3. **Stuck agents will automatically timeout** after 10 minutes instead of blocking indefinitely
4. **Dashboard will provide complete coverage** of all packages in the repository

## Testing

The fix has been:
- ✅ Syntax validated with `python3 -m py_compile`
- ⏳ Ready for runtime testing by restarting the Dashboard server

## Files Modified

- `scripts/review_webui.py` - 3 key changes:
  1. Registry checker logic (lines 3136-3230)
  2. PR checker logic (lines 3243-3280)
  3. Agent watchdog thread (lines 2605-2660)
  4. Agent message handler (lines 3576-3584)

## Next Steps

1. Restart the Dashboard server to apply changes
2. Monitor the build queue to verify all packages are being processed
3. Watch for any agents that trigger the 10-minute timeout
4. Verify that the build completes all 150 packages
