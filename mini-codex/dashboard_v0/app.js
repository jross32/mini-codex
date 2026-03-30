const page = document.body.dataset.page || "portal";

const state = {
  dashboard: null,
  orchestrator: null,
  commands: [],
  selectedWorker: null,
  lastSuccessfulUpdate: null,
  streamConnected: false,
  wsPort: null,
  socket: null,
  reconnectTimer: null,
  ellipsisFrame: 0,
};

function animatedEllipsis() {
  const frames = ["", ".", "..", "..."];
  return frames[state.ellipsisFrame % frames.length];
}

const stageConfig = [
  { key: "seed", label: "Seed", minLevel: 1, copy: "The system is waking up." },
  { key: "scout", label: "Scout", minLevel: 3, copy: "It can map terrain and react to signals." },
  { key: "smith", label: "Toolsmith", minLevel: 6, copy: "Tools begin to feel native, not borrowed." },
  { key: "captain", label: "Captain", minLevel: 10, copy: "Trusted workers can coordinate a fleet." },
  { key: "architect", label: "Architect", minLevel: 14, copy: "The system shapes its own future." },
  { key: "sovereign", label: "Sovereign", minLevel: 18, copy: "Autonomous growth is now a visible force." },
];

const skillNodes = [
  { label: "Telemetry Sight", description: "Reads live orchestrator state without waiting for post-run summaries.", unlocked: (ctx) => ctx.available },
  { label: "Trust Calibration", description: "Activates once at least 4 workers become trusted.", unlocked: (ctx) => ctx.trusted >= 4 },
  { label: "Tool Instinct", description: "Requires 6 distinct tools across the active worker pool.", unlocked: (ctx) => ctx.distinctTools >= 6 },
  { label: "Swarm Discipline", description: "Requires 16 complete workers and a healthy success rate.", unlocked: (ctx) => ctx.complete >= 16 && ctx.successRate >= 0.8 },
  { label: "Autonomy Core", description: "Requires 32 spawned workers with strong integrity.", unlocked: (ctx) => ctx.spawned >= 32 && ctx.successRate >= 0.9 },
  { label: "Repo Ascension", description: "Requires 64 workers and double-digit trusted allies.", unlocked: (ctx) => ctx.spawned >= 64 && ctx.trusted >= 10 },
];

const arsenalRules = [
  { label: "repo_map", description: "Terrain scanner for architecture awareness.", unlocked: (ctx) => ctx.toolSet.has("repo_map") },
  { label: "test_select", description: "Targeting visor for likely-impact files.", unlocked: (ctx) => ctx.toolSet.has("test_select") },
  { label: "friction_summarizer", description: "Reads pain signals from the system.", unlocked: (ctx) => ctx.toolSet.has("friction_summarizer") },
  { label: "tool_improver", description: "Turns friction into upgrades.", unlocked: (ctx) => ctx.toolSet.has("tool_improver") },
  { label: "agent_audit", description: "Self-inspection lens for the core mind.", unlocked: (ctx) => ctx.toolSet.has("agent_audit") },
  { label: "lint_check", description: "Shield against syntax drift and structural damage.", unlocked: (ctx) => ctx.toolSet.has("lint_check") },
];

const milestoneRules = [
  { label: "First Pulse", description: "Any orchestrator summary is available.", unlocked: (ctx) => ctx.available },
  { label: "Trusted Pair", description: "At least 2 trusted workers.", unlocked: (ctx) => ctx.trusted >= 2 },
  { label: "Stable Formation", description: "8 completed workers and no failures in sight.", unlocked: (ctx) => ctx.complete >= 8 && ctx.failed === 0 },
  { label: "Command Presence", description: "A dashboard-launched command has run successfully.", unlocked: (ctx) => ctx.commands.some((command) => command.status === "complete") },
  { label: "Heavy Growth", description: "24 workers spawned.", unlocked: (ctx) => ctx.spawned >= 24 },
  { label: "Mythic Branching", description: "64 spawned workers and at least 12 distinct tools.", unlocked: (ctx) => ctx.spawned >= 64 && ctx.distinctTools >= 12 },
];

function el(id) {
  return document.getElementById(id);
}

function clamp(value, min, max) {
  return Math.max(min, Math.min(max, value));
}

function pct(value) {
  return `${Math.round((value || 0) * 100)}%`;
}

function shortTime(timestamp) {
  if (!timestamp) {
    return "waiting";
  }
  const date = new Date(timestamp);
  if (Number.isNaN(date.getTime())) {
    return String(timestamp);
  }
  return date.toLocaleTimeString();
}

