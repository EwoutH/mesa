import { createTransport } from "./transport.js";

const GROUPS = ["#188e8d", "#7761be"];
const percent = (value) => `${value.toFixed(1)}%`;

class MesaWorkspace extends HTMLElement {
  connectedCallback() {
    this.transport = createTransport();
    this.baseline = this.transport.getSaved().baseline || null;
    this.sourceName = "agents";
    this.selectedId = null;
    this.innerHTML = `
      <header class="app-header">
        <a class="brand" href="#" aria-label="Mesa workspace home">mesa<span class="brand-mark">▦</span></a>
        <span class="header-divider"></span><span class="workspace-title">Model workspace</span>
        <span class="prototype">PROOF OF CONCEPT</span>
        <div class="header-actions"><span class="host-label"></span><button class="quiet" id="source-toggle">Show source</button><button class="quiet" id="browser" hidden>Open in browser</button></div>
      </header>
      <main>
        <div class="model-heading"><div><div class="eyebrow">MESA EXAMPLES / SOCIAL SCIENCE</div><h1>Schelling segregation</h1><p>Small individual preferences. Emergent collective patterns.</p></div><span class="connection" role="status">Connecting to Python…</span></div>
        <div class="toolbar" aria-label="Simulation controls">
          <div class="run-controls"><button class="primary" id="play">Run model</button><button id="step">Step</button><button id="reset">Reset</button></div>
          <div class="time-display">Time <strong id="time">0</strong><span class="state-label" id="status">Paused</span></div>
          <label class="speed-control">Speed <input id="speed" type="range" min="1" max="20" step="1" value="7"><output id="speed-value">7 steps/s</output></label>
          <button class="quiet" id="pin">Keep for comparison</button><button class="quiet" id="reload-code">Reload code</button>
        </div>
        <section class="diagnostic" hidden role="alert"><strong class="error-title">Session error</strong><pre class="error-text"></pre></section>
        <div class="layout">
          <details class="parameters panel" open>
            <summary class="panel-heading"><h2>Parameters</h2><span class="small-tag">NEXT RUN</span></summary>
            <p class="muted small">Changes apply when you reset.</p>
            <label class="field">Random seed<input id="seed" type="number" min="0" max="4294967295" step="1" value="42"></label>
            <label class="field">Population density<output id="density-value">80%</output><input id="density" type="range" min="0.1" max="0.95" step="0.05" value="0.8"></label>
            <label class="field">Similarity threshold<output id="homophily-value">55%</output><input id="homophily" type="range" min="0.1" max="0.9" step="0.05" value="0.55"></label>
            <p class="pending-note" id="pending" hidden>Parameters changed. Reset to start a new run.</p>
            <div class="aside-note"><h3>How this model works</h3><p>Unhappy agents move to an empty cell. An agent is happy when enough of its neighbors belong to the same group.</p><p>The grid wraps at its edges. Each step activates agents in a seeded random order.</p><button class="text-button" id="read-source">Read the agent rules</button></div>
            <div class="run-note"><span class="muted small">CURRENT RUN</span><code id="run-id">—</code><span class="muted small">One Python session · 28 × 28 cells</span></div>
          </details>
          <section class="source-panel panel" hidden aria-label="Python source viewer">
            <div class="source-tabs"><button data-source="agents" class="active">agents.py</button><button data-source="model">model.py</button></div>
            <div class="source-caption"><span>Python · read-only preview</span><button class="text-button" id="edit-source" hidden>Open in editor</button></div>
            <pre class="source-code" aria-label="Source code"></pre>
            <div class="source-footer"><button id="reload">Reload code & reset</button><span>Loads saved Python files.</span></div>
          </section>
          <section class="visuals" aria-label="Model visualization">
            <div class="world-panel panel"><div class="panel-heading"><h2>Neighborhood</h2><span class="muted small">Select an agent to inspect</span></div>
              <div class="world-wrap"><canvas id="world" aria-label="Schelling grid. Use the agent selector in the inspector for keyboard access."></canvas></div>
              <div class="legend"><span><i class="group-a"></i>Group A</span><span><i class="group-b"></i>Group B</span><span><i class="unhappy"></i>Unhappy</span><button class="text-button" id="clear-selection" hidden>Clear selection</button></div>
            </div>
            <div class="chart-panel panel"><div class="panel-heading"><div><h2>Happy agents</h2><span class="chart-value" id="happy-value">—</span></div><span class="muted small">Share of the population</span></div>
              <svg id="chart" role="img" aria-label="Percentage of happy agents over simulation time"></svg>
              <div class="comparison" id="comparison" hidden><span class="baseline-line"></span><span id="comparison-label"></span><button class="text-button" id="clear-baseline">Remove</button></div>
            </div>
          </section>
          <aside class="inspector panel" aria-label="Agent inspector">
            <div class="panel-heading"><h2>Inspector</h2><span class="small-tag">LIVE</span></div>
            <p class="muted small">Click a cell or choose an agent.</p>
            <label class="field">Agent<select id="agent-select"><option value="">Choose an agent…</option></select></label>
            <div class="inspection-empty"><div class="empty-grid">⊞</div><p>A closer look at<br>individual behavior.</p><span class="muted small">Selection follows the agent<br>as it moves.</span></div>
            <div class="agent-detail" hidden><div class="agent-avatar"></div><h3 id="agent-title"></h3><span class="agent-group"></span>
              <dl><div><dt>Position</dt><dd id="agent-position"></dd></div><div><dt>State</dt><dd id="agent-state"></dd></div><div><dt>Neighbors</dt><dd id="agent-neighbors"></dd></div><div><dt>Same group</dt><dd id="agent-similar"></dd></div><div><dt>Threshold</dt><dd id="agent-threshold"></dd></div></dl>
              <p class="small muted">Values belong to the displayed simulation snapshot.</p><button class="text-button" id="agent-source">View agent source</button>
            </div>
            <div class="population-note"><span class="muted small">POPULATION</span><strong id="population">—</strong><span class="muted small">agents · fixed for this run</span></div>
          </aside>
        </div>
        <footer><span>Shared workspace experiment</span><span id="footer-host">Python owns the model. Views share the session.</span></footer>
      </main>`;

    this.querySelector(".host-label").textContent = window.MESA_CONFIG.host === "vscode" ? "VS Code" : "Browser";
    this.querySelector(".parameters").open = window.MESA_CONFIG.host !== "vscode" && window.innerWidth > 720;
    this.$("browser").hidden = !this.transport.openBrowser;
    this.$("browser").onclick = () => this.transport.openBrowser?.();
    this.$("play").onclick = () => this.command(this.state?.status === "running" ? "pause" : "play");
    this.$("step").onclick = () => this.command("step");
    this.$("reset").onclick = () => this.command("reset", { parameters: this.parameters() });
    this.$("reload").onclick = () => this.command("reload", { parameters: this.parameters() });
    this.$("reload-code").onclick = () => this.command("reload", { parameters: this.parameters() });
    this.$("speed").onchange = () => this.command("speed", { speed: Number(this.$("speed").value) });
    this.$("speed").oninput = () => { this.$("speed-value").value = `${this.$("speed").value} steps/s`; };
    for (const name of ["seed", "density", "homophily"]) this.$(name).oninput = () => this.updatePending();
    this.$("source-toggle").onclick = () => this.toggleSource();
    this.$("read-source").onclick = () => this.showSource("agents");
    this.$("agent-source").onclick = () => this.showSource("agents");
    this.$("edit-source").hidden = !this.transport.openSource;
    this.$("edit-source").onclick = () => this.transport.openSource?.(this.sourceName);
    for (const tab of this.querySelectorAll("[data-source]")) tab.onclick = () => this.showSource(tab.dataset.source);
    this.$("pin").onclick = () => {
      if (!this.state) return;
      this.baseline = { run_id: this.state.run_id, parameters: this.state.parameters, history: this.state.history };
      this.save();
      this.drawChart();
    };
    this.$("clear-baseline").onclick = () => { this.baseline = null; this.save(); this.drawChart(); };
    this.$("clear-selection").onclick = () => this.select(null);
    this.$("agent-select").onchange = () => this.select(this.$("agent-select").value ? Number(this.$("agent-select").value) : null);
    this.$("world").onclick = (event) => {
      if (!this.state) return;
      const rect = this.$("world").getBoundingClientRect();
      const x = Math.floor((event.clientX - rect.left) / rect.width * this.state.width);
      const y = this.state.height - 1 - Math.floor((event.clientY - rect.top) / rect.height * this.state.height);
      this.select(this.state.agents.find((a) => a.x === x && a.y === y)?.id ?? null);
    };
    this.resizeObserver = new ResizeObserver(() => { this.drawWorld(); this.drawChart(); });
    this.resizeObserver.observe(this.$("world"));
    this.resizeObserver.observe(this.$("chart"));
    this.poll();
    this.loadSources();
  }

