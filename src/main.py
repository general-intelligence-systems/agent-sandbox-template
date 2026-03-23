"""Agent sandbox server. Loads agent code from /etc/agent/agent.py."""

import importlib.util
import json
import subprocess
from http.server import HTTPServer, BaseHTTPRequestHandler

AGENT_PATH = "/etc/agent/agent.py"


def load_agent(path):
    spec = importlib.util.spec_from_file_location("agent", path)
    assert spec and spec.loader, f"cannot load {path}"
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


agent = load_agent(AGENT_PATH)


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self._reply(200, {"status": "ok"})

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
        if self.path == "/run":
            self._reply(200, agent.run(body))
        elif self.path == "/exec":
            r = subprocess.run(
                body["command"], shell=True, capture_output=True, text=True, timeout=30
            )
            self._reply(
                200,
                {
                    "stdout": r.stdout,
                    "stderr": r.stderr,
                    "exit_code": r.returncode,
                },
            )
        else:
            self._reply(404, {"error": "not found"})

    def _reply(self, code, data):
        b = json.dumps(data).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)


HTTPServer(("0.0.0.0", 8080), Handler).serve_forever()
