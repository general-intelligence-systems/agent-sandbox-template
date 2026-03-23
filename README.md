# agent-sandbox-template

## Development

```bash
nix develop
```

Edit your agent logic in `manifests/agent.yaml`. All agents implement a single function:

```python
def run(request):
    return {"echo": request}
```

The server framework (`src/main.py`) loads this from a mounted ConfigMap and serves it over HTTP.

## Deploy

```bash
start-cluster       # create a k3d cluster
apply-manifests     # build image, install agent-sandbox, apply manifests
claim-sandbox       # claim a sandbox from the warm pool
```

Or all at once:

```bash
up
```

To update the agent without rebuilding:

```bash
kubectl apply -f manifests/agent.yaml
```

## Test

```bash
# health check
curl http://<sandbox-fqdn>:8080/health

# call the agent
curl -X POST http://<sandbox-fqdn>:8080/run \
  -H 'Content-Type: application/json' \
  -d '{"message": "hello"}'

# run a shell command
curl -X POST http://<sandbox-fqdn>:8080/exec \
  -H 'Content-Type: application/json' \
  -d '{"command": "uname -a"}'
```

Inspect resources:

```bash
kubectl get swp
kubectl get sandboxclaim
kubectl get sandbox
kubectl get pods
```

Cleanup:

```bash
k3d cluster delete agent-sandbox
```