  disconnectedCallback() {
    clearTimeout(this.pollTimer);
    this.resizeObserver?.disconnect();
  }

  $(id) { return this.querySelector(`#${id}`); }
  save() { this.transport.save({ baseline: this.baseline }); }
  parameters() {
    return { seed: Number(this.$("seed").value), density: Number(this.$("density").value), homophily: Number(this.$("homophily").value) };
  }

  updatePending() {
    const values = this.parameters();
    this.$("density-value").value = `${Math.round(values.density * 100)}%`;
    this.$("homophily-value").value = `${Math.round(values.homophily * 100)}%`;
    this.$("pending").hidden = !this.state || Object.keys(values).every((key) => values[key] === this.state.parameters[key]);
  }

  async loadSources() {
    try {
      this.sources = await this.transport.request("/api/sources");
      this.renderSource();
    } catch (error) { this.showError(error.message); }
  }

  async poll() {
    try {
      if (!this.busy) this.render(await this.transport.request("/api/state"));
      this.querySelector(".connection").textContent = "Connected to Python";
      this.querySelector(".connection").classList.remove("offline");
    } catch (error) {
      this.querySelector(".connection").textContent = "Disconnected · retrying";
      this.querySelector(".connection").classList.add("offline");
      this.showError(error.message);
    }
    if (this.isConnected) this.pollTimer = setTimeout(() => this.poll(), 250);
  }

