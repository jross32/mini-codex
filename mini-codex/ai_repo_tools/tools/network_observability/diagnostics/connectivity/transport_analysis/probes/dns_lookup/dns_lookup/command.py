import json
import socket
import time
from typing import Dict, List, Tuple


def run_dns_lookup(repo_path: str, host: str, port: int = 443) -> Tuple[int, Dict]:
    _ = repo_path
    t0 = time.monotonic()
    try:
        infos = socket.getaddrinfo(host, port)
    except Exception as exc:
        return 1, {
            "success": False,
            "tool": "dns_lookup",
            "host": host,
            "port": port,
            "error": str(exc),
            "elapsed_ms": round((time.monotonic() - t0) * 1000),
            "summary": f"DNS lookup failed for {host}:{port}",
        }

    addresses: List[str] = sorted({entry[4][0] for entry in infos if entry and len(entry) > 4 and entry[4]})
    canonical = infos[0][3] if infos and len(infos[0]) > 3 else ""
    payload = {
        "success": True,
        "tool": "dns_lookup",
        "host": host,
        "port": port,
        "canonical_name": canonical,
        "addresses": addresses,
        "address_count": len(addresses),
        "elapsed_ms": round((time.monotonic() - t0) * 1000),
        "summary": f"Resolved {host} to {len(addresses)} address(es).",
    }
    return 0, payload


def cmd_dns_lookup(repo_path: str, host: str, port: int = 443):
    code, payload = run_dns_lookup(repo_path, host, port)
    print(json.dumps(payload))
    return code, payload
