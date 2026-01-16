/* "Reacty" (stateful, declarative-ish) UI without external deps.
 *
 * - Left: package list w/ status + warnings/errors + timing
 * - Right: selected package details, KiCanvas view, todo editor, open/approve actions
 * - Live refresh: polls /api/state + selected package detail
 */

const $ = (sel) => document.querySelector(sel);
const el = (tag, attrs = {}, children = []) => {
  const n = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k === "class") n.className = v;
    else if (k === "text") n.textContent = v;
    else if (k.startsWith("on") && typeof v === "function") n.addEventListener(k.slice(2).toLowerCase(), v);
    else n.setAttribute(k, v);
  }
  for (const c of children) n.append(c);
  return n;
};

// Strip auto-generated content from todo for cleaner display
const AUTO_BEGIN = "<!-- AUTO:BEGIN -->";
const AUTO_END = "<!-- AUTO:END -->";
const stripAutoContent = (text) => {
  if (!text) return "";
  const beginIdx = text.indexOf(AUTO_BEGIN);
  const endIdx = text.indexOf(AUTO_END);
  if (beginIdx === -1 || endIdx === -1) return text;
  // Remove the auto section and any trailing whitespace
  const before = text.slice(0, beginIdx).trimEnd();
  const after = text.slice(endIdx + AUTO_END.length).trimStart();
  return (before + (before && after ? "\n\n" : "") + after).trim();
};

// Highlight a specific line in log content for inline log viewer
const highlightLogLine = (logText, lineNum) => {
  if (!logText) return "<span class='muted'>No content</span>";
  const lines = logText.split("\n");
  const escapeHtml = (str) => str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");

  return lines.map((line, i) => {
    const lineNumber = i + 1;
    const isHighlighted = lineNum && lineNumber === lineNum;
    const escapedLine = escapeHtml(line);
    const lineNumSpan = `<span class="logLineNum">${String(lineNumber).padStart(4)}</span>`;
    if (isHighlighted) {
      return `<div class="logLine highlighted">${lineNumSpan}${escapedLine}</div>`;
    }
    return `<div class="logLine">${lineNumSpan}${escapedLine}</div>`;
  }).join("");
};

const state = {
  runDir: null,
  updatedAt: null,
  packages: {}, // name -> JobState
  queue: [],
  filter: "",
  statusFilter: "all", // "all", "building", "error", "warning", "review", "queue"
  sortOrder: "asc", // "asc" (A-Z) or "desc" (Z-A)
  selected: null,
  selectedDetail: null, // { job, todo, excerpts }
  selectedBuild: null,
  selectedLogStage: "build",
  selectedLog: null,
  selectedLogContent: "",
  logIndex: null,
  logIndexFetchedAt: 0,
  logFetchedAt: 0,
  kvKey: null,
  mvKey: null,
  publish: {
    commitMessage: "",
    diff: "",
    lastResult: null,
    error: null,
  },
  dirtyTodo: false,
  lastTodoSavedAt: null,
  diff: "",
  diffInfo: null,
  viewTab: "viewer", // "viewer" | "diff"
  lastViewTab: null,
  // Issues panel
  issues: null, // { issues: [], error_count, warning_count, total_count }
  issuesFetchedAt: 0,
  issueFilter: "all", // "all" | "errors" | "warnings"
  issueSearch: "",
  showLogs: false, // Toggle between issues and raw logs view
  expandedIssue: null, // Index of currently expanded issue (for inline log viewer)
  expandedIssueLog: "", // Log content for expanded issue
  expandedIssueLoading: false,
  expandedIssueScroll: 0, // Preserved scroll position for expanded issue log
  issuesListScroll: 0, // Preserved scroll position for the issues list container
};

// Debug / instrumentation (client-side)
const debugEnabled = (() => {
  try {
    const p = new URLSearchParams(location.search || "");
    if (p.get("debug") === "1") return true;
    return (localStorage.getItem("review_station_debug") || "") === "1";
  } catch {
    return false;
  }
})();

const debug = {
  enabled: debugEnabled,
  marks: [],
  lastRefreshMs: 0,
  lastRenderListMs: 0,
  lastRenderRightMs: 0,
  eventLoopLagMs: 0,
  log(name, ms) {
    if (!this.enabled) return;
    this.marks.push({ t: Date.now(), name, ms });
    if (this.marks.length > 200) this.marks.shift();
    if (ms > 250) console.warn(`[review-station][slow] ${name} ${ms.toFixed(1)}ms`);
  },
};
window.__reviewStationDebug = debug;

function measure(name, fn) {
  const t0 = performance.now();
  const r = fn();
  const ms = performance.now() - t0;
  debug.log(name, ms);
  return r;
}

function updateDebugHud() {
  const hud = $("#debugHud");
  if (!hud) return;
  if (!debug.enabled) {
    hud.style.display = "none";
    return;
  }
  hud.style.display = "inline-flex";
  hud.textContent = `dbg • refresh ${debug.lastRefreshMs.toFixed(0)}ms • list ${debug.lastRenderListMs.toFixed(0)}ms • right ${debug.lastRenderRightMs.toFixed(0)}ms • lag ${debug.eventLoopLagMs.toFixed(0)}ms`;
}

// Event-loop lag monitor (detect "frozen" UI)
if (debug.enabled) {
  let last = performance.now();
  setInterval(() => {
    const now = performance.now();
    const drift = Math.max(0, now - last - 500);
    debug.eventLoopLagMs = drift;
    last = now;
    updateDebugHud();
  }, 500);
}

function applyTheme(mode) {
  // mode: "auto" | "dark" | "light"
  const root = document.documentElement;
  if (mode === "light") root.setAttribute("data-theme", "light");
  else if (mode === "dark") root.setAttribute("data-theme", "dark");
  else root.removeAttribute("data-theme");
}

function getThemeMode() {
  const v = (localStorage.getItem("review_station_theme") || "").trim();
  return v || "auto";
}

function setThemeMode(mode) {
  localStorage.setItem("review_station_theme", mode);
  applyTheme(mode);
  const btn = $("#themeBtn");
  if (btn) btn.textContent = `Theme: ${mode[0].toUpperCase()}${mode.slice(1)}`;
}

function initTheme() {
  // Default: auto (follow system). Persisted override if set.
  const mode = getThemeMode();
  applyTheme(mode);
  const btn = $("#themeBtn");
  if (btn) btn.textContent = `Theme: ${mode[0].toUpperCase()}${mode.slice(1)}`;
  // If on auto, refresh when system theme changes.
  try {
    const mq = window.matchMedia("(prefers-color-scheme: dark)");
    mq.addEventListener("change", () => {
      if (getThemeMode() === "auto") applyTheme("auto");
    });
  } catch {}
}

const statusLabel = (s) => ({
  not_started: "queue",
  building: "building",
  verifying: "verifying",
  awaiting_review: "waiting approval",
  approved: "approved / ready to publish",
  pushing_branch: "pushing branch",
  branch_pushed: "pushed branch",
  published: "published",
  paused: "paused",
  skipped: "paused",
  error: "error",
  needs_input: "needs help",
}[s] || s);

const statusPillClass = (s) => {
  if (s === "approved" || s === "published") return "good";
  if (s === "awaiting_review") return "blue";
  if (s === "building" || s === "verifying" || s === "pushing_branch") return "purple";
  if (s === "branch_pushed") return "blue";
  if (s === "paused" || s === "skipped") return "warn";
  if (s === "error") return "bad";
  if (s === "needs_input") return "urgent";
  return "";
};

const sum = (obj) => Object.values(obj || {}).reduce((a, b) => a + (Number(b) || 0), 0);