function since(timestamp) {
  if (!timestamp) {
    return "waiting";
  }
  const delta = Math.max(0, Math.round((Date.now() - new Date(timestamp).getTime()) / 1000));
  return `${delta}s ago`;
}

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/\"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function normalizeContext() {
  const orchestrator = state.orchestrator || {};
  const metrics = orchestrator.metrics || {};
  const workers = orchestrator.workers || [];
  const toolSet = new Set();
  workers.forEach((worker) => {
    (worker.tools_used || []).forEach((tool) => toolSet.add(tool));
  });

  const spawned = orchestrator.workers_spawned || 0;
  const complete = metrics.complete || 0;
  const trusted = metrics.trusted || 0;
  const successRate = Number(metrics.success_rate || 0);
  const usefulness = Number(metrics.usefulness || 0);
  const failed = metrics.failed || 0;
  const running = metrics.running || 0;
  const distinctTools = toolSet.size;
  const level = Math.max(1, 1 + Math.floor(spawned / 6) + Math.floor(trusted / 3));
  const power = Math.round(complete * 7 + trusted * 12 + distinctTools * 4 + successRate * 60 + usefulness * 8);
  const integrity = clamp(successRate, 0, 1);

  let stage = stageConfig[0];
  for (const candidate of stageConfig) {
    if (level >= candidate.minLevel) {
      stage = candidate;
    }
  }

  return {
    available: Boolean(orchestrator.available),
    workers,
    metrics,
    toolSet,
    distinctTools,
    spawned,
    complete,
    trusted,
    failed,
    running,
    successRate,
    usefulness,
    level,
    power,
    integrity,
    stage,
    commands: state.commands || [],
    allowUnboundedGrowth: Boolean(orchestrator.allow_unbounded_growth),
  };
}

function trustChip(trusted) {
  if (trusted === true) {
    return `<span class="mini-chip good">trusted</span>`;
  }
  if (trusted === false) {
    return `<span class="mini-chip bad">untrusted</span>`;
  }
  return `<span class="mini-chip warn">unknown</span>`;
}

function applySnapshot(snapshot) {
  state.dashboard = snapshot.dashboard || state.dashboard;
  state.orchestrator = snapshot.orchestrator || state.orchestrator;
  state.commands = snapshot.commands || state.commands;

  const workers = (state.orchestrator && state.orchestrator.workers) || [];
  if (state.selectedWorker) {
    state.selectedWorker = workers.find((worker) => worker.worker === state.selectedWorker.worker) || state.selectedWorker;
  }
  if (!state.selectedWorker && workers.length) {
    state.selectedWorker = workers[0];
  }
  state.lastSuccessfulUpdate = new Date().toISOString();
  renderAll();
}

function renderStatus() {
  const chip = el("statusChip");
  if (!chip) {
    return;
  }
  const runtime = (state.orchestrator && state.orchestrator.runtime_status) || {};
  const activity = runtime.activity || (state.streamConnected ? "Streaming online" : "Reconnecting stream");
  const lastAutosaveTs = runtime.last_autosave_utc ? new Date(runtime.last_autosave_utc).getTime() : 0;
  const autosaveRecently = lastAutosaveTs ? (Date.now() - lastAutosaveTs) < 3000 : false;
  const autosaving = Boolean(runtime.autosaving) || autosaveRecently;
  const statusPrefix = autosaving ? "Autosaving" : `[${activity}]`;
  const text = `${statusPrefix}${animatedEllipsis()}`;

  chip.className = `status-chip ${state.streamConnected ? "status-live" : "status-offline"}`;
  el("statusText").textContent = text;
  el("lastUpdate").textContent = since(state.lastSuccessfulUpdate);
}

function renderHero(ctx) {
  if (el("heroPower")) {
    el("heroPower").textContent = String(ctx.power);
  }
  if (el("heroStage")) {
    el("heroStage").textContent = ctx.stage.label;
  }
  if (el("heroStageSub")) {
    el("heroStageSub").textContent = ctx.stage.copy;
  }
}

