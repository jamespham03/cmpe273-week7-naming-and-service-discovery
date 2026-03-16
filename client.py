"""
Service Discovery Client

Demonstrates the full service discovery loop:
  1. Query the registry for all instances of a service
  2. Pick a random instance
  3. Call that instance's /hello endpoint
  4. Repeat N times to show load spreading across instances

Usage:
  python client.py [service_name] [num_calls]

Examples:
  python client.py hello-service 5
  python client.py hello-service        # defaults to 5 calls
  python client.py                      # defaults to hello-service, 5 calls
"""

import sys
import random
import time
import requests

REGISTRY_URL = "http://localhost:5001"


def discover(service_name):
    """Return list of active instance dicts from the registry."""
    resp = requests.get(f"{REGISTRY_URL}/discover/{service_name}", timeout=5)
    if resp.status_code == 404:
        return []
    resp.raise_for_status()
    return resp.json().get("instances", [])


def call_instance(address):
    """Call /hello on the given instance address."""
    resp = requests.get(f"{address}/hello", timeout=5)
    resp.raise_for_status()
    return resp.json()


if __name__ == "__main__":
    service_name = sys.argv[1] if len(sys.argv) > 1 else "hello-service"
    num_calls = int(sys.argv[2]) if len(sys.argv) > 2 else 5

    print(f"Querying registry at {REGISTRY_URL} for '{service_name}'...\n")

    instances = discover(service_name)
    if not instances:
        print(f"No instances of '{service_name}' found. Is the service running?")
        sys.exit(1)

    print(f"Found {len(instances)} instance(s):")
    for inst in instances:
        print(f"  - {inst['address']}  (uptime: {inst['uptime_seconds']:.1f}s)")

    print(f"\nMaking {num_calls} calls, choosing a random instance each time:\n")
    for i in range(1, num_calls + 1):
        chosen = random.choice(instances)
        address = chosen["address"]
        try:
            result = call_instance(address)
            print(f"  [{i}] -> {address}  |  {result['message']}")
        except Exception as e:
            print(f"  [{i}] -> {address}  |  ERROR: {e}")
        time.sleep(0.3)
