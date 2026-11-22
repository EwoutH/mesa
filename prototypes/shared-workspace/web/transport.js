// The components know this interface, not the browser or VS Code APIs.
export function createTransport() {
  if (window.MESA_CONFIG.host === "vscode") {
    const vscode = acquireVsCodeApi();
    let nextId = 0;
    const requests = new Map();
    window.addEventListener("message", ({ data }) => {
      const pending = requests.get(data.id);
      if (!pending) return;
      clearTimeout(pending.timeout);
      requests.delete(data.id);
      if (data.error) pending.reject(new Error(data.error));
      else pending.resolve(data.result);
    });
    return {
      request(path, body) {
        return new Promise((resolve, reject) => {
          const id = ++nextId;
          const timeout = setTimeout(() => {
            requests.delete(id);
            reject(new Error("The Python session did not respond. Reopen the workspace to reconnect."));
          }, 10000);
          requests.set(id, { resolve, reject, timeout });
          vscode.postMessage({ type: "request", id, path, body });
        });
      },
      openSource(name) { vscode.postMessage({ type: "source", name }); },
      openBrowser() { vscode.postMessage({ type: "browser" }); },
      getSaved() { return vscode.getState() || {}; },
      save(value) { vscode.setState(value); },
    };
  }
  return {
    async request(path, body) {
      const response = await fetch(path, {
        method: body ? "POST" : "GET",
        headers: { "Content-Type": "application/json", "X-Mesa-Token": window.MESA_CONFIG.token },
        ...(body ? { body: JSON.stringify(body) } : {}),
      });
      const value = await response.json();
      if (!response.ok) throw new Error(value.error || `Request failed (${response.status})`);
      return value;
    },
    getSaved() {
      try { return JSON.parse(sessionStorage.getItem("mesa-workspace") || "{}"); }
      catch { return {}; }
    },
    save(value) {
      try { sessionStorage.setItem("mesa-workspace", JSON.stringify(value)); }
      catch { /* A disabled or full browser store must not prevent modelling. */ }
    },
  };
}