function renderMissionMetrics(ctx) {
  if (!el("metricWorkers")) {
    return;
  }
  const maxWorkers = state.orchestrator && state.orchestrator.max_total_workers ? state.orchestrator.max_total_workers : 0;
  el("metricWorkers").textContent = String(ctx.spawned);
  el("metricWorkersSub").textContent = `of ${maxWorkers} max workers`;
  el("metricSuccess").textContent = pct(ctx.successRate);
  el("metricUseful").textContent = ctx.usefulness.toFixed(1);
  el("metricTrusted").textContent = String(ctx.trusted);
  el("metricTrustedSub").textContent = `${ctx.running} running / ${ctx.failed} failed`;

  const workerPct = maxWorkers ? ctx.spawned / maxWorkers : 0;
  el("barWorkers").style.width = `${clamp(workerPct, 0, 1) * 100}%`;
  el("barSuccess").style.width = `${clamp(ctx.successRate, 0, 1) * 100}%`;
  el("barUseful").style.width = `${clamp(ctx.usefulness / 5, 0, 1) * 100}%`;
  el("barTrusted").style.width = `${ctx.spawned ? (ctx.trusted / ctx.spawned) * 100 : 0}%`;
}

function renderWorkerGrid(ctx) {
  const grid = el("workerGrid");
  if (!grid) {
    return;
  }
  grid.innerHTML = "";
  if (!ctx.workers.length) {
    grid.innerHTML = `<div class="empty-state">No orchestrator summary yet. Run an orchestration and this constellation will fill with workers.</div>`;
    return;
  }

  ctx.workers.forEach((worker) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = `worker-card ${worker.status || "unknown"}`;
    if (state.selectedWorker && state.selectedWorker.worker === worker.worker) {
      button.classList.add("active");
    }
    button.innerHTML = `
      <div class="worker-name">${worker.worker || "unknown"}</div>
      <div class="worker-status">${worker.status || "unknown"}</div>
      <div class="tiny">${worker.steps || 0} steps</div>
    `;
    button.addEventListener("click", () => {
      state.selectedWorker = worker;
      renderAll();
    });
    grid.appendChild(button);
  });
}

function renderWorkerDetails() {
  const panel = el("workerDetails");
  if (!panel) {
    return;
  }
  const worker = state.selectedWorker;
  if (!worker) {
    panel.innerHTML = `<div class="empty-state">No worker selected yet. Choose one from the constellation to inspect tools, trust thresholds, and summary output.</div>`;
    return;
  }

  const benchmark = worker.benchmark || {};
  const tools = (worker.tools_used || []).map((tool) => `<span class="tool-chip mono">${tool}</span>`).join("");
  panel.innerHTML = `
    <div class="detail-row">
      <div class="detail-label">Worker</div>
      <div class="detail-value"><strong>${worker.worker || "unknown"}</strong> ${trustChip(benchmark.trusted)}</div>
    </div>
    <div class="detail-row">
      <div class="detail-label">Status</div>
      <div class="detail-value">${worker.status || "unknown"} · ${worker.steps || 0} steps</div>
    </div>
    <div class="detail-row">
      <div class="detail-label">Trust</div>
      <div class="detail-value">score ${Number(benchmark.trust_score || 0).toFixed(2)} / threshold ${Number(benchmark.trust_threshold || 0).toFixed(2)}</div>
    </div>
    <div class="detail-row">
      <div class="detail-label">Benchmark</div>
      <div class="detail-value chip-list">
        <span class="mini-chip">success ${pct(benchmark.success_rate || 0)}</span>
        <span class="mini-chip">usefulness ${Number(benchmark.avg_usefulness || 0).toFixed(1)}</span>
        <span class="mini-chip">uncertainty ${Number(benchmark.avg_uncertainty_reduction || 0).toFixed(1)}</span>
        <span class="mini-chip">next ${Number(benchmark.avg_next_step_quality || 0).toFixed(1)}</span>
      </div>
    </div>
    <div class="detail-row">
      <div class="detail-label">Tools</div>
      <div class="detail-value chip-list">${tools || `<span class="tiny">No tools recorded.</span>`}</div>
    </div>
    <div class="detail-row">
      <div class="detail-label">Spawned Worker</div>
      <div class="detail-value">${worker.spawned_worker || "none"}</div>
    </div>
    <div class="detail-row">
      <div class="detail-label">Summary</div>
      <div class="detail-value">${worker.final_summary || "No final summary available."}</div>
    </div>
  `;
  if (el("selectedWorkerHint")) {
    el("selectedWorkerHint").textContent = worker.worker || "Selected worker";
  }
}