function escHtml(s) {
  return String(s)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function pillHtml(kind, text) {
  return `<span class="pill ${kind}"><span class="dot"></span><span>${escHtml(text)}</span></span>`;
}

function kvRowHtml(k, v) {
  if (v == null || v === "") return "";
  return `<div class="sumRow"><div class="sumKey">${escHtml(k)}</div><div class="sumVal">${escHtml(v)}</div></div>`;
}

function summaryHtml(job, { totalWarn, totalErr, totalSecs }) {
  // Progress bar stages
  const stageDefs = [
    { key: "queue", label: "queue" },
    { key: "building", label: "build" },
    { key: "verifying", label: "verify" },
    { key: "waiting", label: "waiting approval" },
    { key: "approved", label: "approved" },
    { key: "pushed", label: "pushed branch" },
    { key: "pr", label: "PR open" },
    { key: "ci", label: "CI" },
    { key: "published", label: "published" },
  ];

  const stageIndexFor = () => {
    if (job.registry_updated_014) return 8;
    if (job.published_pr_url) return 6;
    if (job.published_branch) return 7; // assume CI after push until registry says published
    if (job.status === "pushing_branch" || job.status === "branch_pushed" || job.status === "pr_opened") return 5;
    if (job.approved_by) return 4;
    // If verify ran, park the progress at verify (failure) or waiting approval (success).
    if (job.verify_rc != null) return Number(job.verify_rc) === 0 ? 3 : 2;
    if (job.status === "awaiting_review") return 3;
    if (job.status === "verifying") return 2;
    // If any build results exist, we've reached the build stage.
    if (job.build_rc && Object.keys(job.build_rc).length) return 1;
    if (job.status === "building") return 1;
    return 0;
  };
  const idx = stageIndexFor();
  const pct = (idx / (stageDefs.length - 1)) * 100;

  const stageClassFor = (key, i) => {
    // Compute stage classes from per-step outcomes, not overall job status.
    // This avoids "everything red" when a later stage fails.

    const hasAnyBuild = job.build_rc && Object.keys(job.build_rc).length;
    const anyBuildFail = hasAnyBuild && Object.values(job.build_rc).some((v) => Number(v) !== 0);
    const anyBuildWarn = job.build_warn && Object.values(job.build_warn).some((v) => Number(v) > 0);

    const verifyDone = job.verify_rc != null;
    const verifyFail = verifyDone && Number(job.verify_rc) !== 0;
    const verifyWarn = verifyDone && Number(job.verify_rc) === 0 && Number(job.verify_warn || 0) > 0;

    if (key === "queue") {
      return job.started_at ? "done" : (i === idx ? "active" : "");
    }
    if (key === "building") {
      if (job.status === "building") return "active";
      if (anyBuildFail) return "err";
      if (anyBuildWarn) return "warn";
      if (hasAnyBuild) return "done";
      return i < idx ? "done" : (i === idx ? "active" : "");
    }
    if (key === "verifying") {
      if (job.status === "verifying") return "active";
      if (verifyFail) return "err";
      if (verifyWarn) return "warn";
      if (verifyDone && Number(job.verify_rc) === 0) return "done";
      return i < idx ? "done" : (i === idx ? "active" : "");
    }
    // Remaining stages use the generic progress position.
    return i < idx ? "done" : (i === idx ? "active" : "");
  };

  const prog = `
    <div class="prog">
      <div class="progTrack"><div class="progFill" style="width:${pct}%;"></div></div>
      <div class="progSteps">
        ${stageDefs.map((s, i) => {
          const cls = stageClassFor(s.key, i);
          return `<div class="progStep ${cls}" title="${escHtml(s.label)}"><span class="progDot"></span><span class="progLabel">${escHtml(s.label)}</span></div>`;
        }).join("")}
      </div>
    </div>
  `;

  const pills = [];
  pills.push(pillHtml(statusPillClass(job.status), statusLabel(job.status)));
  if (job.approved_by) pills.push(pillHtml("good", `approved: ${job.approved_by}`));
  if (totalErr) pills.push(pillHtml("bad", `${totalErr} errors`));
  if (totalWarn) pills.push(pillHtml("warn", `${totalWarn} warnings`));
  if (totalSecs) pills.push(pillHtml("neutral", `${totalSecs.toFixed(1)}s`));

  // Only show publish-related info not displayed elsewhere
  const rows = [];
  if (job.publish_error) rows.push(kvRowHtml("publish error", job.publish_error));
  if (job.published_pr_url) rows.push(kvRowHtml("PR", job.published_pr_url));

  // Build targets table (similar to ato build CLI output)
  const buildNames = job.build_names || [];
  let buildTable = "";
  if (buildNames.length > 0) {
    // Parse per-build progress if available (JSON format: {"build_name": "status"})
    let perBuildProgress = {};
    if (job.build_progress) {
      try {
        const parsed = JSON.parse(job.build_progress);
        if (typeof parsed === "object" && parsed !== null) {
          perBuildProgress = parsed;
        }
      } catch {
        // Not JSON - legacy single string format
      }
    }

    const tableRows = buildNames.map((name) => {
      const hasResult = job.build_rc && Object.prototype.hasOwnProperty.call(job.build_rc, name);
      const rc = hasResult ? job.build_rc[name] : null;
      const warn = job.build_warn?.[name] || 0;
      const err = job.build_err?.[name] || 0;
      const secs = job.build_seconds?.[name];

      let statusIcon, statusClass, stageText;
      if (!hasResult) {
        // Not started or in progress
        if (job.status === "building") {
          // Check for per-build progress
          const buildProgress = perBuildProgress[name];
          if (buildProgress) {
            statusIcon = "●";
            statusClass = "inprogress";
            stageText = buildProgress;
          } else if (Object.keys(perBuildProgress).length > 0) {
            // Other builds have progress but not this one - it's queued
            statusIcon = "○";
            statusClass = "pending";
            stageText = "queued";
          } else {
            // No per-build progress - show generic building
            statusIcon = "●";
            statusClass = "inprogress";
            stageText = "building";
          }
        } else {
          // Build hasn't started yet
          statusIcon = "○";
          statusClass = "pending";
          stageText = "—";
        }
      } else if (Number(rc) !== 0) {
        statusIcon = "✗";
        statusClass = "failed";
        stageText = "failed";
      } else if (warn > 0) {
        statusIcon = "⚠";
        statusClass = "warning";
        stageText = "✓"; // Yellow tick for passed with warnings
      } else {
        statusIcon = "✓";
        statusClass = "success";
        stageText = "✓"; // Green tick for clean pass
      }

      const warnText = warn > 0 ? `<span class="buildWarn">${warn}w</span>` : "";
      const errText = err > 0 ? `<span class="buildErr">${err}e</span>` : "";
      const timeText = secs != null ? `${secs.toFixed(1)}s` : "-";

      return `<tr class="buildRow ${statusClass}">
        <td class="buildIcon">${statusIcon}</td>
        <td class="buildName">${escHtml(name)}</td>
        <td class="buildStage">${escHtml(stageText)}</td>
        <td class="buildStats">${errText}${warnText}</td>
        <td class="buildTime">${timeText}</td>
      </tr>`;
    }).join("");

    // Add verify row
    let verifyRow = "";
    if (job.status === "verifying" || job.verify_rc != null) {
      const vrc = job.verify_rc;
      const vwarn = job.verify_warn || 0;
      const verr = job.verify_err || 0;
      const vsecs = job.verify_seconds;

      let vIcon, vClass, vStage;
      if (vrc === undefined || vrc === null) {
        vIcon = "●";
        vClass = "inprogress";
        // Show actual progress during verify if available
        vStage = (job.status === "verifying" && job.build_progress) ? job.build_progress : "verifying";
      } else if (Number(vrc) !== 0) {
        vIcon = "✗";
        vClass = "failed";
        vStage = "failed";
      } else if (vwarn > 0) {
        vIcon = "⚠";
        vClass = "warning";
        vStage = "✓"; // Yellow tick for passed with warnings
      } else {
        vIcon = "✓";
        vClass = "success";
        vStage = "✓"; // Green tick for clean pass
      }

      const vWarnText = vwarn > 0 ? `<span class="buildWarn">${vwarn}w</span>` : "";
      const vErrText = verr > 0 ? `<span class="buildErr">${verr}e</span>` : "";
      const vTimeText = vsecs != null ? `${vsecs.toFixed(1)}s` : "-";

      verifyRow = `<tr class="buildRow ${vClass} verifyRow">
        <td class="buildIcon">${vIcon}</td>
        <td class="buildName">verify</td>
        <td class="buildStage">${escHtml(vStage)}</td>
        <td class="buildStats">${vErrText}${vWarnText}</td>
        <td class="buildTime">${vTimeText}</td>
      </tr>`;
    }


    buildTable = `
      <div class="buildTable">
        <table>
          <thead><tr><th></th><th>Target</th><th>Stage</th><th></th><th>Time</th></tr></thead>
          <tbody>${tableRows}${verifyRow}</tbody>
        </table>
      </div>
    `;
  }

  // Timing element - nice two-column layout for start/finish
  let timingHtml = "";
  if (job.started_at || job.finished_at) {
    const startTime = job.started_at ? job.started_at.split(" ")[1] || job.started_at : "—";
    const endTime = job.finished_at ? job.finished_at.split(" ")[1] || job.finished_at : "—";
    const startDate = job.started_at ? job.started_at.split(" ")[0] : "";
    timingHtml = `
      <div class="timingRow">
        <div class="timingItem">
          <span class="timingIcon">▶</span>
          <span class="timingLabel">Started</span>
          <span class="timingValue">${escHtml(startTime)}</span>
        </div>
        <div class="timingItem">
          <span class="timingIcon">■</span>
          <span class="timingLabel">Finished</span>
          <span class="timingValue">${escHtml(endTime)}</span>
        </div>
        ${startDate ? `<div class="timingDate">${escHtml(startDate)}</div>` : ""}
      </div>
    `;
  }

  const grid = rows.filter(Boolean).join("") || "";
  const gridHtml = grid ? `<div class="sumGrid">${grid}</div>` : "";
  return `${prog}<div class="sumPills">${pills.join("")}</div>${buildTable}${timingHtml}${gridHtml}`;
}

function setHash(pkg) {
  if (!pkg) return;
  history.replaceState(null, "", `#${encodeURIComponent(pkg)}`);
}

function getHash() {
  const h = (location.hash || "").replace(/^#/, "");
  return h ? decodeURIComponent(h) : null;
}

async function apiGet(path) {
  const r = await fetch(path, { cache: "no-store" });
  if (!r.ok) throw new Error(`GET ${path} -> ${r.status}`);
  return await r.json();
}

async function apiPost(path, payload) {
  const r = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload || {}),
  });
  if (!r.ok) throw new Error(`POST ${path} -> ${r.status}`);
  return await r.json();
}

