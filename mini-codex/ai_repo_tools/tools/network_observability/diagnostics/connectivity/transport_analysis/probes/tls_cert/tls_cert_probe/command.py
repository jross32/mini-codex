import json
import socket
import ssl
import time
from typing import Dict, Tuple


def run_tls_cert_probe(repo_path: str, host: str, port: int = 443, timeout_seconds: int = 8) -> Tuple[int, Dict]:
    _ = repo_path
    t0 = time.monotonic()

    context = ssl.create_default_context()
    try:
        with socket.create_connection((host, int(port)), timeout=max(1, int(timeout_seconds))) as sock:
            with context.wrap_socket(sock, server_hostname=host) as tls_sock:
                cert = tls_sock.getpeercert()
    except Exception as exc:
        return 1, {
            "success": False,
            "tool": "tls_cert_probe",
            "host": host,
            "port": port,
            "timeout_seconds": timeout_seconds,
            "error": str(exc),
            "elapsed_ms": round((time.monotonic() - t0) * 1000),
            "summary": f"TLS cert probe failed for {host}:{port}.",
        }

    payload = {
        "success": True,
        "tool": "tls_cert_probe",
        "host": host,
        "port": port,
        "subject": cert.get("subject"),
        "issuer": cert.get("issuer"),
        "serial_number": cert.get("serialNumber"),
        "not_before": cert.get("notBefore"),
        "not_after": cert.get("notAfter"),
        "subject_alt_name": cert.get("subjectAltName"),
        "elapsed_ms": round((time.monotonic() - t0) * 1000),
        "summary": f"TLS cert probe completed for {host}:{port}.",
    }
    return 0, payload


def cmd_tls_cert_probe(repo_path: str, host: str, port: int = 443, timeout_seconds: int = 8):
    code, payload = run_tls_cert_probe(repo_path, host, port, timeout_seconds)
    print(json.dumps(payload))
    return code, payload