  async command(action, extra = {}) {
    if (this.busy) return;
    this.busy = true;
    this.setBusy(true);
    try {
      this.render(await this.transport.request("/api/command", { action, ...extra }));
      this.commandError = null;
      this.showError(this.state.error);
      if (action === "reload") await this.loadSources();
    } catch (error) {
      this.commandError = error.message;
      this.showError(error.message);
    } finally {
      this.busy = false;
      this.setBusy(false);
    }
  }

  setBusy(value) {
    for (const id of ["play", "step", "reset", "reload", "reload-code"]) this.$(id).disabled = value;
    if (!value && this.state) this.updateControls();
  }

  showError(message) {
    this.querySelector(".diagnostic").hidden = !message;
    this.querySelector(".error-text").textContent = message || "";
  }

  render(state) {
    // A command can overtake an in-flight poll. Never repaint an older frame.
    if (this.state && state.revision < this.state.revision) return;
    if (!this.state || state.run_id !== this.state.run_id) {
      this.selectedId = null;
      for (const name of ["seed", "density", "homophily"]) this.$(name).value = state.parameters[name];
      const options = [new Option("Choose an agent…", ""), ...state.agents.map((a) => new Option(`Agent ${a.id} · Group ${a.group === 0 ? "A" : "B"}`, a.id))];
      this.$("agent-select").replaceChildren(...options);
    }
    this.state = state;
    this.$("time").textContent = state.time.toFixed(0);
    this.$("run-id").textContent = state.run_id;
    this.$("population").textContent = state.agents.length.toLocaleString();
    this.$("happy-value").textContent = percent(state.history.at(-1).happy);
    const labels = { running: "Running", paused: "Paused", complete: "All agents happy", limit: "500-step limit reached", error: "Model error" };
    this.$("status").textContent = labels[state.status];
    this.$("status").dataset.status = state.status;
    if (document.activeElement !== this.$("speed")) {
      this.$("speed").value = Math.round(state.speed);
      this.$("speed-value").value = `${Math.round(state.speed)} steps/s`;
    }
    this.updatePending();
    this.updateControls();
    this.showError(state.error || this.commandError);
    this.drawWorld();
    this.drawChart();
    this.renderInspector();
  }

