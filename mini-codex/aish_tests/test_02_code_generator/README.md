# Test Project 2: Code Generator

**Purpose**: Build a sophisticated code generation system with templates, variable resolution, and multi-language support.

**Complexity**: High - template engines, rendering pipelines, variable scoping, code formatting.

**Tools to Test**:
- Template parsing and AST generation
- Variable resolution and scoping
- Code rendering and formatting
- Multi-language support
- Batch rendering and validation

## Architecture

- `templates/` - Template management
  - `template_parser.py` - Parse template DSL
  - `template_store.py` - Template storage and retrieval
  - `variable_resolver.py` - Resolve template variables

- `renderers/` - Code rendering
  - `base_renderer.py` - Renderer interface
  - `python_renderer.py` - Python code generation
  - `typescript_renderer.py` - TypeScript generation
  - `sql_renderer.py` - SQL generation

- `pipeline/` - Generation pipeline
  - `pipeline.py` - Orchestrate generation steps
  - `validator.py` - Validate generated code
  - `formatter.py` - Format output

## Test Scenarios

1. Generate 100+ functions from templates
2. Complex variable interpolation
3. Multi-language generation from single template
4. Nested template composition
5. Performance under batch generation (1000 files)
