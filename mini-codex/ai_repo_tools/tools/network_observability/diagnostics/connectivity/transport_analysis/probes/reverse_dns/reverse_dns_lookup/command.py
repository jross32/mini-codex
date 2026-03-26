import json
import socket
import time
from typing import Dict, Tuple


def run_reverse_dns_lookup(repo_path: str, ip: str) -> Tuple[int, Dict]:
    _ = repo_path
    t0 = time.monotonic()
    try:
        hostname, aliases, addresses = socket.gethostbyaddr(ip)
    except Exception as exc:
        return 1, {
            "success": False,
            "tool": "reverse_dns_lookup",
            "ip": ip,
            "error": str(exc),
            "elapsed_ms": round((time.monotonic() - t0) * 1000),
            "summary": f"Reverse DNS lookup failed for {ip}.",
        }

    payload = {
        "success": True,
        "tool": "reverse_dns_lookup",
        "ip": ip,
        "hostname": hostname,
        "aliases": aliases,
        "addresses": addresses,
        "elapsed_ms": round((time.monotonic() - t0) * 1000),
        "summary": f"Reverse DNS resolved {ip} to {hostname}.",
    }
    return 0, payload


def cmd_reverse_dns_lookup(repo_path: str, ip: str):
    code, payload = run_reverse_dns_lookup(repo_path, ip)
    print(json.dumps(payload))
    return code, payload