function renderCommands() {
  const feed = el("commandFeed");
  if (!feed) {
    return;
  }
  feed.innerHTML = "";
  if (!state.commands.length) {
    feed.innerHTML = `<div class="empty-state">No dashboard-launched commands yet. Launch one above to seed a command history.</div>`;
    return;
  }

  state.commands.forEach((command) => {
    const item = document.createElement("div");
    item.className = "command-item";
    const statusClass = command.status === "complete" ? "good" : command.status === "failed" ? "bad" : "warn";
    const extra = command.command === "orchestrate"
      ? [
          command.iterations ? `iterations ${command.iterations}` : null,
          command.trust_threshold !== null && command.trust_threshold !== undefined ? `trust ${Number(command.trust_threshold).toFixed(2)}` : null,
          command.max_workers ? `max workers ${command.max_workers}` : null,
          command.unbounded ? "unbounded" : null,
        ].filter(Boolean).join(" · ")
      : "";
    item.innerHTML = `
      <div class="command-top">
        <div class="command-title mono">${command.command} --repo ${command.repo}</div>
        <span class="mini-chip ${statusClass}">${command.status || "unknown"}</span>
      </div>
      <div class="command-meta">
        started ${shortTime(command.started_at)} · exit ${command.exit_code ?? "-"}<br>
        ${command.goal ? `goal: ${escapeHtml(command.goal)}<br>` : ""}
        ${extra ? `${escapeHtml(extra)}<br>` : ""}
        ${command.stdout_tail ? `<span class="mono">${escapeHtml(command.stdout_tail.slice(-240))}</span>` : command.stderr_tail ? `<span class="mono">${escapeHtml(command.stderr_tail.slice(-240))}</span>` : "Waiting for process output."}
      </div>
    `;
    feed.appendChild(item);
  });
}

function renderEvents() {
  const feed = el("eventFeed");
  if (!feed) {
    return;
  }
  const orchestrator = state.orchestrator || {};
  const events = orchestrator.recent_worker_events || [];
  feed.innerHTML = "";
  if (!events.length) {
    feed.innerHTML = `<div class="empty-state">Worker events will appear here once orchestration data is available.</div>`;
    return;
  }

  events.slice().reverse().forEach((event) => {
    const item = document.createElement("div");
    item.className = "event-item";
    const statusClass = event.status === "complete" ? "good" : event.status === "failed" ? "bad" : "warn";
    item.innerHTML = `
      <div class="event-top">
        <div class="event-title">${event.worker || "worker"}</div>
        <span class="mini-chip ${statusClass}">${event.status || "unknown"}</span>
      </div>
      <div class="event-meta">
        ${event.steps || 0} steps · primary tool ${event.primary_tool || "-"}<br>
        trust score ${Number(event.trust_score || 0).toFixed(2)}
      </div>
    `;
    feed.appendChild(item);
  });
}

function buildNarration(ctx) {
  const latestCommand = state.commands[0];
  const latestEvents = ((state.orchestrator && state.orchestrator.recent_worker_events) || []).slice(-3).reverse();
  const objective = !ctx.available
    ? "Run an orchestration to wake the chamber."
    : ctx.trusted < 2
      ? "Earn two trusted workers so the chamber stabilizes."
      : ctx.distinctTools < 6
        ? "Broaden the arsenal to six distinct tools."
        : ctx.complete < 16
          ? "Hold a stable 16-worker formation with strong success rate."
          : ctx.spawned < 32
            ? "Grow the swarm to 32 workers without losing integrity."
            : "Push toward sovereign scale with deep trust and broad tools.";

  const lines = [];
  lines.push({ speaker: "Core", tone: "good", text: `Stage ${ctx.stage.label} is active. Power reads ${ctx.power}.` });

  if (latestCommand) {
    const commandState = latestCommand.status === "complete"
      ? "completed cleanly"
      : latestCommand.status === "failed"
        ? "hit resistance"
        : "is still running";
    lines.push({
      speaker: "Strategist",
      tone: latestCommand.status === "failed" ? "bad" : latestCommand.status === "complete" ? "good" : "warn",
      text: `${latestCommand.command} ${commandState} on repo ${latestCommand.repo}.`,
    });
  }

  latestEvents.forEach((event) => {
    const tone = event.status === "complete" ? "good" : event.status === "failed" ? "bad" : "warn";
    lines.push({
      speaker: event.worker || "Scout",
      tone,
      text: `${event.status || "unknown"} after ${event.steps || 0} steps using ${event.primary_tool || "no primary tool"}. Trust ${Number(event.trust_score || 0).toFixed(2)}.`,
    });
  });

  if (ctx.allowUnboundedGrowth) {
    lines.push({ speaker: "Swarm", tone: "warn", text: "Unbounded growth is enabled. Expansion pressure is rising." });
  }

  if (ctx.failed > 0) {
    lines.push({ speaker: "Guardian", tone: "bad", text: `${ctx.failed} worker failures detected. Keep integrity above the collapse line.` });
  }

  return { objective, lines: lines.slice(0, 6) };
}

