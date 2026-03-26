# Test Project 3: AST Refactoring Tool

**Purpose**: Build a sophisticated AST-based code transformation and refactoring system.

**Complexity**: High - visitor patterns, transformation rules, code preservation, safety analysis.

**Tools to Test**:
- AST transformation and rewriting
- Preservation of code structure and formatting
- Safety analysis for refactorings
- Complex pattern matching

## Architecture

- `visitors/` - AST visitor implementations
  - `visitor_base.py` - Base visitor pattern
  - `rename_visitor.py` - Rename refactoring
  - `extract_visitor.py` - Extract method refactoring

- `transformers/` - Code transformations
  - `type_annotator.py` - Add type hints
  - `simplifier.py` - Simplify expressions
  - `optimizer.py` - Optimize code patterns

- `safety/` - Safety analysis
  - `validator.py` - Validate transformations
  - `impact_analyzer.py` - Analyze change impact
  - `conflict_detector.py` - Detect conflicts

## Test Scenarios

1. Rename symbols across 50+ files with 1000+ references
2. Extract methods with complex controls flow
3. Add type hints with inference
4. Optimize nested loops and conditionals
5. Multi-file refactoring with dependency tracking
