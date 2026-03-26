import json
import statistics
import time
from typing import Dict, List, Optional, Tuple

from tools.discovery.fast_analyze.command import run_fast_analyze
from tools.planning.fast_process.command import _pick_followups, _pick_primary_orientation_doc, run_fast_process


def _legacy_fast_process(repo_path: str, max_files: Optional[int] = None) -> Tuple[int, Dict]:
    code, analysis = run_fast_analyze(repo_path, max_files=max_files)
    if code != 0:
        return code, analysis

    orientation_docs = analysis.get("orientation_docs", [])
    orientation_refs = analysis.get("orientation_references", {})
    primary_doc = _pick_primary_orientation_doc(orientation_docs)
    followups = _pick_followups(primary_doc, orientation_refs)
    top_extensions = analysis.get("top_extensions", [])
    top_ext = top_extensions[0].get("ext", "unknown") if top_extensions else "unknown"

    payload = {
        "success": True,
        "primary_orientation_doc": primary_doc,
        "recommended_followups": followups,
        "dominant_extension": top_ext,
    }
    return 0, payload


def _bench_once(fn, repo_path: str, max_files: Optional[int]) -> float:
    t0 = time.perf_counter()
    code, payload = fn(repo_path, max_files=max_files)
    if code != 0:
        raise RuntimeError(f"benchmark target failed: {payload}")
    return time.perf_counter() - t0


def _summarize(samples: List[float]) -> Dict:
    sorted_samples = sorted(samples)
    n = len(sorted_samples)
    p95_idx = max(0, int(0.95 * (n - 1)))
    return {
        "runs": n,
        "mean_s": round(statistics.mean(sorted_samples), 6),
        "median_s": round(statistics.median(sorted_samples), 6),
        "p95_s": round(sorted_samples[p95_idx], 6),
        "min_s": round(sorted_samples[0], 6),
        "max_s": round(sorted_samples[-1], 6),
    }


def _gain(old_s: float, new_s: float) -> Dict:
    if old_s <= 0 or new_s <= 0:
        return {"pct": 0.0, "multiplier": 1.0}
    return {
        "pct": round(((old_s - new_s) / old_s) * 100.0, 2),
        "multiplier": round(old_s / new_s, 3),
    }


def run_bench_compare(
    repo_path: str,
    max_files: Optional[int] = None,
    runs: int = 12,
    warmups: int = 1,
) -> Tuple[int, Dict]:
    if runs <= 1:
        return 2, {"success": False, "error": "invalid_argument", "detail": "runs must be > 1"}
    if warmups < 0:
        return 2, {"success": False, "error": "invalid_argument", "detail": "warmups must be >= 0"}

    for _ in range(warmups):
        _bench_once(_legacy_fast_process, repo_path, max_files)
        _bench_once(run_fast_process, repo_path, max_files)

    old_samples: List[float] = []
    new_samples: List[float] = []
    for _ in range(runs):
        old_samples.append(_bench_once(_legacy_fast_process, repo_path, max_files))
        new_samples.append(_bench_once(run_fast_process, repo_path, max_files))

    old_stats = _summarize(old_samples)
    new_stats = _summarize(new_samples)

    gain = {
        "mean": _gain(old_stats["mean_s"], new_stats["mean_s"]),
        "median": _gain(old_stats["median_s"], new_stats["median_s"]),
        "p95": _gain(old_stats["p95_s"], new_stats["p95_s"]),
    }

    payload = {
        "success": True,
        "repo_path": repo_path,
        "benchmark_mode": "legacy_vs_fast_process",
        "max_files": max_files,
        "runs": runs,
        "warmups": warmups,
        "legacy": old_stats,
        "current": new_stats,
        "gain": gain,
        "summary": (
            f"fast_process mean gain={gain['mean']['pct']}% ({gain['mean']['multiplier']}x), "
            f"p95 gain={gain['p95']['pct']}% ({gain['p95']['multiplier']}x)."
        ),
    }
    return 0, payload


def cmd_bench_compare(
    repo_path: str,
    max_files: Optional[int] = None,
    runs: int = 12,
    warmups: int = 1,
):
    code, payload = run_bench_compare(repo_path, max_files=max_files, runs=runs, warmups=warmups)
    print(json.dumps(payload))
    return code, payload
