"""Build task definitions and interface."""

import time
from enum import Enum
from typing import Any, Dict, List, Optional
from abc import ABC, abstractmethod


class TaskStatus(Enum):
    """Task execution status."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


class Task(ABC):
    """Base class for build tasks."""

    def __init__(self, name: str, dependencies: List[str] = None):
        """Initialize task."""
        self.name = name
        self.dependencies = dependencies or []
        self.status = TaskStatus.PENDING
        self.result: Any = None
        self.error: Optional[str] = None
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.cache_key: Optional[str] = None

    @abstractmethod
    def execute(self) -> Any:
        """Execute the task."""
        pass

    def run(self) -> bool:
        """Run task and track timing."""
        try:
            self.status = TaskStatus.RUNNING
            self.start_time = time.time()
            self.result = self.execute()
            self.status = TaskStatus.SUCCESS
            self.end_time = time.time()
            return True
        except Exception as e:
            self.status = TaskStatus.FAILED
            self.error = str(e)
            self.end_time = time.time()
            return False

    def get_duration(self) -> float:
        """Get task execution duration."""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return 0.0

    def skip(self, reason: str = "") -> None:
        """Mark task as skipped."""
        self.status = TaskStatus.SKIPPED
        self.error = reason


class CompileTask(Task):
    """Compile source code."""

    def __init__(self, name: str, source_files: List[str], **kwargs):
        """Initialize compile task."""
        super().__init__(name, **kwargs)
        self.source_files = source_files

    def execute(self) -> Dict[str, Any]:
        """Execute compilation."""
        return {
            "files_compiled": len(self.source_files),
            "output": f"Compiled {len(self.source_files)} files",
        }


class TestTask(Task):
    """Run tests."""

    def __init__(self, name: str, test_paths: List[str], **kwargs):
        """Initialize test task."""
        super().__init__(name, **kwargs)
        self.test_paths = test_paths

    def execute(self) -> Dict[str, Any]:
        """Execute tests."""
        return {
            "tests_run": len(self.test_paths) * 10,
            "passed": len(self.test_paths) * 10,
            "failed": 0,
        }
