# agent-sandbox-template

## Development

```bash
nix develop
start-cluster       # create a k3d cluster
apply-manifests     # build image, install agent-sandbox, apply manifests
claim-sandbox       # claim a sandbox from the warm pool
```

Or all at once: `up`

Edit your agent logic in `manifests/agent.yaml`. All agents implement one function:

```python
def run(request):
    return {"echo": request}
```

To update without rebuilding: `kubectl apply -f manifests/agent.yaml`

## Deploy

```bash
# Build the image
docker build -t agent-sandbox:local .

# Push to your registry
docker tag agent-sandbox:local your-registry/agent-sandbox:latest
docker push your-registry/agent-sandbox:latest

# Update the image reference in manifests/sandbox-template.yaml, then:
kubectl apply -f manifests/
```

## Test

```bash
bin/test
```