function renderDiffToHtml(diffText) {
  const esc = (s) => s
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");

  const lines = (diffText || "").split("\n");
  const out = [];
  for (const line of lines) {
    let cls = "diffLine diffCtx";
    if (line.startsWith("diff --git") || line.startsWith("index ") || line.startsWith("--- ") || line.startsWith("+++ ")) cls = "diffLine diffMeta";
    else if (line.startsWith("@@")) cls = "diffLine diffHunk";
    else if (line.startsWith("+") && !line.startsWith("+++")) cls = "diffLine diffAdd";
    else if (line.startsWith("-") && !line.startsWith("---")) cls = "diffLine diffDel";
    out.push(`<span class="${cls}">${esc(line)}</span>`);
  }
  return out.join("\n");
}

function renderList() {
  const root = $("#pkgList");
  root.innerHTML = "";

  const filter = (state.filter || "").toLowerCase().trim();

  // Categorize packages by status
  const active = [];      // building, verifying - always at top
  const completed = [];   // error, awaiting_review, approved, etc. - already processed
  const queued = [];      // not_started, paused, skipped - in queue

  for (const name of Object.keys(state.packages)) {
    const j = state.packages[name];
    if (j.status === "building" || j.status === "verifying") {
      active.push(name);
    } else if (j.status === "not_started" || j.status === "paused" || j.status === "skipped") {
      queued.push(name);
    } else {
      completed.push(name);
    }
  }

  // Sort each category
  const sortFn = state.sortOrder === "desc"
    ? (a, b) => b.localeCompare(a)
    : (a, b) => a.localeCompare(b);

  // Active: keep in queue order (first started first)
  // Completed: sort by user preference
  completed.sort(sortFn);
  // Queued: sort by user preference (this affects which gets picked next)
  queued.sort(sortFn);

  // Combine: active first, then completed, then queued
  const names = [...active, ...completed, ...queued];

  // Apply text filter and status filter
  const visible = names.filter((n) => {
    // Text filter
    if (filter && !n.toLowerCase().includes(filter)) return false;

    // Status filter
    const j = state.packages[n];
    const warn = sum(j.build_warn) + (j.verify_warn || 0);
    const err = sum(j.build_err) + (j.verify_err || 0);

    switch (state.statusFilter) {
      case "all": return true;
      case "building": return j.status === "building" || j.status === "verifying";
      case "error": return j.status === "error" || err > 0;
      case "warning": return warn > 0 && err === 0;
      case "review": return j.status === "awaiting_review" || j.status === "needs_input";
      case "help": return j.status === "needs_input";
      case "queue": return j.status === "not_started" || j.status === "paused" || j.status === "skipped";
      default: return true;
    }
  });

  for (const name of visible) {
    const j = state.packages[name];
    const selected = state.selected === name;

    const warn = sum(j.build_warn) + (j.verify_warn || 0);
    const err = sum(j.build_err) + (j.verify_err || 0);

    const metaPills = [];
    metaPills.push(el("span", { class: `pill ${statusPillClass(j.status)}` }, [
      el("span", { class: "dot" }),
      el("span", { text: statusLabel(j.status) }),
    ]));
    if (j.registry_updated_014) {
      metaPills.push(el("span", { class: "pill good" }, [
        el("span", { class: "dot" }),
        el("span", { text: `updated ✅ ${j.registry_requires_atopile || ""}`.trim() }),
      ]));
    } else if (j.registry_requires_atopile) {
      metaPills.push(el("span", { class: "pill" }, [
        el("span", { class: "dot" }),
        el("span", { text: `requires ${j.registry_requires_atopile}` }),
      ]));
    } else if (j.registry_error) {
      metaPills.push(el("span", { class: "pill warn" }, [
        el("span", { class: "dot" }),
        el("span", { text: "registry err" }),
      ]));
    }
    if (warn) metaPills.push(el("span", { class: "pill warn" }, [el("span", { class: "dot" }), el("span", { text: `${warn} warnings` })]));
    if (err) metaPills.push(el("span", { class: "pill bad" }, [el("span", { class: "dot" }), el("span", { text: `${err} errors` })]));
    if (j.approved_by) metaPills.push(el("span", { class: "pill good" }, [el("span", { class: "dot" }), el("span", { text: `approved: ${j.approved_by}` })]));

    // Show build progress when actively building/verifying
    const isActive = j.status === "building" || j.status === "verifying";
    if (isActive && j.build_progress) {
      // Parse JSON format or show raw string
      let progressText = j.build_progress;
      try {
        const parsed = JSON.parse(j.build_progress);
        if (typeof parsed === "object" && parsed !== null) {
          // Show first active build's progress
          const entries = Object.entries(parsed);
          if (entries.length > 0) {
            const [buildName, status] = entries[0];
            progressText = `${buildName}: ${status}`;
          }
        }
      } catch {
        // Not JSON - use as is
      }
      metaPills.push(el("span", { class: "pill purple buildProgress" }, [
        el("span", { class: "dot" }),
        el("span", { text: progressText }),
      ]));
    }

    const metrics = [];
    const canPause = (j.status === "not_started" || j.status === "building" || j.status === "verifying");
    const canUnpause = (j.status === "paused" || j.status === "skipped");
    const canPrioritize = (j.status === "not_started" || j.status === "paused" || j.status === "skipped");
    if (canPause || canUnpause) {
      metrics.push(el("button", {
        class: "miniBtn",
        text: canUnpause ? "Resume" : "Pause",
        onClick: async (ev) => {
          ev.stopPropagation();
          if (canUnpause) await apiPost(`/api/package/${encodeURIComponent(name)}/unpause`, {});
          else await apiPost(`/api/package/${encodeURIComponent(name)}/pause`, {});
          await refresh(true);
        },
      }));
    }
    if (canPrioritize) {
      metrics.push(el("button", {
        class: "miniBtn",
        text: "Do next",
        onClick: async (ev) => {
          ev.stopPropagation();
          // Optimistic UI: move to top immediately for responsiveness.
          if (Array.isArray(state.queue)) {
            state.queue = [name, ...state.queue.filter((p) => p !== name)];
          }
          renderList();
          try {
            await apiPost(`/api/package/${encodeURIComponent(name)}/prioritize`, {});
          } finally {
            await refresh(true);
          }
        },
      }));
    }
    const totalSecs = sum(j.build_seconds) + (j.verify_seconds || 0);
    // Show elapsed time for active builds, or total time for completed builds
    if (isActive && j.started_at) {
      const startMs = new Date(j.started_at.replace(" ", "T")).getTime();
      const elapsedSecs = Math.max(0, (Date.now() - startMs) / 1000);
      metrics.push(el("div", { class: "metric activeTimer", text: `${Math.floor(elapsedSecs)}s` }));
    } else if (totalSecs) {
      metrics.push(el("div", { class: "metric", text: `${totalSecs.toFixed(1)}s` }));
    }
    if (j.finished_at) metrics.push(el("div", { class: "metric", text: `done ${j.finished_at.split(" ")[1]}` }));

    // Highlight packages needing attention (awaiting review OR already published/pushed)
    const needsAttention = ["awaiting_review", "publishing", "branch_pushed", "pr_opened"].includes(j.status);
    const needsHelp = j.status === "needs_input";
    root.append(el("div", {
      class: `pkgRow ${selected ? "selected" : ""} ${needsHelp ? "needs-help" : ""} ${needsAttention ? "attention" : ""}`,
      onClick: () => selectPackage(name),
    }, [
      el("div", {}, [
        el("div", { class: "pkgName", text: name }),
        el("div", { class: "pkgMeta" }, metaPills),
      ]),
      el("div", { class: "metrics" }, metrics),
    ]));
  }
}