  updateControls() {
    const ended = ["complete", "limit", "error"].includes(this.state.status);
    this.$("play").textContent = this.state.status === "running" ? "Pause model" : "Run model";
    this.$("play").disabled = this.busy || ended;
    this.$("step").disabled = this.busy || ended || this.state.status === "running";
  }

  select(id) {
    this.selectedId = id;
    this.$("agent-select").value = id ?? "";
    this.$("clear-selection").hidden = id === null;
    this.drawWorld();
    this.renderInspector();
  }

  renderInspector() {
    const agent = this.state?.agents.find((a) => a.id === this.selectedId);
    this.querySelector(".inspection-empty").hidden = !!agent;
    this.querySelector(".agent-detail").hidden = !agent;
    this.$("clear-selection").hidden = !agent;
    if (!agent) return;
    const { width, height } = this.state;
    const neighbors = this.state.agents.filter((other) => {
      const dx = Math.abs(other.x - agent.x), dy = Math.abs(other.y - agent.y);
      return other.id !== agent.id && Math.min(dx, width - dx) <= 1 && Math.min(dy, height - dy) <= 1;
    });
    const same = neighbors.filter((a) => a.group === agent.group).length;
    this.$("agent-title").textContent = `Agent ${agent.id}`;
    this.querySelector(".agent-group").textContent = `Group ${agent.group === 0 ? "A" : "B"}`;
    const avatar = this.querySelector(".agent-avatar");
    avatar.style.backgroundColor = GROUPS[agent.group];
    avatar.style.borderRadius = agent.group === 0 ? "50%" : "4px";
    this.$("agent-position").textContent = `(${agent.x}, ${agent.y})`;
    this.$("agent-state").textContent = agent.happy ? "Happy" : "Unhappy";
    this.$("agent-neighbors").textContent = neighbors.length;
    this.$("agent-similar").textContent = `${same} / ${neighbors.length}`;
    this.$("agent-threshold").textContent = percent(this.state.parameters.homophily * 100);
  }

  drawWorld() {
    if (!this.state) return;
    const canvas = this.$("world"), rect = canvas.getBoundingClientRect();
    if (!rect.width) return;
    const ratio = window.devicePixelRatio || 1;
    canvas.width = Math.round(rect.width * ratio);
    canvas.height = Math.round(rect.height * ratio);
    const ctx = canvas.getContext("2d");
    ctx.scale(ratio, ratio);
    const cell = rect.width / this.state.width;
    ctx.fillStyle = "#edf1f5";
    ctx.fillRect(0, 0, rect.width, rect.height);
    ctx.strokeStyle = "#dfe5eb";
    ctx.lineWidth = 0.5;
    for (let i = 0; i <= this.state.width; i++) {
      ctx.beginPath(); ctx.moveTo(i * cell, 0); ctx.lineTo(i * cell, rect.height); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(0, i * cell); ctx.lineTo(rect.width, i * cell); ctx.stroke();
    }
    for (const agent of this.state.agents) {
      const x = (agent.x + 0.5) * cell, y = (this.state.height - agent.y - 0.5) * cell;
      const radius = cell * 0.35;
      ctx.fillStyle = GROUPS[agent.group];
      ctx.beginPath();
      if (agent.group === 0) ctx.arc(x, y, radius, 0, Math.PI * 2);
      else ctx.roundRect(x - radius, y - radius, radius * 2, radius * 2, cell * 0.12);
      ctx.fill();
      if (!agent.happy) { ctx.strokeStyle = "#263340"; ctx.lineWidth = 1.2; ctx.stroke(); }
      if (agent.id === this.selectedId) {
        ctx.beginPath(); ctx.arc(x, y, cell * 0.46, 0, Math.PI * 2);
        ctx.strokeStyle = "#fff"; ctx.lineWidth = 4; ctx.stroke();
        ctx.strokeStyle = "#162f4c"; ctx.lineWidth = 1.8; ctx.stroke();
      }
    }
    canvas.setAttribute("aria-label", `${this.state.agents.length} agents at time ${this.state.time}. Select an agent using the inspector dropdown.`);
  }