function renderEvolution(ctx) {
  if (!el("evoLevel")) {
    return;
  }
  el("evoLevel").textContent = String(ctx.level);
  el("evoStage").textContent = ctx.stage.label;
  el("evoPower").textContent = String(ctx.power);
  el("evoIntegrity").textContent = pct(ctx.integrity);
  el("evoAffinity").textContent = String(ctx.distinctTools);

  const scale = clamp(0.84 + ctx.level * 0.055, 0.84, 1.95);
  const root = document.documentElement;
  root.style.setProperty("--character-scale", scale.toFixed(2));
  root.style.setProperty(
    "--character-glow",
    ctx.trusted >= 10 ? "rgba(244, 114, 182, 0.55)" : ctx.trusted >= 4 ? "rgba(52, 211, 153, 0.46)" : "rgba(96, 165, 250, 0.45)"
  );
  el("characterTool").classList.toggle("visible", ctx.distinctTools >= 4);
  el("characterCrown").classList.toggle("visible", ctx.level >= 10);

  const narration = buildNarration(ctx);
  el("questText").textContent = narration.objective;

  const dialogueFeed = el("dialogueFeed");
  dialogueFeed.innerHTML = "";
  narration.lines.forEach((line) => {
    const item = document.createElement("div");
    item.className = `dialogue-card ${line.tone}`;
    item.innerHTML = `
      <div class="dialogue-top">
        <div class="dialogue-speaker">${escapeHtml(line.speaker)}</div>
        <div class="tiny">${since(state.lastSuccessfulUpdate)}</div>
      </div>
      <div class="dialogue-copy">${escapeHtml(line.text)}</div>
    `;
    dialogueFeed.appendChild(item);
  });

  const skillTree = el("skillTree");
  skillTree.innerHTML = "";
  skillNodes.forEach((node) => {
    const unlocked = node.unlocked(ctx);
    const div = document.createElement("div");
    div.className = `skill-node ${unlocked ? "unlocked" : "locked"}`;
    div.innerHTML = `
      <div class="node-title">${node.label}<span class="mini-chip ${unlocked ? "good" : "warn"}">${unlocked ? "unlocked" : "locked"}</span></div>
      <div class="node-copy">${node.description}</div>
    `;
    skillTree.appendChild(div);
  });

  const arsenal = el("arsenalList");
  arsenal.innerHTML = "";
  arsenalRules.forEach((rule) => {
    const unlocked = rule.unlocked(ctx);
    const div = document.createElement("div");
    div.className = `arsenal-item ${unlocked ? "unlocked" : "locked"}`;
    div.innerHTML = `
      <div class="arsenal-title mono">${rule.label}<span class="mini-chip ${unlocked ? "good" : "warn"}">${unlocked ? "equipped" : "missing"}</span></div>
      <div class="arsenal-copy">${rule.description}</div>
    `;
    arsenal.appendChild(div);
  });

  const milestones = el("milestoneList");
  milestones.innerHTML = "";
  milestoneRules.forEach((rule) => {
    const unlocked = rule.unlocked(ctx);
    const div = document.createElement("div");
    div.className = `milestone ${unlocked ? "unlocked" : "locked"}`;
    div.innerHTML = `
      <div class="milestone-title">${rule.label}<span class="mini-chip ${unlocked ? "good" : "warn"}">${unlocked ? "cleared" : "pending"}</span></div>
      <div class="milestone-copy">${rule.description}</div>
    `;
    milestones.appendChild(div);
  });
}

function renderAll() {
  const ctx = normalizeContext();
  renderStatus();
  renderHero(ctx);
  renderMissionMetrics(ctx);
  renderWorkerGrid(ctx);
  renderWorkerDetails();
  renderCommands();
  renderEvents();
  renderEvolution(ctx);
}

async function fetchJson(url, options) {
  const response = await fetch(url, options);
  if (!response.ok) {
    throw new Error(`${url} failed with ${response.status}`);
  }
  return response.json();
}

