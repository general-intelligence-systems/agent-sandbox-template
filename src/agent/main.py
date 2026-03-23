"""Minimal sandbox agent.

Provides an HTTP server with two endpoints:

    GET  /health  - Liveness/readiness probe.
    POST /exec    - Execute a command string and return its output.

This is a starting point. Replace or extend it with your own agent logic.
"""

import json
import subprocess
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler

PORT = 8080


class AgentHandler(BaseHTTPRequestHandler):
    """Handle incoming requests to the sandbox agent."""

    def do_GET(self):
        if self.path == "/health":
            self._json_response(200, {"status": "ok"})
        else:
            self._json_response(404, {"error": "not found"})

    def do_POST(self):
        if self.path == "/exec":
            self._handle_exec()
        else:
            self._json_response(404, {"error": "not found"})

    # ------------------------------------------------------------------

    def _handle_exec(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length)) if length else {}
        except (json.JSONDecodeError, ValueError):
            self._json_response(400, {"error": "invalid json"})
            return

        command = body.get("command")
        if not command:
            self._json_response(400, {"error": "missing 'command' field"})
            return

        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=body.get("timeout", 30),
            )
            self._json_response(
                200,
                {
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "exit_code": result.returncode,
                },
            )
        except subprocess.TimeoutExpired:
            self._json_response(408, {"error": "command timed out"})

    def _json_response(self, status: int, payload: dict):
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):  # noqa: A002
        sys.stderr.write(f"[agent] {format % args}\n")


def main():
    server = HTTPServer(("0.0.0.0", PORT), AgentHandler)
    print(f"Agent listening on :{PORT}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    server.server_close()


if __name__ == "__main__":
    main()