function renderRight() {
  const t0 = performance.now();
  const title = $("#pkgTitle");
  const sub = $("#pkgSub");
  const summary = $("#summary");
  const grid = $(".grid");
  const buildSelect = $("#buildSelect");
  let kv = $("#kv");
  const todo = $("#todo");
  const todoHint = $("#todoHint");
  const openBtn = $("#openBtn");
  const approveBtn = $("#approveBtn");
  const unapproveBtn = $("#unapproveBtn");
  const publishBtn = $("#publishBtn");
  const restartBtn = $("#restartBtn");
  const cursorBtn = $("#cursorBtn");
  const logStageSelect = $("#logStageSelect"); // may be null if user has an old cached HTML
  const logSelect = $("#logSelect");
  const logSearch = $("#logSearch");
  const logViewer = $("#logViewer");
  const logHint = $("#logHint");
  const mv = $("#mv");
  const cardLayout = $("#cardLayout");
  const cardLogs = $("#cardLogs");
  const cardIssues = $("#cardIssues");
  const issuesList = $("#issuesList");
  const issuesHint = $("#issuesHint");
  const issueFilterSelect = $("#issueFilterSelect");
  const issueSearch = $("#issueSearch");
  const toggleLogsBtn = $("#toggleLogsBtn");
  const hideLogsBtn = $("#hideLogsBtn");
  const cardModel = $("#cardModel");
  const cardDiff = $("#cardDiff");
  const diffMeta = $("#diffMeta");
  const diffViewer = $("#diffViewer");
  const refreshDiffBtn = $("#refreshDiffBtn");
  const tabViewer = $("#tabViewer");
  const tabDiff = $("#tabDiff");

  const pkg = state.selected;
  const detail = state.selectedDetail;

  if (!pkg || !detail) {
    title.textContent = "Select a package";
    sub.textContent = "";
    summary.innerHTML = `<div class="muted">—</div>`;
    buildSelect.innerHTML = "";
    kv.removeAttribute("src");
    todo.value = "";
    todoHint.textContent = "";
    openBtn.disabled = true;
    approveBtn.disabled = true;
    unapproveBtn.disabled = true;
    publishBtn.disabled = true;
    restartBtn.disabled = true;
    cursorBtn.disabled = true;
    if (logStageSelect) logStageSelect.innerHTML = "";
    logSelect.innerHTML = "";
    logSearch.value = "";
    logViewer.textContent = "";
    logHint.textContent = "";
    if (issuesList) issuesList.innerHTML = "";
    if (issuesHint) issuesHint.textContent = "";
    if (issueSearch) issueSearch.value = "";
    // Clear agent messages area
    const agentMsgsEl = $("#agentMessages");
    if (agentMsgsEl) agentMsgsEl.innerHTML = "";
    const clearMsgsBtn = $("#clearMessagesBtn");
    if (clearMsgsBtn) clearMsgsBtn.style.display = "none";
    const resolveHelpBtn = $("#resolveHelpBtn");
    if (resolveHelpBtn) resolveHelpBtn.style.display = "none";
    mv.removeAttribute("src");
    if (cardDiff) cardDiff.style.display = "none";
    if (cardIssues) cardIssues.style.display = "flex";
    if (cardLogs) cardLogs.style.display = "none";
    if (grid) grid.classList.remove("modeDiff");
    return;
  }

  const job = detail.job;
  const approved = !!job.approved_by;
  const prevTab = state.lastViewTab;
  state.lastViewTab = state.viewTab;

  // Tabs: always available; approval just gates Publish.
  tabViewer.classList.toggle("active", state.viewTab === "viewer");
  tabDiff.classList.toggle("active", state.viewTab === "diff");
  if (!tabViewer._wired) {
    tabViewer.addEventListener("click", async () => {
      state.viewTab = "viewer";
      renderRight();
    });
    tabViewer._wired = true;
  }
  if (!tabDiff._wired) {
    tabDiff.addEventListener("click", async () => {
      state.viewTab = "diff";
      await fetchDiff();
      renderRight();
    });
    tabDiff._wired = true;
  }

  // Viewer vs Diff visibility
  if (state.viewTab === "diff") {
    if (grid) grid.classList.add("modeDiff");
    cardLayout.style.display = "none";
    if (cardLogs) cardLogs.style.display = "none";
    if (cardIssues) cardIssues.style.display = "none";
    cardModel.style.display = "none";
    cardDiff.style.display = "flex";

    // Hidden-change summary (files excluded from the filtered diff)
    const info = state.diffInfo || {};
    const hidden = info.hidden_summary || {};
    const pills = [];
    if (typeof info.shown_total === "number" && typeof info.changed_total === "number") {
      pills.push(pillHtml("neutral", `shown ${info.shown_total}/${info.changed_total} files`));
    }
    if (typeof info.hidden_total === "number" && info.hidden_total > 0) {
      pills.push(pillHtml("warn", `hidden ${info.hidden_total} files`));
    }
    const items = Object.entries(hidden)
      .sort((a, b) => (b[1] || 0) - (a[1] || 0))
      .slice(0, 12)
      .map(([k, v]) => pillHtml("neutral", `${k}: ${v}`))
      .join("");
    diffMeta.innerHTML = `
      <div class="sumPills">${pills.join("")}</div>
      ${items ? `<div style="margin-top:6px;">${items}</div>` : `<div class="muted">No hidden file changes.</div>`}
    `;

    diffViewer.innerHTML = renderDiffToHtml(state.diff || "(loading diff…)");
    if (!refreshDiffBtn._wired) {
      refreshDiffBtn.addEventListener("click", async () => {
        await fetchDiff();
        renderRight();
      });
      refreshDiffBtn._wired = true;
    }
  } else {
    if (grid) grid.classList.remove("modeDiff");
    cardLayout.style.display = "flex";
    // Issues vs Logs visibility handled later in this function
    cardModel.style.display = "flex";
    cardDiff.style.display = "none";
  }
  title.textContent = pkg;
  sub.textContent = job.package_dir;

  // Build selector
  const builds = (job.build_names || []).slice();
  buildSelect.innerHTML = "";
  for (const b of builds) buildSelect.append(el("option", { value: b, text: b }));

  if (!state.selectedBuild || !builds.includes(state.selectedBuild)) {
    state.selectedBuild = builds[0] || null;
  }
  buildSelect.value = state.selectedBuild || "";
  buildSelect.disabled = (state.viewTab === "diff");

  // KiCanvas src
  if (state.selectedBuild) {
    // KiCanvas appears to pick loader behavior based on URL suffix, so serve a URL
    // that ends in `.kicad_pcb` (matches the VSCode extension's usage).
    const key = `${pkg}:${state.selectedBuild}`;
    const desiredSrc = `/pcb/${encodeURIComponent(pkg)}/${encodeURIComponent(state.selectedBuild)}.kicad_pcb?cb=${Date.now()}`;
    if (state.kvKey !== key || kv.getAttribute("src") == null) {
      state.kvKey = key;
      const next = document.createElement("kicanvas-embed");
      next.id = "kv";
      next.setAttribute("controls", "full");
      next.setAttribute("zoom", "objects");
      next.setAttribute("controlslist", "nodownload");
      next.setAttribute("src", desiredSrc);
      kv.replaceWith(next);
      kv = next;

      // Post-load auto-zoom: KiCanvas can end up at a weird scale after being hidden/shown.
      // We don't have a public imperative API, but the custom element exposes a `zoom` prop.
      const tryZoom = () => {
        try {
          if (!next.hasAttribute("loaded")) return;
          next.zoom = "objects";
          next.setAttribute("zoom", "objects");
          // Nudge resize observers
          window.dispatchEvent(new Event("resize"));
        } catch {}
      };
      const t0 = Date.now();
      const pump = () => {
        tryZoom();
        if (!next.hasAttribute("loaded") && Date.now() - t0 < 4000) requestAnimationFrame(pump);
      };
      requestAnimationFrame(pump);
    }
  } else {
    state.kvKey = null;
    kv.removeAttribute("src");
  }

  // If we just transitioned from diff -> viewer, force a remount to restore sane zoom.
  if (prevTab === "diff" && state.viewTab === "viewer") {
    state.kvKey = null;
    // next renderRight call (poll) will recreate kv; do it immediately for UX.
    setTimeout(() => renderRight(), 0);
  }

  // Buttons
  openBtn.disabled = !state.selectedBuild || !job.layout_paths || !job.layout_paths[state.selectedBuild];
  approveBtn.disabled = approved;
  unapproveBtn.disabled = !approved;
  // Publish is guarded: only allowed once all builds + verify completed with rc=0,
  // unless the server is started with --publish-anyway (unsafe override).
  const cfg = state.stateConfig || {};
  const publishAnyway = !!cfg.publish_anyway;
  const buildNames = (job.build_names || []).slice();
  const allBuildsDone = buildNames.length > 0 && buildNames.every((b) => job.build_rc && job.build_rc[b] != null);
  const allBuildsOk = buildNames.length > 0 && buildNames.every((b) => Number(job.build_rc?.[b]) === 0);
  const verifyDone = job.verify_rc != null;
  const verifyOk = Number(job.verify_rc) === 0;
  const publishable = allBuildsDone && allBuildsOk && verifyDone && verifyOk;
  publishBtn.disabled = !(publishAnyway || publishable);
  restartBtn.disabled = (job.status === "building" || job.status === "verifying");
  cursorBtn.disabled = !state.selectedBuild || !job.build_entries || !job.build_entries[state.selectedBuild];

  // Summary text
  const totalWarn = sum(job.build_warn) + (job.verify_warn || 0);
  const totalErr = sum(job.build_err) + (job.verify_err || 0);
  const totalSecs = sum(job.build_seconds) + (job.verify_seconds || 0);
  summary.innerHTML = summaryHtml(job, { totalWarn, totalErr, totalSecs });

  // TODO editor - show only user content, hide auto-generated summary
  if (!state.dirtyTodo) {
    todo.value = stripAutoContent(detail.todo || "");
  }
  todoHint.textContent = state.dirtyTodo
    ? "Saving…"
    : (state.lastTodoSavedAt ? `Saved ${state.lastTodoSavedAt}` : `File: ${job.todo_path}`);

  // Agent messages
  const agentMsgsEl = $("#agentMessages");
  const clearMsgsBtn = $("#clearMessagesBtn");
  const resolveHelpBtn = $("#resolveHelpBtn");
  const messages = job.agent_messages || [];
  if (agentMsgsEl) {
    if (messages.length > 0) {
      agentMsgsEl.innerHTML = messages.map((m) => `
        <div class="agentMsg ${m.type || 'info'}">
          <div class="msgTime">${m.timestamp || ''}</div>
          <div class="msgText">${escHtml(m.message)}</div>
        </div>
      `).join("");
      agentMsgsEl.scrollTop = agentMsgsEl.scrollHeight; // Auto-scroll to latest
    } else {
      agentMsgsEl.innerHTML = "";
    }
  }
  if (clearMsgsBtn) {
    clearMsgsBtn.style.display = messages.length > 0 ? "inline-block" : "none";
  }
  if (resolveHelpBtn) {
    resolveHelpBtn.style.display = job.status === "needs_input" ? "inline-block" : "none";
  }

  // 3D model viewer
  const modelPaths = job.model_paths || {};
  if (state.selectedBuild && modelPaths[state.selectedBuild]) {
    // Important: do NOT cache-bust every poll; GLBs can be large and this will freeze the UI.
    const key = `${pkg}:${state.selectedBuild}:${modelPaths[state.selectedBuild]}`;
    const desiredSrc = `/glb/${encodeURIComponent(pkg)}/${encodeURIComponent(state.selectedBuild)}.glb`;
    if (state.mvKey !== key || mv.getAttribute("src") !== desiredSrc) {
      state.mvKey = key;
      mv.setAttribute("src", desiredSrc);
    }
  } else {
    mv.removeAttribute("src");
    state.mvKey = null;
  }

  // Issues panel vs Logs toggle
  if (cardIssues && cardLogs) {
    if (state.showLogs) {
      cardIssues.style.display = "none";
      cardLogs.style.display = "flex";
    } else {
      cardIssues.style.display = "flex";
      cardLogs.style.display = "none";
    }
  }

  // Wire toggle buttons (idempotent)
  if (toggleLogsBtn && !toggleLogsBtn._wired) {
    toggleLogsBtn.addEventListener("click", async () => {
      state.showLogs = true;
      if (!state.logIndex) await fetchLogIndex();
      pickDefaultLogForStage();
      await fetchLog(false);
      renderRight();
    });
    toggleLogsBtn._wired = true;
  }
  if (hideLogsBtn && !hideLogsBtn._wired) {
    hideLogsBtn.addEventListener("click", () => {
      state.showLogs = false;
      renderRight();
    });
    hideLogsBtn._wired = true;
  }

  // Issues panel rendering
  if (issuesList && !state.showLogs) {
    const issues = state.issues?.issues || [];
    const filterType = state.issueFilter || "all";
    const searchQ = (state.issueSearch || "").toLowerCase().trim();

    // Filter issues
    const filtered = issues.filter((issue) => {
      if (filterType === "errors" && issue.type !== "error") return false;
      if (filterType === "warnings" && issue.type !== "warning") return false;
      if (searchQ && !issue.message.toLowerCase().includes(searchQ)) return false;
      return true;
    });

    // Preserve scroll positions before clearing
    state.issuesListScroll = issuesList.scrollTop;
    const existingLogViewer = issuesList.querySelector(".issueLogViewer");
    if (existingLogViewer && state.expandedIssue !== null) {
      state.expandedIssueScroll = existingLogViewer.scrollTop;
    }

    issuesList.innerHTML = "";

    if (filtered.length === 0) {
      if (issues.length === 0) {
        issuesList.innerHTML = `
          <div class="issuesEmpty">
            <span class="checkmark">✓</span>
            <span>No issues found</span>
            <span class="muted" style="font-size:12px;">Build completed without errors or warnings</span>
          </div>
        `;
      } else {
        issuesList.innerHTML = `
          <div class="issuesEmpty">
            <span class="muted">No matching issues</span>
            <span class="muted" style="font-size:12px;">Try adjusting your filter</span>
          </div>
        `;
      }
    } else {
      filtered.forEach((issue, idx) => {
        const isExpanded = state.expandedIssue === idx;
        const item = el("div", { class: `issueItem ${issue.type}${isExpanded ? " expanded" : ""}` }, [
          el("span", { class: `issueType ${issue.type}`, text: issue.type }),
          el("div", { class: "issueContent" }, [
            el("div", { class: "issueMessage", text: issue.message }),
            el("div", { class: "issueSource", text: `${issue.source}${issue.line_num ? ` (line ${issue.line_num})` : ""}` }),
          ]),
          el("span", { class: "issueMeta" }, [
            el("span", { text: issue.stage || "" }),
            el("span", { class: "issueExpandIcon", text: isExpanded ? "▼" : "▶" }),
          ]),
        ]);

        // Click to toggle inline log viewer
        item.addEventListener("click", async () => {
          if (state.expandedIssue === idx) {
            // Collapse if clicking the same issue
            state.expandedIssue = null;
            state.expandedIssueLog = "";
            state.expandedIssueScroll = 0;
            renderRight();
          } else {
            // Expand this issue (and collapse any other)
            state.expandedIssue = idx;
            state.expandedIssueLoading = true;
            state.expandedIssueLog = "";
            state.expandedIssueScroll = 0; // Reset scroll for new issue
            renderRight();

            // Fetch the log content for this issue
            if (issue.log_id) {
              try {
                const pkg = state.selected;
                const resp = await fetch(`/log/${encodeURIComponent(pkg)}/${encodeURIComponent(issue.log_id)}`);
                if (resp.ok) {
                  const text = await resp.text();
                  state.expandedIssueLog = text;
                } else {
                  state.expandedIssueLog = `Failed to load log (${resp.status})`;
                }
              } catch (e) {
                state.expandedIssueLog = `Error loading log: ${e.message}`;
              }
            } else {
              state.expandedIssueLog = "No log file associated with this issue";
            }
            state.expandedIssueLoading = false;
            renderRight();

            // Scroll the log viewer to the relevant line
            setTimeout(() => {
              const logPre = issuesList.querySelector(`.issueLogViewer[data-idx="${idx}"]`);
              if (logPre && issue.line_num) {
                const lines = state.expandedIssueLog.split("\n");
                const lineHeight = 14; // approx for 11px mono
                const targetScroll = Math.max(0, (issue.line_num - 3)) * lineHeight;
                logPre.scrollTop = targetScroll;
              }
            }, 50);
          }
        });
        issuesList.appendChild(item);

        // If this issue is expanded, add inline log viewer
        if (isExpanded) {
          const logContent = state.expandedIssueLoading
            ? "Loading..."
            : highlightLogLine(state.expandedIssueLog, issue.line_num);
          const logViewer = el("div", { class: `issueLogViewer ${issue.type}`, "data-idx": idx });
          logViewer.innerHTML = logContent;
          issuesList.appendChild(logViewer);

          // Restore scroll position after append
          if (state.expandedIssueScroll > 0) {
            logViewer.scrollTop = state.expandedIssueScroll;
          }

          // Track scroll changes to preserve position across re-renders
          logViewer.addEventListener("scroll", () => {
            state.expandedIssueScroll = logViewer.scrollTop;
          });
        }
      });

      // Restore issues list scroll position after rendering
      if (state.issuesListScroll > 0) {
        issuesList.scrollTop = state.issuesListScroll;
      }
    }

    // Update hint
    if (issuesHint) {
      const errCount = state.issues?.error_count || 0;
      const warnCount = state.issues?.warning_count || 0;
      issuesHint.textContent = `${errCount} error${errCount !== 1 ? "s" : ""}, ${warnCount} warning${warnCount !== 1 ? "s" : ""} • click an issue to expand log`;
    }
  }

  // Wire issue filter/search (idempotent)
  if (issueFilterSelect && !issueFilterSelect._wired) {
    issueFilterSelect.addEventListener("change", () => {
      state.issueFilter = issueFilterSelect.value;
      state.expandedIssue = null;  // Collapse expanded issue when filter changes
      state.expandedIssueLog = "";
      state.expandedIssueScroll = 0;
      state.issuesListScroll = 0;  // Reset list scroll when filter changes
      renderRight();
    });
    issueFilterSelect._wired = true;
  }
  if (issueSearch && !issueSearch._wired) {
    issueSearch.addEventListener("input", () => {
      state.issueSearch = issueSearch.value;
      state.expandedIssue = null;  // Collapse expanded issue when search changes
      state.expandedIssueLog = "";
      state.expandedIssueScroll = 0;
      state.issuesListScroll = 0;  // Reset list scroll when search changes
      renderRight();
    });
    issueSearch._wired = true;
  }
  // Keep filter select in sync
  if (issueFilterSelect) {
    issueFilterSelect.value = state.issueFilter || "all";
  }

  // Logs viewer (stage -> log)
  const idx = state.logIndex?.stages || {};
  const stageLabels = { build: "build", verify: "verify", other: "other" };
  const stageKeys = Object.keys(idx);
  if (logStageSelect) {
    logStageSelect.innerHTML = "";
    for (const k of stageKeys) logStageSelect.append(el("option", { value: k, text: stageLabels[k] || k }));
    if (!state.selectedLogStage || !stageKeys.includes(state.selectedLogStage)) {
      state.selectedLogStage = stageKeys[0] || "build";
    }
    logStageSelect.value = state.selectedLogStage || "";
  } else {
    // Old cached HTML: no stage selector. Fall back to a reasonable stage.
    if (!state.selectedLogStage || !stageKeys.includes(state.selectedLogStage)) {
      state.selectedLogStage = stageKeys[0] || "build";
    }
  }

  const logsForStage = (idx[state.selectedLogStage] || []).slice();
  const fmtBadge = (l) => {
    const e = Number(l.err || 0);
    const w = Number(l.warn || 0);
    // Use simple symbol "icons" because <option> can't contain rich HTML.
    // × = error, ! = warning
    if (e || w) return `[×${e} !${w}] `;
    return "";
  };
  const fmtReady = (l) => (l.exists === false ? "(not ready) " : "");
  logSelect.innerHTML = "";
  for (const l of logsForStage) {
    const label = `${fmtBadge(l)}${fmtReady(l)}${l.label || l.id}`;
    logSelect.append(el("option", { value: l.id, text: label }));
  }
  if (!state.selectedLog || !logsForStage.some((o) => o.id === state.selectedLog)) {
    state.selectedLog = logsForStage[0]?.id || null;
  }
  logSelect.value = state.selectedLog || "";

  const raw = state.selectedLogContent || "";
  const q = (logSearch.value || "").trim();
  if (!q) {
    logViewer.textContent = raw || "—";
  } else {
    const esc = (s) => s.replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;");
    const re = new RegExp(q.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"), "gi");
    logViewer.innerHTML = esc(raw).replace(re, (m) => `<mark style="background:${getComputedStyle(document.documentElement).getPropertyValue("--ctp-yellow")}; color:${getComputedStyle(document.documentElement).getPropertyValue("--ctp-crust")}; padding:0 2px; border-radius:3px;">${m}</mark>`);
  }
  logHint.textContent = state.selectedLog
    ? `Showing ${state.selectedLog}  •  scroll to inspect`
    : "";

  // Wire events (idempotent)
  if (!buildSelect._wired) {
    buildSelect.addEventListener("change", () => {
      state.selectedBuild = buildSelect.value;
      state.dirtyTodo = state.dirtyTodo; // keep
      fetchSelectedDetail(true);
      // refresh logs (some packages have build-target-scoped internal logs)
      fetchLogIndex().then(() => fetchLog(true)).catch(() => {});
      renderRight();
      setHash(pkg);
    });
    buildSelect._wired = true;
  }

  if (!todo._wired) {
    todo.addEventListener("input", () => {
      state.dirtyTodo = true;
      scheduleTodoAutosave();
      renderRight();
    });
    todo._wired = true;
  }

  if (logStageSelect && !logStageSelect._wired) {
    logStageSelect.addEventListener("change", async () => {
      state.selectedLogStage = logStageSelect.value;
      state.selectedLog = null;
      state.selectedLogContent = "";
      await fetchLogIndex();
      pickDefaultLogForStage();
      await fetchLog(false);
      renderRight();
    });
    logStageSelect._wired = true;
  }

  if (!logSelect._wired) {
    logSelect.addEventListener("change", async () => {
      state.selectedLog = logSelect.value;
      if (!state.logIndex) await fetchLogIndex();
      await fetchLog(false);
      renderRight();
    });
    logSelect._wired = true;
  }

  if (!logSearch._wired) {
    logSearch.addEventListener("input", () => renderRight());
    logSearch._wired = true;
  }

  debug.lastRenderRightMs = performance.now() - t0;
  updateDebugHud();
}

async function fetchState() {
  const s = await apiGet("/api/state");
  state.runDir = s.run_dir;
  state.updatedAt = s.updated_at;
  state.stateConfig = s.config || {};
  state.packages = s.packages || {};
  state.queue = s.queue || [];
}

async function fetchSelectedDetail(soft = false) {
  if (!state.selected) return;
  // If user is editing, don't clobber their textarea; still update job/excerpts.
  const d = await apiGet(`/api/package/${encodeURIComponent(state.selected)}`);
  state.selectedDetail = d;
  if (!soft) {
    state.dirtyTodo = false;
  }
}

async function fetchDiff() {
  if (!state.selected) return;
  try {
    const d = await apiGet(`/api/package/${encodeURIComponent(state.selected)}/diff`);
    state.diff = d?.diff || "";
    state.diffInfo = d || null;
  } catch (e) {
    state.diff = `Failed to load diff: ${String(e)}`;
    state.diffInfo = null;
  }
}

async function fetchLogIndex() {
  if (!state.selected) return;
  try {
    const d = await apiGet(`/api/package/${encodeURIComponent(state.selected)}/logs`);
    state.logIndex = d || null;
    state.logIndexFetchedAt = Date.now();
  } catch (e) {
    state.logIndex = { stages: { other: [{ id: "run__verify.log", label: `Failed to load log index: ${String(e)}`, warn: 0, err: 1, exists: false }] } };
    state.logIndexFetchedAt = Date.now();
  }
}

async function fetchIssues() {
  if (!state.selected) return;
  try {
    const d = await apiGet(`/api/package/${encodeURIComponent(state.selected)}/issues`);
    state.issues = d || null;
    state.issuesFetchedAt = Date.now();
  } catch (e) {
    state.issues = {
      issues: [{ type: "error", message: `Failed to load issues: ${String(e)}`, source: "system", stage: "other", line_num: 0 }],
      error_count: 1,
      warning_count: 0,
      total_count: 1,
    };
    state.issuesFetchedAt = Date.now();
  }
}

function pickDefaultLogForStage() {
  const idx = state.logIndex?.stages || {};
  const stageKeys = Object.keys(idx);
  if (!stageKeys.length) {
    state.selectedLogStage = "build";
    state.selectedLog = null;
    return;
  }
  if (!state.selectedLogStage || !stageKeys.includes(state.selectedLogStage)) {
    state.selectedLogStage = stageKeys[0] || "build";
  }
  const logsForStage = idx[state.selectedLogStage] || [];
  if (!state.selectedLog || !logsForStage.some((o) => o.id === state.selectedLog)) {
    state.selectedLog = logsForStage[0]?.id || null;
  }
}

let _todoTimer = null;
function scheduleTodoAutosave() {
  if (_todoTimer) clearTimeout(_todoTimer);
  _todoTimer = setTimeout(() => saveTodo().catch(() => {}), 450);
}

async function fetchLog(soft = false) {
  const pkg = state.selected;
  if (!pkg || !state.selectedLog) return;
  const path = `/log/${encodeURIComponent(pkg)}/${encodeURIComponent(state.selectedLog)}`;
  const r = await fetch(path, { cache: "no-store" });
  if (!r.ok) {
    state.selectedLogContent = `Failed to load ${state.selectedLog} (${r.status})`;
    return;
  }
  const txt = await r.text();
  state.selectedLogContent = txt;
  state.logFetchedAt = Date.now();
}

async function selectPackage(name) {
  if (state.selected === name) return;
  state.selected = name;
  state.selectedBuild = null;
  state.selectedDetail = null;
  state.selectedLogStage = "build";
  state.selectedLog = null;
  state.selectedLogContent = "";
  state.logIndex = null;
  state.diffInfo = null;
  state.dirtyTodo = false;
  state.issues = null;
  state.showLogs = false;  // Reset to issues view
  state.issueFilter = "all";
  state.issueSearch = "";
  state.expandedIssue = null;  // Reset expanded issue
  state.expandedIssueLog = "";
  state.expandedIssueLoading = false;
  state.expandedIssueScroll = 0;
  state.issuesListScroll = 0;  // Reset issues list scroll
  setHash(name);
  await fetchSelectedDetail(false);
  // Fetch issues first (primary view)
  await fetchIssues();
  await fetchLogIndex();
  pickDefaultLogForStage();
  // Default tab: if already approved, land in Diff; else Viewer.
  state.viewTab = state.selectedDetail?.job?.approved_by ? "diff" : "viewer";
  await fetchDiff();
  await fetchLog(true);
  renderList();
  renderRight();
}

async function saveTodo() {
  const pkg = state.selected;
  if (!pkg) return;
  const todo = $("#todo").value;
  await apiPost(`/api/package/${encodeURIComponent(pkg)}/todo`, { todo });
  state.dirtyTodo = false;
  state.lastTodoSavedAt = new Date().toLocaleTimeString();
  await fetchSelectedDetail(true);
  renderRight();
}

async function approveSelected() {
  const pkg = state.selected;
  if (!pkg) return;
  const reviewer = ($("#reviewer").value || "").trim() || null;
  await apiPost(`/api/package/${encodeURIComponent(pkg)}/approve`, { reviewer });
  await refresh(true);
  state.viewTab = "diff";
  await fetchDiff();
  renderRight();
}

async function unapproveSelected() {
  const pkg = state.selected;
  if (!pkg) return;
  await apiPost(`/api/package/${encodeURIComponent(pkg)}/unapprove`, {});
  await refresh(true);
  state.viewTab = "viewer";
  renderRight();
}

async function restartSelected() {
  const pkg = state.selected;
  if (!pkg) return;
  await apiPost(`/api/package/${encodeURIComponent(pkg)}/restart`, {});
  state.selectedLogContent = "";
  await fetchLogIndex();
  await refresh(true);
}

async function publishSelected() {
  const pkg = state.selected;
  if (!pkg) return;
  const reviewer = ($("#reviewer").value || "").trim() || null;
  const target_requires_atopile = ($("#targetAtopile").value || "").trim() || "^0.14.0";
  const commit_message = state.publish.commitMessage || "";
  try {
    const res = await apiPost(`/api/package/${encodeURIComponent(pkg)}/publish`, { reviewer, commit_message, target_requires_atopile });
    state.publish.lastResult = res.result || res;
    state.publish.error = null;
  } catch (e) {
    state.publish.error = String(e);
  }
  await refresh(true);
}

async function openInKicad() {
  const pkg = state.selected;
  const build = state.selectedBuild;
  if (!pkg || !build) return;
  await apiPost(`/api/package/${encodeURIComponent(pkg)}/open`, { build });
}

async function openInCursor() {
  const pkg = state.selected;
  const build = state.selectedBuild;
  if (!pkg || !build) return;
  try {
    await apiPost(`/api/package/${encodeURIComponent(pkg)}/open_cursor`, { build });
  } catch (e) {
    alert(`Open in Cursor failed: ${String(e)}`);
  }
}

async function openLogsInCursor() {
  const pkg = state.selected;
  if (!pkg) return;
  try {
    await apiPost(`/api/package/${encodeURIComponent(pkg)}/open_logs_cursor`, {});
  } catch (e) {
    alert(`Open logs in Cursor failed: ${String(e)}`);
  }
}

async function refresh(keepDetail = true) {
  const t0 = performance.now();
  await fetchState();
  const tList0 = performance.now();
  renderList();
  debug.lastRenderListMs = performance.now() - tList0;
  // If we reopened via a link, pick up selection from the hash once the package list is known.
  if (!state.selected) {
    const h = getHash();
    if (h && state.packages[h]) state.selected = h;
  }
  if (state.selected) {
    // If the selected package disappeared (filters/regex), drop selection cleanly.
    if (!state.packages[state.selected]) {
      state.selected = null;
      state.selectedDetail = null;
      state.selectedLog = null;
      state.selectedLogContent = "";
      state.logIndex = null;
      state.issues = null;
    } else {
      await fetchSelectedDetail(keepDetail);
      // Refresh issues periodically (every 5 seconds or if never fetched)
      const issueAge = Date.now() - (state.issuesFetchedAt || 0);
      if (!state.showLogs && (!state.issues || issueAge > 5000)) {
        await fetchIssues();
      }
      // Logs are fetched on-demand (on selection / build change / manual actions).
      if (state.viewTab === "diff") await fetchDiff();
    }
  }
  renderRight();
  debug.lastRefreshMs = performance.now() - t0;
  updateDebugHud();
}

function wireGlobal() {
  $("#filter").addEventListener("input", (e) => {
    state.filter = e.target.value || "";
    renderList();
  });

  // Status filter buttons
  const statusFilters = document.querySelectorAll(".statusFilterBtn");
  statusFilters.forEach((btn) => {
    btn.addEventListener("click", () => {
      state.statusFilter = btn.dataset.status || "all";
      // Update active state on buttons
      statusFilters.forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      renderList();
    });
  });


  $("#sortToggle")?.addEventListener("click", async () => {
    state.sortOrder = state.sortOrder === "asc" ? "desc" : "asc";
    const btn = $("#sortToggle");
    if (btn) btn.textContent = state.sortOrder === "asc" ? "A→Z" : "Z→A";
    // Update backend queue order so next build picks from correct end
    try {
      await apiPost("/api/sort_queue", { order: state.sortOrder });
    } catch (e) {
      console.error("Failed to sort queue:", e);
    }
    renderList();
  });
  $("#themeBtn")?.addEventListener("click", () => {
    const cur = getThemeMode();
    const next = cur === "auto" ? "dark" : (cur === "dark" ? "light" : "auto");
    setThemeMode(next);
  });
  $("#approveBtn").addEventListener("click", approveSelected);
  $("#unapproveBtn").addEventListener("click", unapproveSelected);
  $("#publishBtn").addEventListener("click", publishSelected);
  $("#restartBtn").addEventListener("click", restartSelected);
  $("#cursorBtn").addEventListener("click", openInCursor);
  $("#openBtn").addEventListener("click", openInKicad);
  $("#openLogsBtn").addEventListener("click", openLogsInCursor);

  // Agent message buttons
  $("#clearMessagesBtn")?.addEventListener("click", async () => {
    const pkg = state.selected;
    if (!pkg) return;
    try {
      await apiPost(`/api/package/${encodeURIComponent(pkg)}/clear_messages`, {});
      await refresh(true);
    } catch (e) {
      alert(`Failed to clear messages: ${String(e)}`);
    }
  });
  $("#resolveHelpBtn")?.addEventListener("click", async () => {
    const pkg = state.selected;
    if (!pkg) return;
    try {
      await apiPost(`/api/package/${encodeURIComponent(pkg)}/resolve_help`, {});
      await refresh(true);
    } catch (e) {
      alert(`Failed to resolve help: ${String(e)}`);
    }
  });

  // Copy Agent Instructions button - just copies the prompt
  $("#openAndCopyBtn")?.addEventListener("click", async () => {
    const pkg = state.selected;
    if (!pkg) return;
    const job = state.packages[pkg];
    if (!job) return;
    const todoPath = job.todo_path || `${job.package_dir}/review.todo.md`;
    const prompt = `Please read this file and fix the package following the instructions inside:\n\n${todoPath}\n\nThe file contains build errors/warnings that need to be fixed, along with API endpoints you can use to trigger rebuilds and check status.`;

    try {
      await navigator.clipboard.writeText(prompt);
      const btn = $("#openAndCopyBtn");
      const orig = btn.textContent;
      btn.textContent = "✓ Copied!";
      setTimeout(() => { btn.textContent = orig; }, 2000);
    } catch (e) {
      alert(`Failed to copy: ${String(e)}`);
    }
  });
}

async function bootstrap() {
  wireGlobal();
  initTheme();

  // Initialize sort button text
  const sortBtn = $("#sortToggle");
  if (sortBtn) sortBtn.textContent = state.sortOrder === "asc" ? "A→Z" : "Z→A";

  await refresh(false);

  // Prefill reviewer from git
  try {
    const who = await apiGet("/api/whoami");
    if (who?.name) $("#reviewer").value = who.name;
  } catch {}

  const initial = getHash();
  if (initial && state.packages[initial]) {
    await selectPackage(initial);
  }

  // Poll. Keep it snappy but not noisy.
  setInterval(() => refresh(true).catch(() => {}), 1200);
}

bootstrap().catch((e) => {
  $("#pkgTitle").textContent = "Failed to load";
  $("#pkgSub").textContent = String(e);
});
