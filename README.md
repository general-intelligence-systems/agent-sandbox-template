# agent-sandbox-template

A project template for [Kubernetes Agent Sandbox](https://github.com/kubernetes-sigs/agent-sandbox). Uses the extensions API and k3d for local development.

The image (`src/main.py`) is a generic server framework. Agent behavior is defined in `manifests/agent.yaml` -- a ConfigMap mounted into the sandbox at runtime. Edit the YAML, apply, done. No image rebuild.

## Prerequisites

- [Nix](https://nixos.org/download/) with flakes enabled
- [Docker](https://docs.docker.com/get-docker/) running

## Quick Start

```bash
nix develop
up
```

## Step-by-Step

```bash
nix develop
start-cluster           # create k3d cluster
apply-manifests         # build image, install agent-sandbox, apply manifests
claim-sandbox           # create a SandboxClaim, wait for ready
```

## Agent Interface

Every agent implements one function:

```python
def run(request: dict) -> dict:
```

The server (`src/main.py`) loads `agent.py` from a mounted ConfigMap and calls `run()` on `POST /run`.

| Endpoint | Method | Description |
|---|---|---|
| `/health` | GET | Readiness probe |
| `/run` | POST | Call `agent.run(request)` |
| `/exec` | POST | Run a shell command |

## Changing Agent Behavior

Edit `manifests/agent.yaml`:

```yaml
data:
  agent.py: |
    def run(request):
        return {"echo": request}
```

Apply:

```bash
kubectl apply -f manifests/agent.yaml
```

No image rebuild. Kubernetes propagates the ConfigMap update to running pods.

## Examples

See [`examples/langchain/`](examples/langchain/) for a LangChain coding agent adapted to the extensions API.

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `CLUSTER_NAME` | `agent-sandbox` | k3d cluster name |
| `AGENT_SANDBOX_VERSION` | `v0.2.1` | Upstream release to install |
| `IMAGE_NAME` | `agent-sandbox:local` | Docker image tag |

## Nix Outputs

| Output | Command |
|---|---|
| Agent image (impure) | `nix build .#image --impure` |
| Manifests | `nix build .#manifests` |
| LangChain image (impure) | `nix build .#examples-langchain-image --impure` |
| LangChain manifests | `nix build .#examples-langchain-manifests` |
| Dev shell | `nix develop` |

## Cleanup

```bash
k3d cluster delete agent-sandbox
```
