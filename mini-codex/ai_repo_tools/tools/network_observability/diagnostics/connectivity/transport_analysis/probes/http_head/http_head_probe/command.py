import json
import time
import urllib.error
import urllib.request
from typing import Dict, Tuple


def run_http_head_probe(repo_path: str, url: str, timeout_seconds: int = 8) -> Tuple[int, Dict]:
    _ = repo_path
    t0 = time.monotonic()
    request = urllib.request.Request(url, method="HEAD")
    try:
        with urllib.request.urlopen(request, timeout=max(1, int(timeout_seconds))) as resp:
            headers = dict(resp.headers.items())
            status_code = int(getattr(resp, "status", 0) or 0)
    except urllib.error.HTTPError as exc:
        headers = dict(exc.headers.items()) if exc.headers else {}
        status_code = int(exc.code)
    except Exception as exc:
        return 1, {
            "success": False,
            "tool": "http_head_probe",
            "url": url,
            "timeout_seconds": timeout_seconds,
            "error": str(exc),
            "elapsed_ms": round((time.monotonic() - t0) * 1000),
            "summary": f"HTTP HEAD probe failed for {url}.",
        }

    payload = {
        "success": True,
        "tool": "http_head_probe",
        "url": url,
        "timeout_seconds": timeout_seconds,
        "status_code": status_code,
        "headers": headers,
        "elapsed_ms": round((time.monotonic() - t0) * 1000),
        "summary": f"HTTP HEAD probe completed for {url} with status {status_code}.",
    }
    return 0, payload


def cmd_http_head_probe(repo_path: str, url: str, timeout_seconds: int = 8):
    code, payload = run_http_head_probe(repo_path, url, timeout_seconds)
    print(json.dumps(payload))
    return code, payload
