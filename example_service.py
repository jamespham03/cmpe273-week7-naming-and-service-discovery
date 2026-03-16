"""
Service Instance

A microservice that:
  1. Starts a Flask HTTP server on the given port
  2. Registers itself with the service registry on startup
  3. Sends periodic heartbeats to stay alive in the registry
  4. Deregisters itself on graceful shutdown

Usage:
  python example_service.py <service_name> <port>

Examples:
  python example_service.py hello-service 8001
  python example_service.py hello-service 8002
"""

import sys
import signal
import time
import requests
from threading import Thread, Event
from flask import Flask, jsonify

REGISTRY_URL = "http://localhost:5001"
HEARTBEAT_INTERVAL = 10  # seconds

app = Flask(__name__)

service_name = None
service_port = None
stop_event = Event()


# ---------------------------------------------------------------------------
# HTTP endpoints served by this instance
# ---------------------------------------------------------------------------

@app.route("/hello")
def hello():
    return jsonify({
        "message": f"Hello from {service_name}!",
        "instance": f"http://localhost:{service_port}",
        "port": service_port,
    })


@app.route("/health")
def health():
    return jsonify({"status": "healthy", "service": service_name, "port": service_port})


# ---------------------------------------------------------------------------
# Registry interactions
# ---------------------------------------------------------------------------

def _address():
    return f"http://localhost:{service_port}"


def register():
    try:
        resp = requests.post(
            f"{REGISTRY_URL}/register",
            json={"service": service_name, "address": _address()},
            timeout=5,
        )
        if resp.status_code in (200, 201):
            print(f"[{service_name}:{service_port}] Registered with registry")
            return True
        print(f"[{service_name}:{service_port}] Registration failed ({resp.status_code}): {resp.text}")
        return False
    except requests.exceptions.ConnectionError:
        print(f"[{service_name}:{service_port}] Cannot reach registry at {REGISTRY_URL}")
        return False
    except Exception as e:
        print(f"[{service_name}:{service_port}] Registration error: {e}")
        return False


def deregister():
    try:
        requests.post(
            f"{REGISTRY_URL}/deregister",
            json={"service": service_name, "address": _address()},
            timeout=5,
        )
        print(f"[{service_name}:{service_port}] Deregistered from registry")
    except Exception as e:
        print(f"[{service_name}:{service_port}] Deregistration error: {e}")


def heartbeat_loop():
    while not stop_event.wait(HEARTBEAT_INTERVAL):
        try:
            requests.post(
                f"{REGISTRY_URL}/heartbeat",
                json={"service": service_name, "address": _address()},
                timeout=5,
            )
            print(f"[{service_name}:{service_port}] Heartbeat sent")
        except Exception as e:
            print(f"[{service_name}:{service_port}] Heartbeat error: {e}")


def shutdown(sig, frame):
    print(f"\n[{service_name}:{service_port}] Shutting down gracefully...")
    stop_event.set()
    deregister()
    sys.exit(0)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python example_service.py <service_name> <port>")
        print("\nExample:")
        print("  python example_service.py hello-service 8001")
        sys.exit(1)

    service_name = sys.argv[1]
    service_port = int(sys.argv[2])

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    if not register():
        sys.exit(1)

    Thread(target=heartbeat_loop, daemon=True).start()

    print(f"[{service_name}:{service_port}] Running — GET /hello  GET /health")
    app.run(host="0.0.0.0", port=service_port)
