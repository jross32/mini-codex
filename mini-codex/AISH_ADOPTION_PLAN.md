# AISH v0 Adoption Plan

## What Uses AISH by Default

**Benchmark runs**: All structured codebase analysis
- apaR, Trade, myLife, and future benchmarks run via `aish inspect`
- Usage tracking automatically captured and aggregated

**Repo inspection**: Discovery and mapping
- Initial codebase exploration → `aish map` instead of direct tool calls
- File structure analysis → `aish map` before deep dives

**File reads**: Code analysis
- Individual file examination → `aish read <path>` instead of direct ai_read
- Captures file analysis in usage tracking

**Usage reporting**: Metrics and accounting
- `aish usage` becomes standard for tool adoption visibility
- Replaces ad-hoc log grepping

## Escape Hatch: Allowed Bypasses

**Direct agent invocation** permitted for:
- Internal agent debugging (testing agent_loop changes)
- Low-level tool validation (verifying repo_map behavior)
- Emergency diagnosis if AISH suspected broken

**Condition**: Bypass should be rare and documented when used
- If using `python -m agent.agent_loop` directly, note why
- Bypass counts as "outside adoption" in metrics

## Default Benchmark Workflow

For structured codebase analysis (the primary adoption goal):

```
aish inspect --goal <goal> --repo <path> --max-steps 10
aish usage                                               # verify bounded deltas
```

Rationale: `inspect` internally triggers repo_map and file analysis. No mandatory prerequisites.

## Manual Reconnaissance Tools (Optional)

Use only when you need targeted information before or outside a benchmark run:

```
aish map <repo>             # Quick "what's in this repo?" - get structure
aish read <file>            # Single-file examination - what does this do?
aish usage                  # Adoption check - review cumulative tool usage
```

These are **optional**, not mandatory before every inspect.

**When to use each**:
- **map**: Ad-hoc exploration, rapid repo orientation
- **read**: Deep dive on specific file, understand implementation
- **inspect**: Full analysis with goal, default for benchmarks
- **usage**: Adoption metrics, track tool consumption

## Healthy Adoption Signals

✓ **Good adoption = benchmark runs use AISH by default**:
- Every benchmark run goes through `aish inspect`, not direct `python -m agent.agent_loop`
- Each run records inspect +1 in aish_usage.json
- Tool deltas bounded (repo_map +1, ai_read 2-5, agent_loop +1, etc.) per run
- No manual tool sequence required—inspect handles discovery internally

✓ **Measured over 3+ consecutive benchmark runs**:
- 100% of benchmarks routed through AISH
- Usage tracking shows consistent, bounded deltas
- No log contamination or historical overflow
- Escape hatch (direct agent) used rarely/never

✗ **Warning signs (adoption problem)**:
- Benchmarks starting with `python -m agent.agent_loop` instead of `aish inspect`
- Inspect counts jumping by 10+ per run (log contamination)
- Direct agent calls becoming routine (adoption slipping)
- Tool sequence appearing mandatory before every inspect (defeats purpose)

## How to Verify Adoption

For each benchmark run:

1. **Before**: `aish usage` — note current inspect, repo_map, ai_read, agent_loop totals

2. **Execute**: `aish inspect --goal "analyze..." --repo "<path>" --max-steps 10`

3. **After**: `aish usage` — confirm deltas are small and bounded
   - inspect +1 ✓
   - repo_map ~1 ✓
   - ai_read ~2-5 ✓
   - agent_loop +1 ✓

**Adoption check**: Did the benchmark use AISH (not direct agent)?
- If `aish inspect` was used → **adoption working**
- If `python -m agent.agent_loop` was used → **adoption slipping**

**Over 3+ runs**: All benchmarks should route through AISH, not bypass to direct agent.

## What Not to Do Yet

- ❌ Add new AISH commands (map, read, inspect, usage are complete)
- ❌ Add shell/REPL features (stays command-only)
- ❌ Auto-evolve AISH based on usage patterns (frozen baseline)
- ❌ Integrate symbol_graph or Phase 2 features
- ❌ Modify underlying agent behavior (AISH wrapper only)

## Adoption Checkpoint

**Phase 1 complete when all benchmark runs are AISH-first**:
- Next 3 benchmarks routed through `aish inspect`, not direct agent
- Usage tracking shows consistent, bounded deltas per run
- No log contamination
- Escape hatch (direct agent) not used

Then: unlock Phase 2 (symbol_graph integration).

## Reference

- AISH implementation: `mini-codex/aish/`
- Baseline proof: `AISH_BASELINE.md`
- Usage log: `agent_logs/aish_usage.json`
- Trade benchmark validation: approved, benchmark-equivalent behavior confirmed