  drawChart() {
    if (!this.state) return;
    const svg = this.$("chart"), width = svg.clientWidth;
    if (!width) return;
    const height = 150, left = 38, right = 12, top = 15, bottom = 25;
    svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
    svg.replaceChildren();
    const add = (name, attrs, content) => {
      const el = document.createElementNS("http://www.w3.org/2000/svg", name);
      for (const [key, value] of Object.entries(attrs)) el.setAttribute(key, value);
      if (content !== undefined) el.textContent = content;
      svg.append(el); return el;
    };
    const maxTime = Math.max(20, this.state.time, this.baseline?.history.at(-1)?.time || 0);
    const x = (t) => left + t / maxTime * (width - left - right);
    const y = (value) => height - bottom - value / 100 * (height - top - bottom);
    for (const value of [0, 50, 100]) {
      add("line", { x1: left, y1: y(value), x2: width - right, y2: y(value), stroke: "#e2e7ed" });
      add("text", { x: left - 8, y: y(value) + 4, "text-anchor": "end", class: "axis-label" }, `${value}%`);
    }
    for (const value of [0, Math.round(maxTime / 2), maxTime]) add("text", { x: x(value), y: height - 5, "text-anchor": value === 0 ? "start" : "end", class: "axis-label" }, value);
    const line = (points, baseline) => {
      const d = points.map((point, i) => `${i ? "L" : "M"}${x(point.time)},${y(point.happy)}`).join(" ");
      add("path", { d, fill: "none", stroke: baseline ? "#929bac" : GROUPS[0], "stroke-width": baseline ? 2 : 2.5, ...(baseline ? { "stroke-dasharray": "5 4" } : {}) });
      const last = points.at(-1);
      if (last && !baseline) add("circle", { cx: x(last.time), cy: y(last.happy), r: 3.5, fill: GROUPS[0] });
    };
    if (this.baseline) line(this.baseline.history, true);
    line(this.state.history, false);
    this.$("comparison").hidden = !this.baseline;
    if (this.baseline) this.$("comparison-label").textContent = `Saved run ${this.baseline.run_id} · seed ${this.baseline.parameters.seed} · threshold ${Math.round(this.baseline.parameters.homophily * 100)}%`;
    svg.setAttribute("aria-label", `Happy agents: ${percent(this.state.history.at(-1).happy)} at simulation time ${this.state.time}. Horizontal axis: simulation time. Vertical axis: percent happy.`);
  }

  toggleSource() {
    const panel = this.querySelector(".source-panel");
    this.showSource(this.sourceName, panel.hidden);
  }

  showSource(name, show = true) {
    this.sourceName = name;
    // The editor host opens the real file, rather than duplicating its editor.
    if (this.transport.openSource && show) {
      this.transport.openSource(name);
      return;
    }
    this.querySelector(".source-panel").hidden = !show;
    this.classList.toggle("source-open", show);
    this.$("source-toggle").textContent = show ? "Hide source" : "Show source";
    this.renderSource();
  }

  renderSource() {
    const source = this.sources?.[this.sourceName];
    if (!source) return;
    this.querySelector(".source-code").replaceChildren(...source.text.split("\n").map((text, index) => {
      const line = document.createElement("span"); line.className = "code-line";
      const number = document.createElement("span"); number.className = "line-number"; number.textContent = index + 1;
      const content = document.createElement("span"); content.textContent = text;
      if (text.trim().startsWith("#")) content.className = "code-comment";
      else if (/^\s*(class |def |from |import )/.test(text)) content.className = "code-keyword";
      line.append(number, content); return line;
    }));
    for (const tab of this.querySelectorAll("[data-source]")) tab.classList.toggle("active", tab.dataset.source === this.sourceName);
  }
}

customElements.define("mesa-workspace", MesaWorkspace);
