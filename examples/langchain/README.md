# LangChain Coding Agent Example

Adapts the [upstream LangChain example](https://github.com/kubernetes-sigs/agent-sandbox/tree/main/examples/langchain) to use the Agent Sandbox extensions API (SandboxTemplate, SandboxWarmPool, SandboxClaim).

## Files

```
examples/langchain/
├── Dockerfile           # Agent container image
├── Dockerfile.init      # Model downloader init container
├── coding_agent.py      # Agent entrypoint (placeholder -- replace with your logic)
├── download_model.py    # Model download script (placeholder)
├── requirements.txt     # Python dependencies
├── README.md
└── manifests/
    ├── secret.yaml              # HuggingFace token
    ├── sandbox-template.yaml    # SandboxTemplate + model cache PVC
    ├── sandbox-warm-pool.yaml   # Pre-warmed pool of 2 agents
    └── sandbox-claim.yaml       # Claim with auto-expiry
```

## Usage

```bash
# Build and load images into k3d
docker build -t langchain-coding-agent:local -f examples/langchain/Dockerfile examples/langchain/
docker build -t langchain-model-downloader:local -f examples/langchain/Dockerfile.init examples/langchain/
k3d image import langchain-coding-agent:local langchain-model-downloader:local -c agent-sandbox

# Edit the secret with your HF token
$EDITOR examples/langchain/manifests/secret.yaml

# Apply everything
kubectl apply -f examples/langchain/manifests/secret.yaml
kubectl apply -f examples/langchain/manifests/sandbox-template.yaml
kubectl apply -f examples/langchain/manifests/sandbox-warm-pool.yaml

# Claim an agent
claim-sandbox examples/langchain/manifests/sandbox-claim.yaml
```
