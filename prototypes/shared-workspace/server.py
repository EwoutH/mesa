"""Serve the shared workspace locally, with no additional Python dependencies."""

from __future__ import annotations

import argparse
import json
import secrets
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

# Support running directly from a Mesa source checkout without an editable install.
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from session import Session  # noqa: E402

ASSETS = Path(__file__).parent / "web"
FILES = {
    "/": ("index.html", "text/html"),
    "/workspace.js": ("workspace.js", "text/javascript"),
    "/transport.js": ("transport.js", "text/javascript"),
    "/styles.css": ("styles.css", "text/css"),
}


def make_server(port=8765):
    """Create a loopback-only server and its shared simulation session."""
    session = Session()
    token = secrets.token_urlsafe(32)

    class Handler(BaseHTTPRequestHandler):
        def setup(self):
            super().setup()
            self.connection.settimeout(10)

        def log_message(self, *_args):
            pass

        def send(self, status, body, content_type="application/json"):
            data = body.encode("utf-8") if isinstance(body, str) else body
            self.send_response(status)
            self.send_header("Content-Type", content_type + "; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Cross-Origin-Resource-Policy", "same-origin")
            self.send_header(
                "Content-Security-Policy",
                "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; frame-ancestors 'none'",
            )
            self.end_headers()
            self.wfile.write(data)

        def valid_host(self):
            return self.headers.get("Host") in {
                f"127.0.0.1:{self.server.server_port}",
                f"localhost:{self.server.server_port}",
            }

        def authorized(self):
            return self.valid_host() and secrets.compare_digest(
                self.headers.get("X-Mesa-Token", ""), token
            )

        def do_GET(self):
            if not self.valid_host():
                self.send(403, '{"error":"Invalid host"}')
                return
            path = urlparse(self.path).path
            if path == "/config.js":
                config = json.dumps({"token": token, "host": "browser"})
                self.send(200, f"window.MESA_CONFIG = {config};", "text/javascript")
            elif path in FILES:
                filename, content_type = FILES[path]
                self.send(200, (ASSETS / filename).read_bytes(), content_type)
            elif path in {"/api/state", "/api/sources"}:
                if not self.authorized():
                    self.send(403, '{"error":"Invalid session token"}')
                    return
                value = (
                    session.snapshot() if path == "/api/state" else session.sources()
                )
                self.send(200, json.dumps(value))
            else:
                self.send(404, '{"error":"Not found"}')

        def do_POST(self):
            origin = self.headers.get("Origin")
            allowed_origins = {
                f"http://127.0.0.1:{self.server.server_port}",
                f"http://localhost:{self.server.server_port}",
            }
            if not self.authorized() or (origin and origin not in allowed_origins):
                self.send(403, '{"error":"Invalid session token or origin"}')
                return
            if self.path != "/api/command":
                self.send(404, '{"error":"Not found"}')
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 < length <= 4096:
                    raise ValueError("Expected a small JSON command")
                body = json.loads(self.rfile.read(length))
                if not isinstance(body, dict):
                    raise ValueError("Expected a JSON object")
                parameters = body.get("parameters")
                if parameters is not None and not isinstance(parameters, dict):
                    raise ValueError("Parameters must be an object")
                action = body.get("action", "")
                if not isinstance(action, str):
                    raise ValueError("Action must be a string")
                value = session.command(action, parameters, body.get("speed"))
                self.send(200, json.dumps(value))
            except (ValueError, TypeError) as error:
                self.send(400, json.dumps({"error": str(error)}))

    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    server.daemon_threads = True
    return server, session, token


def main():
    """Run the server and the simulation clock until interrupted."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    server, session, token = make_server(args.port)
    stop = threading.Event()

    def clock():
        while not stop.wait(session.interval):
            session.tick()

    worker = threading.Thread(target=clock, daemon=True)
    worker.start()
    print(
        json.dumps({"url": f"http://127.0.0.1:{server.server_port}", "token": token}),
        flush=True,
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        stop.set()
        server.server_close()
        worker.join(timeout=2)


if __name__ == "__main__":
    main()
