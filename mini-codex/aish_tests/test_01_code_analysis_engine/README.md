# Test Project 1: Code Analysis Engine

**Purpose**: Build a comprehensive static code analysis system to test AST parsing, graph analysis, and report generation tools.

**Complexity**: High - multi-module dependency resolution, symbol tracking, cross-file analysis.

**Tools to Test**:
- Code parsing and AST manipulation
- Symbol graph construction
- Dependency tracking
- Multi-file analysis and aggregation
- Report generation and formatting

## Architecture

- `analyzer/` - Core analysis engine
  - `ast_parser.py` - Parse Python code to AST
  - `symbol_extractor.py` - Extract symbols (classes, functions, variables)
  - `dependency_resolver.py` - Build dependency graph
  - `metrics_calculator.py` - Calculate code metrics (cyclomatic complexity, coupling)

- `graph/` - Graph data structures
  - `symbol_graph.py` - Symbol relationship graph
  - `dependency_graph.py` - Dependency relationships
  - `query_engine.py` - Query capabilities

- `reporters/` - Report generation
  - `base_reporter.py` - Reporter interface
  - `json_reporter.py` - JSON output
  - `html_reporter.py` - HTML visualization
  - `summary_reporter.py` - Executive summary

- `config/` - Configuration management
  - `defaults.py` - Default settings
  - `validators.py` - Config validation

- `tests/` - Full test suite covering edge cases

## Test Scenarios

1. Analyze large multi-file project (>100 files)
2. Track circular dependencies
3. Generate dependency warnings
4. Cross-module reference tracking
5. Performance on 1000+ symbol project