async function bootstrapSnapshot() {
  const [dashboard, orchestrator, commands, streamConfig] = await Promise.all([
    fetchJson("/api/dashboard"),
    fetchJson("/api/orchestrator"),
    fetchJson("/api/commands"),
    fetchJson("/api/stream-config"),
  ]);
  state.wsPort = streamConfig.ws_port;
  applySnapshot({ dashboard, orchestrator, commands: commands.commands || [] });
}

function scheduleReconnect() {
  if (state.reconnectTimer) {
    return;
  }
  state.reconnectTimer = window.setTimeout(() => {
    state.reconnectTimer = null;
    connectStream();
  }, 1500);
}

function connectStream() {
  if (!state.wsPort) {
    return;
  }
  const protocol = window.location.protocol === "https:" ? "wss" : "ws";
  const socket = new WebSocket(`${protocol}://${window.location.hostname}:${state.wsPort}`);
  state.socket = socket;

  socket.addEventListener("open", () => {
    state.streamConnected = true;
    renderStatus();
  });

  socket.addEventListener("message", (event) => {
    try {
      const payload = JSON.parse(event.data);
      applySnapshot(payload);
    } catch (error) {
      console.error(error);
    }
  });

  socket.addEventListener("close", () => {
    state.streamConnected = false;
    renderStatus();
    scheduleReconnect();
  });

  socket.addEventListener("error", () => {
    state.streamConnected = false;
    renderStatus();
    socket.close();
  });
}

async function launchCommand(payload) {
  const response = await fetch("/api/command", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error || "command launch failed");
  }
  await bootstrapSnapshot();
}

function syncCommandFields() {
  const commandName = el("commandName");
  if (!commandName) {
    return;
  }
  const command = commandName.value;
  const orchestrateMode = command === "orchestrate";
  el("orchestrateControls").hidden = !orchestrateMode;
  el("unboundedWrap").hidden = !orchestrateMode;
  el("commandHint").textContent = orchestrateMode
    ? "Use max workers, iterations, trust threshold, and unbounded growth to tune the orchestrator directly."
    : command === "inspect" || command === "auto"
      ? "Goal is required here. These commands use the same live stream after launch."
      : "Map runs quickly and refreshes the dashboard state without orchestration knobs.";
}

function buildCommandPayload(overrides = {}) {
  const command = overrides.command || el("commandName").value;
  const payload = {
    command,
    repo: overrides.repo || el("commandRepo").value.trim() || ".",
    goal: overrides.goal !== undefined ? overrides.goal : el("commandGoal").value.trim(),
  };

  if (command === "orchestrate") {
    const maxWorkers = overrides.max_workers !== undefined ? overrides.max_workers : el("commandWorkers").value.trim();
    const iterations = overrides.iterations !== undefined ? overrides.iterations : el("commandIterations").value.trim();
    const trustThreshold = overrides.trust_threshold !== undefined ? overrides.trust_threshold : el("commandTrust").value.trim();
    payload.max_workers = maxWorkers;
    payload.iterations = iterations;
    payload.trust_threshold = trustThreshold;
    payload.unbounded = overrides.unbounded !== undefined ? overrides.unbounded : el("commandUnbounded").checked;
  }

  return payload;
}

function attachHandlers() {
  if (el("commandName")) {
    el("commandName").addEventListener("change", syncCommandFields);
    syncCommandFields();
  }

  if (el("commandForm")) {
    el("commandForm").addEventListener("submit", async (event) => {
      event.preventDefault();
      try {
        await launchCommand(buildCommandPayload());
      } catch (error) {
        alert(error.message);
      }
    });
  }

  if (el("quickInspect")) {
    el("quickInspect").addEventListener("click", async () => {
      try {
        await launchCommand({ command: "inspect", repo: ".", goal: "find the highest-value improvement opportunities" });
      } catch (error) {
        alert(error.message);
      }
    });
  }

  if (el("quickOrchestrate")) {
    el("quickOrchestrate").addEventListener("click", async () => {
      try {
        await launchCommand({
          command: "orchestrate",
          repo: ".",
          max_workers: 16,
          iterations: 3,
          trust_threshold: 0.84,
          unbounded: false,
        });
      } catch (error) {
        alert(error.message);
      }
    });
  }
}

async function init() {
  if (page === "portal") {
    return;
  }
  attachHandlers();
  window.setInterval(() => {
    state.ellipsisFrame = (state.ellipsisFrame + 1) % 4;
    renderStatus();
  }, 1000);
  try {
    await bootstrapSnapshot();
    connectStream();
  } catch (error) {
    console.error(error);
    renderAll();
    scheduleReconnect();
  }
}

init();