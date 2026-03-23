"""Minimal sandbox agent.

Provides an HTTP server with these endpoints:

    GET  /health   - Liveness/readiness probe.
    GET  /config   - Return loaded tool/skill configuration.
    POST /exec     - Execute a command string and return its output.

On startup the agent loads configuration from mounted volumes:

    /etc/agent/config.yaml  - Tool and skill configuration (ConfigMap).
    /etc/agent/secrets/     - Tokens and credentials (Secret).
    /etc/agent/scripts/     - Executable scripts to run in the sandbox (ConfigMap).

All mount paths are configurable via environment variables.
"""

import json
import os
import subprocess
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

PORT = int(os.environ.get("AGENT_PORT", "8080"))
CONFIG_PATH = os.environ.get("AGENT_CONFIG_PATH", "/etc/agent/config.yaml")
SECRETS_DIR = os.environ.get("AGENT_SECRETS_DIR", "/etc/agent/secrets")
SCRIPTS_DIR = os.environ.get("AGENT_SCRIPTS_DIR", "/etc/agent/scripts")


def load_config() -> dict:
    """Load agent configuration from the mounted config file."""
    path = Path(CONFIG_PATH)
    if not path.exists():
        return {}
    text = path.read_text()
    # Minimal YAML-subset parser: supports flat key: value pairs.
    # For real YAML, add PyYAML to requirements.txt.
    config = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" in line:
            key, _, value = line.partition(":")
            config[key.strip()] = value.strip()
    return config


def load_secrets() -> dict:
    """Load secrets from the mounted secrets directory.

    Each file in the directory becomes a key (filename) with the file
    content as the value, matching how Kubernetes Secret volumes work.
    """
    secrets_path = Path(SECRETS_DIR)
    if not secrets_path.is_dir():
        return {}
    secrets = {}
    for f in secrets_path.iterdir():
        if f.is_file() and not f.name.startswith("."):
            secrets[f.name] = f.read_text().strip()
    return secrets


def discover_scripts() -> list[str]:
    """List executable scripts from the mounted scripts directory."""
    scripts_path = Path(SCRIPTS_DIR)
    if not scripts_path.is_dir():
        return []
    return sorted(f.name for f in scripts_path.iterdir() if f.is_file())


class AgentHandler(BaseHTTPRequestHandler):
    """Handle incoming requests to the sandbox agent."""

    config: dict = {}
    secrets: dict = {}
    scripts: list[str] = []

    def do_GET(self):
        if self.path == "/health":
            self._json_response(200, {"status": "ok"})
        elif self.path == "/config":
            self._json_response(
                200,
                {
                    "config": self.config,
                    "secrets": list(self.secrets.keys()),  # names only, not values
                    "scripts": self.scripts,
                },
            )
        else:
            self._json_response(404, {"error": "not found"})

    def do_POST(self):
        if self.path == "/exec":
            self._handle_exec()
        elif self.path.startswith("/run/"):
            self._handle_run_script()
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

        env = {**os.environ, **self.secrets}
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=body.get("timeout", 30),
                env=env,
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

    def _handle_run_script(self):
        script_name = self.path[len("/run/") :]
        script_path = Path(SCRIPTS_DIR) / script_name

        if not script_path.is_file():
            self._json_response(404, {"error": f"script '{script_name}' not found"})
            return

        env = {**os.environ, **self.secrets}
        try:
            result = subprocess.run(
                ["bash", str(script_path)],
                capture_output=True,
                text=True,
                timeout=60,
                env=env,
            )
            self._json_response(
                200,
                {
                    "script": script_name,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "exit_code": result.returncode,
                },
            )
        except subprocess.TimeoutExpired:
            self._json_response(408, {"error": f"script '{script_name}' timed out"})

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
    config = load_config()
    secrets = load_secrets()
    scripts = discover_scripts()

    print(
        f"Agent config:  {CONFIG_PATH} ({'loaded' if config else 'not found'})",
        flush=True,
    )
    print(f"Agent secrets: {SECRETS_DIR} ({len(secrets)} keys)", flush=True)
    print(f"Agent scripts: {SCRIPTS_DIR} ({len(scripts)} scripts)", flush=True)

    AgentHandler.config = config
    AgentHandler.secrets = secrets
    AgentHandler.scripts = scripts

    server = HTTPServer(("0.0.0.0", PORT), AgentHandler)
    print(f"Agent listening on :{PORT}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    server.server_close()


if __name__ == "__main__":
    main()
