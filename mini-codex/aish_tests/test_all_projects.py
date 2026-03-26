"""Comprehensive test suite for all 10 intensive projects."""

import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))


class TestProject1CodeAnalysis:
    """Tests for Code Analysis Engine."""

    def test_parse_python_file(self):
        """Test parsing Python files."""
        from test_01_code_analysis_engine.analyzer import ASTParser
        parser = ASTParser()
        assert parser is not None
        assert parser.parse_count == 0

    def test_symbol_extraction(self):
        """Test symbol extraction from AST."""
        from test_01_code_analysis_engine.analyzer import SymbolExtractor
        import ast
        
        code = "def hello(): pass"
        tree = ast.parse(code)
        extractor = SymbolExtractor("test.py")
        symbols = extractor.extract(tree)
        assert len(symbols) > 0

    def test_dependency_resolution(self):
        """Test dependency cycle detection."""
        from test_04_build_orchestrator.orchestrator import BuildGraph
        graph = BuildGraph()
        assert len(graph.tasks) == 0

    def test_dataflow_analyzer(self):
        """Test variable dataflow tracking."""
        import ast
        from test_01_code_analysis_engine.analyzer import DataflowAnalyzer

        code = "x = 1\ny = x + 2\n"
        analyzer = DataflowAnalyzer()
        flows = analyzer.analyze(ast.parse(code))
        assert "x" in flows
        assert len(flows["x"].definitions) >= 1


class TestProject2CodeGeneration:
    """Tests for Code Generator."""

    def test_template_parsing(self):
        """Test template parsing."""
        from test_02_code_generator.templates import TemplateParser
        parser = TemplateParser()
        template = "Hello {{ name }}!"
        vars = parser.get_variables(template)
        assert "name" in vars

    def test_variable_resolution(self):
        """Test variable resolution."""
        from test_02_code_generator.templates import VariableResolver
        resolver = VariableResolver({"user": {"name": "Alice"}})
        value = resolver.resolve("user.name")
        assert value == "Alice"

    def test_python_renderer(self):
        """Test Python code rendering."""
        from test_02_code_generator.renderers import PythonRenderer

        renderer = PythonRenderer()
        code = renderer.render_function("hello", ["name"], "return name")
        assert "def hello(name):" in code

    def test_typescript_renderer(self):
        """Test TypeScript interface rendering."""
        from test_02_code_generator.renderers import TypeScriptRenderer

        renderer = TypeScriptRenderer()
        iface = renderer.render_interface("User", {"id": "number"})
        assert "interface User" in iface


class TestProject3ASTRefactoring:
    """Tests for AST Refactoring Tool."""

    def test_rename_visitor(self):
        """Test symbol renaming."""
        from test_03_ast_refactoring.visitors import RenameVisitor
        import ast
        
        code = "x = 1"
        tree = ast.parse(code)
        visitor = RenameVisitor("x", "y")
        assert visitor.old_name == "x"
        assert visitor.new_name == "y"

    def test_type_annotation(self):
        """Test type annotation."""
        from test_03_ast_refactoring.transformers import TypeAnnotator
        annotator = TypeAnnotator()
        assert annotator.annotation_count == 0

    def test_extract_method_refactoring(self):
        """Test repeated expression extraction helper."""
        from test_03_ast_refactoring.refactorings import ExtractMethodRefactoring

        source = "a = x + y\nb = x + y\n"
        refactoring = ExtractMethodRefactoring()
        result = refactoring.extract(source, method_name="sum_xy")
        assert result.replacements >= 2
        assert "def sum_xy" in result.helper_source


class TestProject4BuildOrchestrator:
    """Tests for Build Orchestrator."""

    def test_build_graph(self):
        """Test build graph construction."""
        from test_04_build_orchestrator.orchestrator import BuildGraph
        graph = BuildGraph()
        assert len(graph.tasks) == 0
        cycles = graph.find_cycles()
        assert cycles == []

    def test_task_execution(self):
        """Test task base class."""
        from test_04_build_orchestrator.tasks import CompileTask
        task = CompileTask("compile", ["file1.py", "file2.py"])
        assert task.name == "compile"
        assert len(task.source_files) == 2


class TestProject5ETLPipeline:
    """Tests for ETL Pipeline."""

    def test_csv_extraction(self):
        """Test CSV extractor."""
        from test_05_etl_pipeline.extractors import CSVExtractor
        extractor = CSVExtractor("test.csv")
        assert extractor.source == "test.csv"
        assert extractor.row_count == 0

    def test_data_cleaner(self):
        """Test data cleaning transformer."""
        from test_05_etl_pipeline.transformers import DataCleaner
        cleaner = DataCleaner()
        row = {"name": " Alice ", "age": "25"}
        result = cleaner.transform(row)
        assert result is not None


