# agent-sandbox-template

A ready-to-use template for running [Kubernetes Agent Sandbox](https://github.com/kubernetes-sigs/agent-sandbox) locally with k3d, using the extensions API (SandboxTemplate, SandboxWarmPool, SandboxClaim).

## Prerequisites

- [Nix](https://nixos.org/download/) with flakes enabled
- [Docker](https://docs.docker.com/get-docker/) running

## Quick Start

Enter the dev shell and run everything in one command:

```bash
nix develop
up
```

This will:

1. Create a k3d cluster called `agent-sandbox` with 2 agent nodes
2. Install agent-sandbox v0.2.1 (core + extensions controllers)
3. Apply the base SandboxTemplate and SandboxWarmPool
4. Create a SandboxClaim and wait for it to become ready

Once complete, you'll see the sandbox name and how to exec into it.

## Step-by-Step Usage

If you prefer to run each step individually:

```bash
nix develop

# 1. Start the k3d cluster
start-cluster

# 2. Install agent-sandbox and apply the base template + warm pool
apply-manifests

# 3. Claim a sandbox from the warm pool
claim-sandbox
```

### Claiming with a custom manifest

The `claim-sandbox` script accepts an optional path argument:

```bash
# Claim using the LangChain example instead of the base
claim-sandbox manifests/examples/langchain/sandbox-claim.yaml
```

## What Gets Deployed

### Base (`manifests/base/`)

| Resource | Name | Description |
|---|---|---|
| SandboxTemplate | `default` | Ubuntu 24.04 container with managed network isolation |
| SandboxWarmPool | `default-pool` | 2 pre-warmed sandbox pods for instant provisioning |
| SandboxClaim | `my-sandbox` | Claims a sandbox from the default template |

### LangChain Example (`manifests/examples/langchain/`)

An adaptation of the [upstream LangChain coding agent example](https://github.com/kubernetes-sigs/agent-sandbox/tree/main/examples/langchain), converted to use the extensions API:

| Resource | Name | Description |
|---|---|---|
| Secret | `coding-agent-hf-token` | HuggingFace token (replace placeholder before use) |
| PVC | `models-cache-pvc` | 20Gi shared model cache |
| SandboxTemplate | `langchain-coding-agent` | Full agent spec with init container for model download |
| SandboxWarmPool | `langchain-coding-agent-pool` | 2 pre-warmed agent pods |
| SandboxClaim | `my-coding-agent` | Claim with auto-expiry and delete-on-shutdown |

To use the LangChain example:

```bash
# Edit the secret with your actual HF token
$EDITOR manifests/examples/langchain/secret.yaml

# Apply the secret and template
kubectl apply -f manifests/examples/langchain/secret.yaml
kubectl apply -f manifests/examples/langchain/sandbox-template.yaml
kubectl apply -f manifests/examples/langchain/sandbox-warm-pool.yaml

# Claim an agent
claim-sandbox manifests/examples/langchain/sandbox-claim.yaml
```

## Inspecting Resources

```bash
# Check warm pool status
kubectl get swp

# List sandbox claims
kubectl get sandboxclaim

# List sandboxes
kubectl get sandbox

# Watch pods
kubectl get pods -w
```

## Configuration

| Environment Variable | Default | Description |
|---|---|---|
| `CLUSTER_NAME` | `agent-sandbox` | Name of the k3d cluster |
| `AGENT_SANDBOX_VERSION` | `v0.2.1` | Upstream agent-sandbox release to install |

Example:

```bash
CLUSTER_NAME=my-cluster AGENT_SANDBOX_VERSION=v0.2.1 up
```

## Nix Outputs

| Output | Description |
|---|---|
| `packages.<system>.manifests` | All k8s manifests as a Nix derivation (`nix build .#manifests`) |
| `devShells.<system>.default` | Shell with kubectl, k3d, k9s, and `bin/` on PATH |

## Cleanup

```bash
k3d cluster delete agent-sandbox
```
