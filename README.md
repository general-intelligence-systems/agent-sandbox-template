# agent-sandbox-template

A project template for building AI agents on [Kubernetes Agent Sandbox](https://github.com/kubernetes-sigs/agent-sandbox), using the extensions API (SandboxTemplate, SandboxWarmPool, SandboxClaim) and k3d for local development.

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
4. Apply ConfigMaps, Secrets, SandboxTemplate, and SandboxWarmPool
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

The base agent (`src/agent/main.py`) is a generic HTTP server. You don't need to rebuild the image to change what it does -- configure it entirely through mounted volumes.

| Endpoint | Method | Description |
|---|---|---|
| `/health` | GET | Liveness/readiness probe |
| `/config` | GET | Return loaded config, secret key names, and available scripts |
| `/exec` | POST | Execute a command (secrets injected as env vars) |
| `/run/<name>` | POST | Run a mounted script by name |

## Configuring via Volume Mounts

The agent image is intentionally generic. All behavior is configured by mounting ConfigMaps and Secrets into the sandbox via the SandboxTemplate -- no image rebuilds needed.

### Mount Points

| Path | Source | Description |
|---|---|---|
| `/etc/agent/config.yaml` | ConfigMap `agent-config` | Tool and skill configuration (key-value pairs) |
| `/etc/agent/secrets/` | Secret `agent-secrets` | API tokens -- each key becomes a file, injected as env vars on exec |
| `/etc/agent/scripts/` | ConfigMap `agent-scripts` | Executable scripts, runnable via `POST /run/<name>` |

### How it works

1. **Edit `manifests/base/agent-config.yaml`** to set model params, tool settings, skill definitions -- whatever your agent needs:

    ```yaml
    data:
      config.yaml: |
        model: gpt-4
        max_tokens: 4096
        tools: web-search,code-exec
    ```

2. **Edit `manifests/base/agent-secrets.yaml`** with your API keys:

    ```yaml
    stringData:
      OPENAI_API_KEY: "sk-..."
      ANTHROPIC_API_KEY: "sk-ant-..."
    ```

3. **Edit `manifests/base/agent-scripts.yaml`** to add scripts the agent can run:

    ```yaml
    data:
      fetch-data.sh: |
        #!/usr/bin/env bash
        curl -H "Authorization: Bearer $OPENAI_API_KEY" https://api.openai.com/v1/models
    ```

4. **Apply the changes** -- no image rebuild, just:

    ```bash
    kubectl apply -f manifests/base/
    ```

    Kubernetes propagates ConfigMap/Secret updates to running pods automatically.

### Overriding mount paths

All paths are configurable via environment variables in the SandboxTemplate:

| Env Variable | Default | Description |
|---|---|---|
| `AGENT_PORT` | `8080` | Server listen port |
| `AGENT_CONFIG_PATH` | `/etc/agent/config.yaml` | Path to config file |
| `AGENT_SECRETS_DIR` | `/etc/agent/secrets` | Directory of secret files |
| `AGENT_SCRIPTS_DIR` | `/etc/agent/scripts` | Directory of executable scripts |

### Example: calling a mounted script

```bash
# Run the hello.sh script (mounted from agent-scripts ConfigMap)
curl -X POST http://<sandbox-fqdn>:8080/run/hello.sh

# Execute arbitrary commands (secrets available as env vars)
curl -X POST http://<sandbox-fqdn>:8080/exec \
  -H 'Content-Type: application/json' \
  -d '{"command": "echo $OPENAI_API_KEY | head -c 8"}'
```

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
| `packages.<system>.image` | Agent Docker image, impure (`nix build .#image --impure`) |
| `packages.<system>.manifests` | Base k8s manifests (`nix build .#manifests`) |
| `packages.<system>.examples-langchain-image` | LangChain agent + init images, impure (`nix build .#examples-langchain-image --impure`) |
| `packages.<system>.examples-langchain-manifests` | LangChain k8s manifests (`nix build .#examples-langchain-manifests`) |
| `devShells.<system>.default` | Shell with kubectl, k3d, k9s, python3 |

## Cleanup

```bash
k3d cluster delete agent-sandbox
```
