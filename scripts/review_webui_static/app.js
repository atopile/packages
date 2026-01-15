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

const state = {
  runDir: null,
  updatedAt: null,
  packages: {}, // name -> JobState
  queue: [],
  filter: "",
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
  const mode = getThemeMode();
  applyTheme(mode);
  const btn = $("#themeBtn");
  if (btn) btn.textContent = `Theme: ${mode[0].toUpperCase()}${mode.slice(1)}`;
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
}[s] || s);

const statusPillClass = (s) => {
  if (s === "approved" || s === "published") return "good";
  if (s === "awaiting_review") return "blue";
  if (s === "building" || s === "verifying" || s === "pushing_branch") return "purple";
  if (s === "branch_pushed") return "blue";
  if (s === "paused" || s === "skipped") return "warn";
  if (s === "error") return "bad";
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

  const rows = [];
  if (job.error) rows.push(kvRowHtml("error", job.error));
  if (job.package_identifier) rows.push(kvRowHtml("identifier", job.package_identifier));
  if (job.published_branch) rows.push(kvRowHtml("pushed branch", job.published_branch));
  if (job.published_pr_url) rows.push(kvRowHtml("PR", job.published_pr_url));
  if (job.published_target_requires_atopile) rows.push(kvRowHtml("target atopile", job.published_target_requires_atopile));
  if (job.published_at) rows.push(kvRowHtml("pushed at", job.published_at));
  if (job.publish_error) rows.push(kvRowHtml("publish error", job.publish_error));
  if (job.registry_requires_atopile) {
    rows.push(kvRowHtml("registry requires-atopile", job.registry_requires_atopile));
    rows.push(kvRowHtml("registry updated 0.14.x", job.registry_updated_014 ? "yes" : "no"));
  }
  if (job.registry_published_version) rows.push(kvRowHtml("registry published version", job.registry_published_version));
  if (job.started_at) rows.push(kvRowHtml("started", job.started_at));
  if (job.finished_at) rows.push(kvRowHtml("finished", job.finished_at));
  if (job.approved_by) rows.push(kvRowHtml("approved at", job.approved_at || "?"));

  const grid = rows.filter(Boolean).join("") || `<div class="muted">—</div>`;
  return `${prog}<div class="sumPills">${pills.join("")}</div><div class="sumGrid">${grid}</div>`;
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
  // Render in queue order (this makes "Do next" feel immediate and meaningful).
  // Append any packages not present in the queue (defensive).
  const queueNames = Array.isArray(state.queue) ? state.queue.slice() : [];
  const extra = Object.keys(state.packages).filter((n) => !queueNames.includes(n));
  extra.sort((a, b) => a.localeCompare(b));
  const names = (queueNames.length ? queueNames : Object.keys(state.packages).sort((a, b) => a.localeCompare(b))).concat(extra);

  const visible = names.filter((n) => !filter || n.toLowerCase().includes(filter));

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
    if (totalSecs) metrics.push(el("div", { class: "metric", text: `${totalSecs.toFixed(1)}s` }));
    if (j.finished_at) metrics.push(el("div", { class: "metric", text: `done ${j.finished_at.split(" ")[1]}` }));

    root.append(el("div", {
      class: `pkgRow ${selected ? "selected" : ""}`,
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
  const logBuildLink = $("#logBuildLink");
  const logVerifyLink = $("#logVerifyLink");
  const logSelect = $("#logSelect");
  const logSearch = $("#logSearch");
  const logViewer = $("#logViewer");
  const logHint = $("#logHint");
  const mv = $("#mv");
  const cardLayout = $("#cardLayout");
  const cardLogs = $("#cardLogs");
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
    logBuildLink.href = "#";
    logVerifyLink.href = "#";
    logSelect.innerHTML = "";
    logSearch.value = "";
    logViewer.textContent = "";
    logHint.textContent = "";
    mv.removeAttribute("src");
    if (cardDiff) cardDiff.style.display = "none";
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
    cardLogs.style.display = "none";
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
    cardLogs.style.display = "flex";
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

  // Links
  const buildLogName = state.selectedBuild ? `build.${state.selectedBuild}.log` : null;
  logBuildLink.href = buildLogName ? `/log/${encodeURIComponent(pkg)}/${buildLogName}` : "#";
  logVerifyLink.href = job.verify_log ? `/log/${encodeURIComponent(pkg)}/verify.log` : "#";

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

  // TODO editor
  if (!state.dirtyTodo) {
    todo.value = detail.todo || "";
  }
  todoHint.textContent = state.dirtyTodo
    ? "Saving…"
    : (state.lastTodoSavedAt ? `Saved ${state.lastTodoSavedAt}` : `File: ${job.todo_path}`);

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

  // Logs viewer
  const logOpts = [];
  for (const b of builds) logOpts.push({ value: `build.${b}.log`, label: `build.${b}.log` });
  logOpts.push({ value: "verify.log", label: "verify.log" });
  logSelect.innerHTML = "";
  for (const o of logOpts) logSelect.append(el("option", { value: o.value, text: o.label }));
  if (!state.selectedLog || !logOpts.some((o) => o.value === state.selectedLog)) {
    state.selectedLog = logOpts[0]?.value || null;
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
      // refresh model+logs
      fetchLog(true);
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

  if (!logSelect._wired) {
    logSelect.addEventListener("change", async () => {
      state.selectedLog = logSelect.value;
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
}

async function selectPackage(name) {
  if (state.selected === name) return;
  state.selected = name;
  state.selectedBuild = null;
  state.selectedDetail = null;
  state.selectedLog = null;
  state.selectedLogContent = "";
  state.diffInfo = null;
  state.dirtyTodo = false;
  setHash(name);
  await fetchSelectedDetail(false);
  // Default tab: if already approved, land in Diff; else Viewer.
  state.viewTab = state.selectedDetail?.job?.approved_by ? "diff" : "viewer";
  await fetchDiff();
  renderList();
  renderRight();
  // renderRight() sets a default selectedLog; now actually load it.
  await fetchLog(true);
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
    if (!state.packages[state.selected]) {
      state.selected = null;
      state.selectedDetail = null;
      state.selectedLog = null;
      state.selectedLogContent = "";
      state.logIndex = null;
    } else {
      await fetchSelectedDetail(keepDetail);
      // Logs are fetched on-demand (on selection / build change / manual actions).
      if (state.viewTab === "diff") await fetchDiff();
      await fetchLog(true);
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
}

async function bootstrap() {
  wireGlobal();
  initTheme();
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
