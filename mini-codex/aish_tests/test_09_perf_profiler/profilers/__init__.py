"""CPU and performance profiling."""

import cProfile
import pstats
import io
from typing import Dict, Any, Callable, Optional
from contextlib import contextmanager


class CPUProfiler:
    """Profile CPU usage of functions."""

    def __init__(self):
        """Initialize profiler."""
        self.profiler: Optional[cProfile.Profile] = None
        self.stats: Optional[pstats.Stats] = None

    @contextmanager
    def profile(self, name: str = "profile"):
        """Context manager for profiling."""
        self.profiler = cProfile.Profile()
        self.profiler.enable()
        try:
            yield self.profiler
        finally:
            self.profiler.disable()
            s = io.StringIO()
            self.stats = pstats.Stats(self.profiler, stream=s)
            self.stats.strip_dirs()
            self.stats.sort_stats('cumulative')

    def get_top_functions(self, n: int = 10) -> list:
        """Get top N functions by time."""
        if not self.stats:
            return []
        s = io.StringIO()
        self.stats.stream = s
        self.stats.print_stats(n)
        return s.getvalue().split('\\n')

    def get_stats(self) -> Dict[str, Any]:
        """Get profiling statistics."""
        if not self.stats:
            return {}
        return {
            "total_calls": sum(v[1] for v in self.stats.stats.values()),
            "total_time": sum(v[3] for v in self.stats.stats.values()),
        }


class MemoryProfiler:
    """Track memory usage."""

    def __init__(self):
        """Initialize memory profiler."""
        self.peak_memory = 0
        self.snapshots: list = []

    def take_snapshot(self) -> Dict[str, Any]:
        """Take memory snapshot."""
        try:
            import tracemalloc
            if not tracemalloc.is_tracing():
                tracemalloc.start()

            current, peak = tracemalloc.get_traced_memory()
            self.peak_memory = max(self.peak_memory, current)

            snapshot = {
                "current_mb": current / 1024 / 1024,
                "peak_mb": peak / 1024 / 1024,
            }
            self.snapshots.append(snapshot)
            return snapshot
        except Exception:
            return {}

    def get_peak_memory(self) -> float:
        """Get peak memory usage in MB."""
        return self.peak_memory / 1024 / 1024

    def detect_leaks(self, threshold_mb: float = 100.0) -> bool:
        """Detect potential memory leaks."""
        if len(self.snapshots) < 2:
            return False

        growth = (self.snapshots[-1]["current_mb"] -
                 self.snapshots[0]["current_mb"])
        return growth > threshold_mb
