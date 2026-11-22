const vscode = require("vscode");
const fs = require("node:fs");
const path = require("node:path");
const http = require("node:http");
const crypto = require("node:crypto");
const { spawn } = require("node:child_process");

const prototype = path.resolve(__dirname, "..");
const root = path.resolve(prototype, "../..");
const assets = path.join(prototype, "web");
let active;

function request(info, apiPath, body) {
  return new Promise((resolve, reject) => {
    const data = body === undefined ? null : JSON.stringify(body);
    const req = http.request(new URL(apiPath, info.url), {
      method: data ? "POST" : "GET",
      headers: {
        "X-Mesa-Token": info.token,
        ...(data ? { "Content-Type": "application/json", "Content-Length": Buffer.byteLength(data) } : {}),
      },
    }, (res) => {
      let result = "";
      res.setEncoding("utf8");
      res.on("data", (chunk) => { result += chunk; });
      res.on("end", () => {
        try {
          const parsed = JSON.parse(result);
          if (res.statusCode !== 200) reject(new Error(parsed.error || `HTTP ${res.statusCode}`));
          else resolve(parsed);
        } catch (error) { reject(error); }
      });
    });
    req.on("error", reject);
    req.setTimeout(8000, () => req.destroy(new Error("Python session timed out")));
    if (data) req.write(data);
    req.end();
  });
}

async function startPython(output) {
  const configured = vscode.workspace.getConfiguration("mesaWorkspace").get("pythonPath");
  const local = path.join(root, ".venv", process.platform === "win32" ? "Scripts/python.exe" : "bin/python");
  const python = configured || (fs.existsSync(local) ? local : "python");
  const child = spawn(python, ["-u", path.join(prototype, "server.py"), "--port", "0"], {
    cwd: root, env: { ...process.env, PYTHONUTF8: "1" }, windowsHide: true,
  });
  output.appendLine(`Launching ${python}`);
  child.stderr.on("data", (chunk) => output.append(chunk.toString()));
  const ready = await new Promise((resolve, reject) => {
    let line = "";
    const timer = setTimeout(() => { child.kill(); reject(new Error("Python did not start within 30 seconds. Check the Mesa Workspace output.")); }, 30000);
    child.once("error", (error) => { clearTimeout(timer); reject(error); });
    child.once("exit", (code) => { clearTimeout(timer); reject(new Error(`Python exited (${code}). Check the Mesa Workspace output.`)); });
    child.stdout.on("data", (chunk) => {
      line += chunk.toString();
      const end = line.indexOf("\n");
      if (end === -1) return;
      try {
        const info = JSON.parse(line.slice(0, end));
        clearTimeout(timer);
        resolve(info);
      } catch (error) { clearTimeout(timer); child.kill(); reject(error); }
    });
  });
  output.appendLine(`Python session ready at ${ready.url}`);
  return { child, info: ready };
}

function webviewHtml(webview) {
  const nonce = crypto.randomBytes(18).toString("base64");
  const uri = (file) => webview.asWebviewUri(vscode.Uri.file(path.join(assets, file))).toString();
  return `<!doctype html><html lang="en"><head><meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src ${webview.cspSource} 'unsafe-inline'; script-src 'nonce-${nonce}' ${webview.cspSource}; connect-src ${webview.cspSource};">
    <link rel="stylesheet" href="${uri("styles.css")}">
    <script nonce="${nonce}">window.MESA_CONFIG = { host: "vscode" };</script>
    <script nonce="${nonce}" type="module" src="${uri("workspace.js")}"></script>
    <title>Mesa shared workspace</title></head><body><mesa-workspace></mesa-workspace></body></html>`;
}

function activate(context) {
  const output = vscode.window.createOutputChannel("Mesa Workspace");
  context.subscriptions.push(output, vscode.commands.registerCommand("mesaWorkspace.open", async () => {
    if (active?.panel) { active.panel.reveal(vscode.ViewColumn.Two); return; }
    if (active?.starting) return;
    active = { starting: true };
    try {
      if (!vscode.workspace.isTrusted) throw new Error("Trust this checkout before running Python model code.");
      const runtime = await startPython(output);
      active = runtime;
      const sources = await request(runtime.info, "/api/sources");
      const openSource = async (name) => {
        const source = sources[name];
        if (!source) return;
        const doc = await vscode.workspace.openTextDocument(vscode.Uri.file(source.path));
        const editor = await vscode.window.showTextDocument(doc, { viewColumn: vscode.ViewColumn.One, preserveFocus: false });
        const position = new vscode.Position(Math.max(0, source.line - 1), 0);
        editor.selection = new vscode.Selection(position, position);
        editor.revealRange(new vscode.Range(position, position), vscode.TextEditorRevealType.AtTop);
      };
      await openSource("agents");
      const panel = vscode.window.createWebviewPanel("mesaWorkspace", "Mesa · Schelling", vscode.ViewColumn.Two, {
        enableScripts: true, localResourceRoots: [vscode.Uri.file(assets)], retainContextWhenHidden: true,
      });
      runtime.panel = panel;
      panel.webview.onDidReceiveMessage(async (message) => {
        try {
          if (message.type === "source") await openSource(message.name);
          else if (message.type === "browser") await vscode.env.openExternal(vscode.Uri.parse(runtime.info.url));
          else if (message.type === "request") {
            if (!["/api/state", "/api/sources", "/api/command"].includes(message.path)) throw new Error("Unsupported session endpoint");
            const result = await request(runtime.info, message.path, message.path === "/api/command" ? message.body : undefined);
            await panel.webview.postMessage({ id: message.id, result });
          }
        } catch (error) {
          if (message.type === "request") await panel.webview.postMessage({ id: message.id, error: error.message });
          else vscode.window.showErrorMessage(error.message);
        }
      }, undefined, context.subscriptions);
      panel.onDidDispose(() => { runtime.child.kill(); if (active === runtime) active = null; }, undefined, context.subscriptions);
      panel.webview.html = webviewHtml(panel.webview);
      runtime.child.on("exit", (code) => {
        output.appendLine(`Python session exited (${code}).`);
      });
    } catch (error) {
      active?.child?.kill();
      active = null;
      output.appendLine(error.stack || error.message);
      vscode.window.showErrorMessage(error.message);
    }
  }));
}

function deactivate() {
  active?.child?.kill();
  active = null;
}

module.exports = { activate, deactivate };
