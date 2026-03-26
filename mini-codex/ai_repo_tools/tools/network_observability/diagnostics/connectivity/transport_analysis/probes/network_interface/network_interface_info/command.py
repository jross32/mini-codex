import json
import socket
import time
from typing import Dict, List, Tuple


def _collect_addresses(hostname: str) -> List[str]:
    addresses = set()
    try:
        infos = socket.getaddrinfo(hostname, None)
        for info in infos:
            if info and len(info) > 4 and info[4]:
                addresses.add(info[4][0])
    except Exception:
        pass

    for candidate in ("localhost", "127.0.0.1", "::1"):
        addresses.add(candidate)

    return sorted(addresses)


def run_network_interface_info(repo_path: str) -> Tuple[int, Dict]:
    _ = repo_path
    t0 = time.monotonic()
    hostname = socket.gethostname()
    fqdn = socket.getfqdn()
    addresses = _collect_addresses(hostname)

    payload = {
        "success": True,
        "tool": "network_interface_info",
        "hostname": hostname,
        "fqdn": fqdn,
        "addresses": addresses,
        "address_count": len(addresses),
        "elapsed_ms": round((time.monotonic() - t0) * 1000),
        "summary": f"Collected {len(addresses)} local address candidate(s).",
    }
    return 0, payload


def cmd_network_interface_info(repo_path: str):
    code, payload = run_network_interface_info(repo_path)
    print(json.dumps(payload))
    return code, payload
