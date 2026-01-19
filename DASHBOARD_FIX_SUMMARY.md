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

### Issue 2: Build Cancellation Bug (FIXED in v2)
The first fix attempt introduced a bug where running builds were being cancelled when PRs were found.
The code was setting `should_update_status = True` for "building" packages and then calling
`self._mp_cancel[pkg_name] = True`, which killed the worker processes. The results never came back
properly, leaving packages stuck in "building" state forever.

### Issue 3: Stuck Agent Without Timeout
The ti-ina3221 package had an agent marked as `agent_working=True` after the build finished.
No timeout mechanism existed to detect and clear stuck agents.

## Solutions Implemented (v2)

### Solution 1: Don't Skip Unbuilt Packages, Don't Cancel Running Builds

**Changed Behavior:**
- PR/registry information is **always stored** when discovered
- Status is **only changed** if the package has been built locally (`job.build_rc` is populated)
- Packages with status "not_started" are **never** removed from the queue
- **CRITICAL FIX**: Running builds ("building", "verifying") are **never** cancelled or interrupted

**Code Changes:**
```python
# BEFORE (buggy): Cancelled running builds
if job.status in ("building", "verifying"):
    should_update_status = True  # This caused cancellation!

# AFTER (fixed): Never interrupt running builds
if job.status == "branch_pushed" and cached_pr.get("url"):
    should_update_status = True
elif job.status not in ("not_started", "building", "verifying") and job.build_rc:
    # Package completed locally, safe to update status
    should_update_status = True
# No more build cancellation code
```

### Solution 2: Agent Watchdog Thread (Lines 2605-2660)

**New Feature:**
- New background thread `_agent_watchdog` runs every 30 seconds
- Monitors all packages for stuck agents
- Automatically times out stuck agents after 10 minutes

## Expected Results

1. **All packages will now build to completion** without being cancelled
2. **Each package will have a health status** from the local build
3. **Stuck agents will automatically timeout** after 10 minutes

## Files Modified

- `scripts/review_webui.py` - Key changes:
  1. Registry checker logic - removed build cancellation
  2. PR checker logic - removed build cancellation
  3. Agent watchdog thread
  4. Agent message handler

## Next Steps

1. Restart the Dashboard server to apply changes
2. Monitor the build queue to verify builds complete normally
3. Verify that packages finish and move to the next status
