"""Tool routing and orchestration."""

import ast
import time
from typing import Dict, Any, List, Optional, Type
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ToolCapability:
    """Describes a tool's capability."""
    tool_name: str
    description: str
    input_types: List[str]
    output_types: List[str]
    performance_tier: str  # "fast", "medium", "slow"


class ToolRouter:
    """Route tasks to appropriate tools."""

    def __init__(self):
        """Initialize router."""
        self.tools: Dict[str, ToolCapability] = {}
        self.tool_registry: Dict[str, Type] = {}

    def register_tool(self, name: str, capability: ToolCapability, 
                     tool_class: Type) -> None:
        """Register a tool."""
        self.tools[name] = capability
        self.tool_registry[name] = tool_class

    def select_tool(self, task_type: str, constraints: Dict[str, Any] = None
                   ) -> Optional[str]:
        """Select best tool for task."""
        constraints = constraints or {}

        candidates = []
        for tool_name, tool in self.tools.items():
            if task_type in tool.output_types:
                # Score based on constraints
                score = 0
                if tool.performance_tier == "fast":
                    score += 3
                elif tool.performance_tier == "medium":
                    score += 2

                candidates.append((tool_name, score))

        if not candidates:
            return None

        # Return best scoring tool
        return max(candidates, key=lambda x: x[1])[0]

    def get_tool_info(self, tool_name: str) -> Optional[ToolCapability]:
        """Get tool information."""
        return self.tools.get(tool_name)

    def list_tools(self) -> List[str]:
        """List registered tools."""
        return list(self.tools.keys())

    def get_tools_for_output(self, output_type: str) -> List[str]:
        """Get tools that produce specific output type."""
        return [name for name, tool in self.tools.items()
               if output_type in tool.output_types]


class WorkflowEngine:
    """Execute multi-tool workflows."""

    def __init__(self, router: ToolRouter):
        """Initialize workflow engine."""
        self.router = router
        self.execution_history: List[Dict[str, Any]] = []

    def execute_workflow(self, steps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute a workflow of tool invocations."""
        results = {}

        for i, step in enumerate(steps):
            tool_name = step.get("tool")
            if not tool_name:
                continue

            inputs = step.get("inputs", {})
            tool_capability = self.router.get_tool_info(tool_name)

            if not tool_capability:
                return {"error": f"Tool not found: {tool_name}", "step": i}

            # Simulate tool execution
            result = {
                "tool": tool_name,
                "step": i,
                "status": "success",
                "data": inputs,
            }

            results[step.get("name", f"step_{i}")] = result
            self.execution_history.append(result)

        return {"success": True, "results": results}

    def get_execution_history(self) -> List[Dict[str, Any]]:
        """Get workflow execution history."""
        return self.execution_history


class IntegrationOrchestrator:
    """Execute concrete cross-project phase workflows."""

    def run_analyze_refactor_test(self, source: str) -> Dict[str, Any]:
        """Run phase workflow: Analyze -> Refactor -> Test."""
        from test_01_code_analysis_engine.analyzer import MetricsCalculator
        from test_03_ast_refactoring.refactorings import ExtractMethodRefactoring

        tree = ast.parse(source)
        metrics = MetricsCalculator().calculate(tree)

        extractor = ExtractMethodRefactoring()
        extraction = extractor.extract(source, method_name="phase_extracted")

        # Lightweight validation test: produced helper should compile if present.
        compile_ok = True
        if extraction.helper_source:
            try:
                compile(extraction.helper_source, "<extracted>", "exec")
            except SyntaxError:
                compile_ok = False

        return {
            "success": compile_ok,
            "workflow": "analyze_refactor_test",
            "analysis": metrics,
            "refactor": {
                "extracted_name": extraction.extracted_name,
                "replacements": extraction.replacements,
            },
            "tests": {
                "compile_extracted_helper": compile_ok,
            },
        }

    def run_generate_analyze_benchmark(self) -> Dict[str, Any]:
        """Run phase workflow: Generate -> Analyze -> Benchmark."""
        from test_02_code_generator.renderers import PythonRenderer
        from test_01_code_analysis_engine.analyzer import ASTParser, MetricsCalculator

        renderer = PythonRenderer()
        generated = renderer.render_function(
            name="generated_fn",
            params=["x", "y"],
            body="return x + y",
        )

        parser = ASTParser()
        tree = parser.parse_source(generated, filename="<generated>")
        metrics = MetricsCalculator().calculate(tree) if tree else {}

        # Benchmark report uses baseline/current + delta fields expected by policy.
        run_count = 5
        warmups = 1
        baseline = self._measure_parse_time("def a(x):\n    return x\n", run_count, warmups)
        current = self._measure_parse_time(generated, run_count, warmups)
        gain_pct = ((baseline - current) / baseline * 100.0) if baseline > 0 else 0.0
        multiplier = (baseline / current) if current > 0 else float("inf")

        return {
            "success": tree is not None,
            "workflow": "generate_analyze_benchmark",
            "generated_code": generated,
            "analysis": metrics,
            "benchmark": {
                "baseline": baseline,
                "current": current,
                "percentage_gain": gain_pct,
                "multiplier": multiplier,
                "run_count": run_count,
                "warmups": warmups,
                "max_files": 1,
            },
        }

    def _measure_parse_time(self, source: str, run_count: int, warmups: int) -> float:
        """Measure average AST parse time for source."""
        for _ in range(warmups):
            ast.parse(source)

        start = time.perf_counter()
        for _ in range(run_count):
            ast.parse(source)
        elapsed = time.perf_counter() - start
        return elapsed / max(1, run_count)
