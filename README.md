# agent-sandbox-template

A project template for building AI agents on [Kubernetes Agent Sandbox](https://github.com/kubernetes-sigs/agent-sandbox), using the extensions API (SandboxTemplate, SandboxWarmPool, SandboxClaim) and k3d for local development.

## Project Structure

```
agent-sandbox-template/
├── Dockerfile                          # Builds the agent container image
├── flake.nix                           # Nix flake (image, manifests, devShell)
├── src/
│   └── agent/
│       ├── main.py                     # Agent entrypoint (HTTP server + code exec)
│       ├── requirements.txt            # Python dependencies
│       └── __init__.py
├── manifests/
│   └── base/
│       ├── sandbox-template.yaml       # SandboxTemplate referencing the agent image
│       ├── sandbox-warm-pool.yaml      # Pre-warmed pool of 2 sandbox pods
│       └── sandbox-claim.yaml          # SandboxClaim to request a sandbox
├── examples/
│   └── langchain/                      # LangChain coding agent example
│       ├── Dockerfile
│       ├── Dockerfile.init
│       ├── coding_agent.py
│       ├── download_model.py
│       ├── requirements.txt
│       └── manifests/
│           ├── secret.yaml
│           ├── sandbox-template.yaml
│           ├── sandbox-warm-pool.yaml
│           └── sandbox-claim.yaml
└── bin/
    ├── start-cluster                   # Create a k3d cluster
    ├── apply-manifests                 # Build image, install agent-sandbox, apply manifests
    ├── claim-sandbox                   # Create a SandboxClaim and wait for ready
    └── up                              # Run all three in sequence
```

## Prerequisites

- [Nix](https://nixos.org/download/) with flakes enabled
- [Docker](https://docs.docker.com/get-docker/) running

## Quick Start

```bash
nix develop
up
```

This will:

1. Create a k3d cluster with 2 agent nodes
2. Build the agent Docker image and load it into the cluster
3. Install agent-sandbox v0.2.1 (core + extensions)
4. Apply the SandboxTemplate and SandboxWarmPool
5. Create a SandboxClaim and wait for it to become ready

## Step-by-Step

```bash
nix develop

# 1. Start the k3d cluster
start-cluster

# 2. Build the image, install agent-sandbox, apply template + warm pool
apply-manifests

# 3. Claim a sandbox
claim-sandbox
```

## The Agent

The base agent (`src/agent/main.py`) is a minimal HTTP server that runs inside each sandbox:

| Endpoint | Method | Description |
|---|---|---|
| `/health` | GET | Liveness/readiness probe |
| `/exec` | POST | Execute a command and return stdout/stderr/exit code |

Example:

```bash
curl -X POST http://<sandbox-fqdn>:8080/exec \
  -H 'Content-Type: application/json' \
  -d '{"command": "echo hello world"}'
```

Edit `src/agent/main.py` and `requirements.txt` to build your own agent logic. The Dockerfile and manifests will pick up the changes automatically on the next `apply-manifests` run.

## Claiming with a Custom Manifest

```bash
claim-sandbox examples/langchain/manifests/sandbox-claim.yaml
```

## Examples

### LangChain Coding Agent

See [`examples/langchain/`](examples/langchain/) for a skeleton that adapts the [upstream LangChain example](https://github.com/kubernetes-sigs/agent-sandbox/tree/main/examples/langchain) to the extensions API. It includes separate Dockerfiles for the agent and model-downloader init container.

## Inspecting Resources

```bash
kubectl get swp              # warm pool status
kubectl get sandboxclaim     # claims
kubectl get sandbox          # sandboxes
kubectl get pods -w          # watch pods
```

## Configuration

| Variable | Default | Description |
|---|---|---|
| `CLUSTER_NAME` | `agent-sandbox` | k3d cluster name |
| `AGENT_SANDBOX_VERSION` | `v0.2.1` | Upstream release to install |
| `IMAGE_NAME` | `agent-sandbox:local` | Docker image tag for the agent |

## Nix Outputs

| Output | Description |
|---|---|
| `packages.<system>.image` | Agent Docker image, impure (`nix build .#image --impure && docker load < result`) |
| `packages.<system>.manifests` | K8s manifests in the Nix store (`nix build .#manifests`) |
| `devShells.<system>.default` | Shell with kubectl, k3d, k9s, python3 |

## Cleanup

```bash
k3d cluster delete agent-sandbox
```