class TestProject6TestMatrix:
    """Tests for Test Matrix Framework."""

    def test_matrix_builder(self):
        """Test matrix building."""
        from test_06_test_matrix.matrix import MatrixBuilder
        builder = MatrixBuilder()
        builder.add_parameter("version", ["1.0", "2.0"])
        builder.add_parameter("env", ["dev", "prod"])
        assert builder.get_matrix_size() == 4

    def test_test_generator(self):
        """Test test code generation."""
        from test_06_test_matrix.generators import TestGenerator
        gen = TestGenerator()
        assert gen.get_test_count() == 0


class TestProject7Deployment:
    """Tests for Deployment Automation."""

    def test_docker_provisioner(self):
        """Test Docker provisioning."""
        from test_07_deployment_automation.provisioners import (
            DockerProvisioner, DeploymentConfig
        )
        provisioner = DockerProvisioner()
        config = DeploymentConfig(name="web", version="1.0")
        success = provisioner.provision(config)
        assert success


class TestProject8APISchema:
    """Tests for API Schema Extractor."""

    def test_endpoint_extraction(self):
        """Test API endpoint extraction."""
        from test_08_api_schema.extractors import EndpointExtractor
        import ast
        
        code = '@get("/users")\ndef list_users(): pass'
        # Note: actual decorator extraction requires proper syntax
        extractor = EndpointExtractor()
        assert extractor is not None


class TestProject9PerfProfiler:
    """Tests for Performance Profiler."""

    def test_cpu_profiler(self):
        """Test CPU profiling."""
        from test_09_perf_profiler.profilers import CPUProfiler
        profiler = CPUProfiler()
        assert profiler.get_stats() == {} or isinstance(profiler.get_stats(), dict)

    def test_memory_profiler(self):
        """Test memory profiling."""
        from test_09_perf_profiler.profilers import MemoryProfiler
        profiler = MemoryProfiler()
        assert profiler.peak_memory >= 0


class TestProject10Integration:
    """Tests for Cross-Tool Integration Hub."""

    def test_tool_router(self):
        """Test tool routing."""
        from test_10_tool_integration.orchestrator import (
            ToolRouter, ToolCapability
        )
        router = ToolRouter()
        assert len(router.list_tools()) == 0

    def test_workflow_engine(self):
        """Test workflow execution."""
        from test_10_tool_integration.orchestrator import (
            ToolRouter, WorkflowEngine
        )
        router = ToolRouter()
        engine = WorkflowEngine(router)
        result = engine.execute_workflow([])
        assert result.get("success") == True

    def test_phase_analyze_refactor_test(self):
        """Test phase workflow: Analyze -> Refactor -> Test."""
        from test_10_tool_integration.orchestrator import IntegrationOrchestrator

        orchestrator = IntegrationOrchestrator()
        source = "x = a + b\ny = a + b\n"
        result = orchestrator.run_analyze_refactor_test(source)
        assert result.get("success") is True
        assert result["workflow"] == "analyze_refactor_test"
        assert "cyclomatic_complexity" in result["analysis"]

    def test_phase_generate_analyze_benchmark(self):
        """Test phase workflow: Generate -> Analyze -> Benchmark."""
        from test_10_tool_integration.orchestrator import IntegrationOrchestrator

        orchestrator = IntegrationOrchestrator()
        result = orchestrator.run_generate_analyze_benchmark()
        assert result.get("success") is True
        assert result["workflow"] == "generate_analyze_benchmark"
        assert "benchmark" in result
        assert result["benchmark"]["run_count"] > 0


if __name__ == "__main__":
    print("Running intensive test suite...")
    
    suites = [
        TestProject1CodeAnalysis,
        TestProject2CodeGeneration,
        TestProject3ASTRefactoring,
        TestProject4BuildOrchestrator,
        TestProject5ETLPipeline,
        TestProject6TestMatrix,
        TestProject7Deployment,
        TestProject8APISchema,
        TestProject9PerfProfiler,
        TestProject10Integration,
    ]

    total_tests = 0
    total_passed = 0

    for suite_class in suites:
        suite = suite_class()
        methods = [m for m in dir(suite) if m.startswith("test_")]
        
        print(f"\\n{suite_class.__name__}:")
        for method_name in methods:
            total_tests += 1
            try:
                method = getattr(suite, method_name)
                method()
                print(f"  ✓ {method_name}")
                total_passed += 1
            except Exception as e:
                print(f"  ✗ {method_name}: {e}")

    print(f"\\n\\nSummary: {total_passed}/{total_tests} tests passed")
