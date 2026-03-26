# Phase 2 Decision Gate: Baseline Measurements

**Established**: 2026-03-24 after Phase 1 AISH validation

## Control Group: Agent Step Counts (Without Symbol_Graph)

| Benchmark | ai_read calls | repo_map calls | Total exploration steps | Notes |
|-----------|--------------|----------------|----------------------|-------|
| Trade | 6 | 5 | 11 | Full-stack, layered API → Service → Data |
| apaR | 3 | 1 | 4 | Backend monolith with 9 local imports |
| myLife | 3 | 1 | 4 | Hybrid (Flask + React), mixed language |

**Baseline interpretation**:
- Trade requires more exploration (complex multi-layer architecture)
- apaR/myLife show similar patterns (deterministic entry point discovery)
- Baseline = control group for measuring symbol_graph impact

---

## Decision Gate Criteria

**Implement symbol_graph Phase 2 if ALL conditions met**:

1. **Performance**: Symbol graph AST parsing completes < 5 seconds on all 5 benchmarks
2. **Size**: Output JSON < 100KB for each benchmark repo
3. **Impact**: At least 1 benchmark shows agent exploration steps reduced by ≥30% with `--use-symbols` enabled
   - Trade: ≤ 7 steps (baseline 11)
   - apaR: ≤ 3 steps (baseline 4) 
   - myLife: ≤ 3 steps (baseline 4)

**Defer symbol_graph if ANY condition fails**:
- Parser takes > 10 seconds or times out
- Graph size > 200KB (indicates over-complexity)
- No benchmark shows meaningful step reduction
- Planner still explores randomly despite symbol_graph availability

---

## Next Validation Run

**Scope**: 5 benchmarks (Trade, apaR, cog, LifeOS_2, myLife)

**Procedure**:
1. Build symbol_graph v0 AST parser (isolated module, no integration)
2. Test parser on all 5 repos; record:
   - Parse time for each repo
   - Output JSON size for each repo
   - Any parse errors or edge cases
3. If parser passes criteria → proceed to planner integration
4. If parser fails criteria → log blocker and defer