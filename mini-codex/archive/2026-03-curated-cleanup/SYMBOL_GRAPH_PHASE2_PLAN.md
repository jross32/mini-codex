# SYMBOL_GRAPH Phase 2 Plan

## Problem Statement

**Phase 1 (AISH) limitation**: File-aware but not system-aware. Can detect "which files exist and what agent reads" but cannot answer "what actual code relationships exist between files."

**Specific gap**:
- Import tracking: Phase 1 sees `from api import get_user` but doesn't know `get_user` is defined in `api/users.py`, not `api/__init__.py`
- Relationship discovery: Phase 1 finds files via repo_map; symbol_graph would find *connections* (e.g., "Controller → Service → Repository" patterns)
- Planner blindness: Agent picks files heuristically; symbol_graph would enable targeted file selection based on actual call graphs

**Why it matters**:
- Current benchmarks (Trade, apaR, myLife) all have deep architectural patterns (API layers, domain models, service interfaces)
- Agent currently learns these through expensive exploration (many tool calls to discover pattern)
- Symbol_graph could pre-compute these patterns, reducing agent steps

---

## Smallest Useful v0 Scope

**Inputs**:
- Repository root path
- List of Python files (or auto-discover from repo_map)

**Outputs** (deterministic, file-scoped only):
```json
{
  "symbols": {
    "file_path": {
      "imports": ["module.name", "other.func"],
      "exports": ["class_A", "function_b"],
      "internal_calls": [{"from": "class_A.method", "to": "function_b"}]
    }
  },
  "edges": [
    {"source": "api/users.py", "target": "models/user.py", "type": "import"},
    {"source": "services/auth.py", "target": "api/users.py", "type": "uses"}
  ]
}
```

**Scope constraints**:
- Parse Python AST only (stdlib `ast` module)
- Track top-level symbols and direct calls within files
- No cross-file inference or transitive closure
- No versioning, no delta tracking, no evolution
- Single snapshot per repo

**NOT included**:
- Type inference
- Dynamic dispatch resolution
- Package-level abstractions
- Caching or versioning

---

## Integration Shape

**Architecture placement**:
```
agent_loop
  ├─ planner (decides next step)
  ├─ tool_runner (executes tools)
  │   ├─ repo_map (file list)
  │   ├─ ai_read (file content)
  │   └─ test_select (test files)
  └─ [NEW] symbol_graph (pre-computed, consulted by planner)

AISH (wrapper layer, unchanged)
  ├─ map (calls repo_map)
  ├─ read (calls ai_read)
  └─ inspect (wraps agent_loop)
       └─ agent_loop consults symbol_graph if available
```

**Interactions**:
- `planner.next_step()` checks symbol_graph to find related files instead of random exploration
- `tool_runner` does NOT call symbol_graph; it's a read-only reference
- AISH tracks symbol_graph calls as a new tool (optional, for benchmarking)
- Agent behavior remains unchanged if symbol_graph unavailable

**Entry point for Phase 2**: 
- Add optional `--use-symbols` flag to `aish inspect`
- If enabled, build symbol graph before agent loop starts
- Measure: does agent find answer faster (fewer steps)?

---

## Benchmark Relevance

| Benchmark | What symbol_graph reveals | Test focus |
|-----------|--------------------------|-----------|
| **Trade** | Deep API → Service → Repository layering; can planner skip to service layer directly? | Architectural pattern recognition |
| **apaR** | Mixed backend (Python) + frontend (TypeScript); can symbol_graph handle single language only? | Language scope boundary |
| **cog** | Simulation domain model; complex state machines; can symbol_graph find state-related files? | Complex domain relationships |
| **LifeOS_2** | Multi-feature app (health, finance, habits); separate modules; can symbol_graph find feature boundaries? | Modular system identification |
| **myLife** | React + Flask hybrid; API calls; can symbol_graph find frontend-backend integration points? | Cross-layer data flow |

**Hypothesis**: Symbol_graph is valuable if ≥2 benchmarks show planner making fewer total tool calls with symbol_graph enabled.
