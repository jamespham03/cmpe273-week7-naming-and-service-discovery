# Architecture

This project implements the **client-side service discovery** pattern:
services register themselves with a central registry, and clients query
the registry to find an available instance before making a call.

## System Diagram

```mermaid
flowchart TD
    subgraph Registry["Service Registry (port 5001)"]
        R[("fa:fa-database\nin-memory store\nhello-service: [A, B]")]
        R_API["POST /register\nPOST /heartbeat\nPOST /deregister\nGET  /discover/:name\nGET  /services\nGET  /health"]
    end

    subgraph InstanceA["hello-service — Instance A (port 8001)"]
        A["GET /hello\nGET /health"]
    end

    subgraph InstanceB["hello-service — Instance B (port 8002)"]
        B["GET /hello\nGET /health"]
    end

    subgraph Client["Client (client.py)"]
        C["1. discover hello-service\n3. print response"]
    end

    A -- "POST /register\nPOST /heartbeat every 10s" --> Registry
    B -- "POST /register\nPOST /heartbeat every 10s" --> Registry

    C -- "1. GET /discover/hello-service" --> Registry
    Registry -- "returns [A, B]" --> C
    C -- "2. call random instance" --> A
    C -- "2. call random instance" --> B
```

## Sequence Diagram

```mermaid
sequenceDiagram
    participant R as Registry :5001
    participant A as Instance A :8001
    participant B as Instance B :8002
    participant C as Client

    A->>R: POST /register {hello-service, :8001}
    R-->>A: 201 registered

    B->>R: POST /register {hello-service, :8002}
    R-->>B: 201 registered

    loop every 10s
        A->>R: POST /heartbeat
        B->>R: POST /heartbeat
    end

    C->>R: GET /discover/hello-service
    R-->>C: [{:8001, uptime}, {:8002, uptime}]

    loop N calls
        C->>C: pick random instance
        C->>A: GET /hello  (or B)
        A-->>C: {message, port}
    end

    A->>R: POST /deregister  (on Ctrl-C)
    B->>R: POST /deregister  (on Ctrl-C)
```

## Components

| File | Role |
|------|------|
| `service_registry_improved.py` | Central registry — stores service addresses, tracks heartbeats, cleans up stale entries |
| `example_service.py` | Service instance — Flask HTTP server that registers itself and sends heartbeats |
| `client.py` | Discovery client — queries registry, picks a random instance, calls it |

## Flow

1. **Registry starts** on port 5001 and begins a background cleanup thread (removes instances that miss heartbeats for > 30 s).

2. **Two service instances start** (e.g. ports 8001 and 8002). Each instance:
   - `POST /register` → tells the registry its name and address
   - Starts a background thread that `POST /heartbeat` every 10 s
   - Serves `GET /hello` and `GET /health` for incoming requests
   - `POST /deregister` on Ctrl-C before exiting

3. **Client runs** (`python client.py hello-service 5`):
   - `GET /discover/hello-service` → registry returns both instance addresses
   - For each of N calls: picks a random instance, calls `GET /hello`, prints the response
   - Random selection spreads load across instances

## Ports

| Process | Port |
|---------|------|
| Service Registry | 5001 |
| hello-service Instance A | 8001 |
| hello-service Instance B | 8002 |

## Health & Cleanup

- Each instance sends a heartbeat every **10 seconds**.
- The registry removes any instance whose last heartbeat is older than **30 seconds**.
- If an instance is killed without deregistering, it disappears automatically within 30 s.
