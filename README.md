# Microservice with Discovery

CMPE 273 — Week 7: Naming and Service Discovery

Demonstrates the core service discovery pattern:
- Two service instances register with a central registry
- A client queries the registry to discover available instances
- The client calls a randomly chosen instance

---

## How to Run

### 1. Install dependencies

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Start the Service Registry

Open a terminal:

```bash
python service_registry_improved.py
```

Expected output:
```
Service Registry starting on port 5001...
Heartbeat timeout: 30s
Cleanup interval: 10s
```

### 3. Start Two Service Instances

Open a **second** terminal:

```bash
python example_service.py hello-service 8001
```

Expected output:
```
[hello-service:8001] Registered with registry
[hello-service:8001] Running — GET /hello  GET /health
```

Open a **third** terminal:

```bash
python example_service.py hello-service 8002
```

Expected output:
```
[hello-service:8002] Registered with registry
[hello-service:8002] Running — GET /hello  GET /health
```

### 4. Run the Client

Open a **fourth** terminal:

```bash
python client.py hello-service 5
```

Expected output:
```
Querying registry at http://localhost:5001 for 'hello-service'...

Found 2 instance(s):
  - http://localhost:8001  (uptime: 8.4s)
  - http://localhost:8002  (uptime: 3.1s)

Making 5 calls, choosing a random instance each time:

  [1] -> http://localhost:8002  |  Hello from hello-service!
  [2] -> http://localhost:8001  |  Hello from hello-service!
  [3] -> http://localhost:8001  |  Hello from hello-service!
  [4] -> http://localhost:8002  |  Hello from hello-service!
  [5] -> http://localhost:8001  |  Hello from hello-service!
```

The client randomly selects between the two instances on each call, demonstrating load spreading via service discovery.

---

## Expected Program Behavior

| What happens | Why |
|---|---|
| Both instances appear in discovery results | They both called `POST /register` on startup |
| Client calls alternate between ports 8001 and 8002 | Client picks a random instance from the registry response each call |
| After Ctrl-C on an instance, it disappears from the registry | Instance calls `POST /deregister` on graceful shutdown |
| If an instance is killed hard, it disappears within 30 s | Registry's background cleanup removes instances with stale heartbeats |

---

## Files

| File | Description |
|------|-------------|
| `service_registry_improved.py` | Central registry server (port 5001) |
| `example_service.py` | Service instance — registers, sends heartbeats, serves HTTP |
| `client.py` | Discovery client — finds instances, calls a random one |
| `requirements.txt` | Python dependencies (Flask, requests) |
| `Dockerfile` | Container image for the registry |
| `k8s/` | Kubernetes manifests |
| `ARCHITECTURE.md` | Architecture diagram |

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/register` | Register a service instance |
| `POST` | `/heartbeat` | Keep an instance alive |
| `POST` | `/deregister` | Remove an instance |
| `GET` | `/discover/<name>` | Get all active instances of a service |
| `GET` | `/services` | List all registered services |
| `GET` | `/health` | Registry health check |

### Register
```bash
curl -X POST http://localhost:5001/register \
  -H "Content-Type: application/json" \
  -d '{"service": "hello-service", "address": "http://localhost:8001"}'
```

### Discover
```bash
curl http://localhost:5001/discover/hello-service
```

### List all services
```bash
curl http://localhost:5001/services
```

---

See [ARCHITECTURE.md](ARCHITECTURE.md) for the full architecture diagram.
