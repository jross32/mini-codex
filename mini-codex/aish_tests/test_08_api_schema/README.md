# Test Project 8: API Schema Extractor

**Purpose**: Build a comprehensive API documentation extraction and validation system.

**Complexity**: High - AST parsing, schema inference, validation rules, multi-format support.

**Tools to Test**:
- Extract API schemas from code
- Generate OpenAPI/AsyncAPI schemas
- Validate API contracts
- Cross-service validation

## Architecture

- `extractors/` - Schema extraction
  - `endpoint_extractor.py` - Extract endpoints
  - `model_extractor.py` - Extract data models
  - `schema_builder.py` - Build schemas

- `validators/` - Schema validation
  - `schema_validator.py` - Validate schemas
  - `contract_checker.py` - Check contracts
  - `consistency_checker.py` - Check consistency

- `generators/` - Schema generation
  - `openapi_generator.py` - Generate OpenAPI docs
  - `asyncapi_generator.py` - Generate AsyncAPI docs
  - `markdown_generator.py` - Generate Markdown docs

## Test Scenarios

1. Extract schemas from 100+ endpoints
2. Generate OpenAPI 3.0 specifications
3. Validate request/response schemas
4. Cross-service contract checking
5. Documentation generation
