# AISH Production Improvement Analysis

**Date:** 2026-03-26  
**Focus:** Gaps that catch real production problems in tool evolution  
**Thoroughness:** Medium (7 key improvement areas)

---

## Executive Summary

AISH v1 has a solid pilot promotion pipeline for `trust_trend`, but lacks production-grade visibility, configuration, recovery, and extension hooks. The following gaps would likely surface problems in production evolution:

1. **No runtime degradation detection** — promotions can't be reverted; failures require manual intervention
2. **Hard-coded gate thresholds** — no tuning per tool or adaptive gates  
3. **Shallow candidate metrics** — only perf + correctness; misses behavioral/integration changes
4. **No deprecation lifecycle** — tools live or are archived, no sunsetting
5. **Limited audit/decision trails** — promotion report exists but reasoning buried in gate logic
6. **No integration hooks** — can't add custom gates without modifying core
7. **No comparative history** — each promotion isolated; no trends across candidates

---

## Analysis by Area

### 1. Promotion Pipeline Gates & Rejection Handling

**Current Implementation** ([promotion_pipeline.py](aish/promotion_pipeline.py#L201-L280)):
- **Gates:**
  - Correctness: success_rate must be 1.0 (all 3 runs succeed)
  - Performance: slowdown_pct ≤ max_slowdown_pct (default 5%)
  - Regression: required payload keys match baseline
  - Safety: no blocked patterns (os.remove, shutil.rmtree, etc.)
- **Rejection:** Returns exit code 1, marks decision=reject, stores JSON report
- **No rollback:** Bad promotion is promoted anyway if accidentally triggered; stable_command and live_command both updated without reverting

**Gaps That Matter in Production:**

| Gap | Problem | Example |
|-----|---------|---------|
| **No veto gate** | Promotion succeeds even if wrong | Correctness always passes if 3/3 runs are lucky; no stochastic failure detection |
| **Static binary gates** | No gray zones or soft fails | Performance gate at 5% is arbitrary; no gradual degradation tracking |
| **No environmental gates** | Ignores deployment context | Tool might be slow on large repos but gate runs small test; no parameterized testing |
| **Rejection is silent** | Failure not actionable | Exit code 1 is success for shell; orchestrator can't distinguish rejection from error |
| **No rollback** | Can't undo bad promotions | If candidate causes crashes at scale after promotion, stable_command is already overwritten |

**Practical Improvements:**

1. **Add explicit rollback mechanism**
   - Keep N previous stable versions (e.g., last 5)
   - Expose `promote-tool --rollback` command
   - Record rollback reason in audit log

2. **Distinguish rejection from errors**
   - New exit code: 2 for rejection (gate failed), 1 for errors
   - Promotion report includes `gate_failures` list with reasons
   - Orchestrator can route differently based on exit code

3. **Add "canary" gate** (optional second stage)
   - Run candidate on live samples (e.g., agent_logs) before full promotion
   - Detect integration issues that microbenchmark misses
   - Gate: sample success rate ≥ 90% (softer than 100%)

4. **Add ambient context to gates**
   - Record: repo size, Python version, available memory
   - When promoting future tools, check if context matches

---

### 2. Error Recovery & Rollback Capabilities

**Current State:**
- No recovery: only `ensure_lifecycle` initializes versions; promotion is one-shot
- No revert: `run_promotion` writes to `stable_command` and `live_command` without keeping old versions
- No abort: once promotion starts running, can't cancel mid-test

**Production Scenarios That Fail:**

| Scenario | Current Behavior | Needed |
|----------|------------------|--------|
| Promotion partially succeeds (e.g., baseline runs fail) | Continues to comparison; may promote bad baseline | Allow abort if baseline success_rate < threshold |
| Post-promotion, live tool crashes in agent loop | Stable command is already replaced; must manually restore | Auto-detect failures and revert within N seconds |
| User realizes mistake after promotion | No undo; must manually restore from git | `promote-tool --rollback --to <previous_candidate_id>` |
| Network failure during test run | Incomplete results treated as valid or error depends on where it fails | Checkpointed runs; resume from last complete state |

**Practical Improvements:**

1. **Versioned stable snapshots**
   ```python
   # Instead of single "stable/command.py", create versions_root/stable/v1, v2, v3...
   # Keep last N (e.g., 5) with metadata (timestamp, candidate_id promoted from)
   stable_snapshots = versions_root / "stable_snapshots"
   stable_snapshots / "v20260326_023953" / "command.py"  # current
   stable_snapshots / "v20260325_180000" / "command.py"  # previous
   ```

2. **Rollback command**
   ```
   aish promote-tool trust_trend --repo <path> --rollback --to-snapshot v20260325_180000
   ```
   - Writes JSON audit entry: {action: rollback, from: v123, to: v20260325_180000, reason: "..."}

3. **Automatic revert on detection failure**
   - If candidate is active and agent_logs shows N consecutive tool errors, temporarily revert to stable
   - Log: {event: auto_revert, candidate: vXYZ, error_count: N, reverted_at: timestamp}
   - Manual confirmation required to re-promote

4. **Checkpoint-based promotion runs**
   - Save run results after each successful run (not just at end)
   - If promotion interrupted, resume from checkpoint (skip already-completed baseline runs)

---

### 3. Configuration & Tuning of Gate Thresholds

**Current State:**
```python
# In promotion_pipeline.py:
max_slowdown_pct: float = 5.0  # hardcoded; no config
REQUIRED_PAYLOAD_KEYS = {"success", "tool", "overall", "workers", "summary"}  # fixed list
# Correctness gate: candidate.get("success_rate", 0.0) >= 1.0  # always 1.0
```

**Problems:**

- **No per-tool configuration**: All tools must pass 5% slowdown; fast tools could accept 10%, cache tools need 1%
- **No adaptive gates**: Can't tighten thresholds after first promotion or based on observed failures
- **No env-scoped gates**: Gate should differ: "trust_trend on large Trade repo" vs "on small test_repo"
- **No decay gates**: Older candidates (2+ months) might need stricter re-certification before re-promotion

**Practical Improvements:**

1. **Gate configuration file** (`agent_logs/promotion_gates.json`)
   ```json
   {
     "default": {
       "correctness_floor": 1.0,
       "max_slowdown_pct": 5.0,
       "min_runs": 3,
       "required_keys": ["success", "tool", "overall", "workers", "summary"]
     },
     "trust_trend": {
       "max_slowdown_pct": 10.0,
       "correctness_floor": 0.95,
       "min_runs": 5,
       "environmental": {
         "large_repo": {"max_slowdown_pct": 15.0},
         "small_repo": {"max_slowdown_pct": 5.0}
       }
     }
   }
   ```

2. **Tier-based release gates**
   - Tier 0 (strict): correctness 1.0, slowdown < 2%, 5 runs, safety + custom gates
   - Tier 1 (normal): correctness 0.98, slowdown < 5%, 3 runs, safety + custom gates
   - Tier 2 (beta): correctness 0.95, slowdown < 10%, 2 runs, safety gate only
   - `promote-tool --tier 0` uses appropriate thresholds

3. **Dynamic threshold adjustment**
   - Track: "What slowdown % have we observed in live deployments?"
   - Every N promotions, analyze if gate too loose/strict
   - Recommend: `aish analyze-gate-drift --tool trust_trend`
   - Output: "Current gate allows 5% slowdown but live avg 2%; consider tightening to 3%"

---

### 4. Candidate Comparison & Reporting Depth

**Current State** ([promotion_pipeline.py](aish/promotion_pipeline.py#L228-L250)):
```python
# Comparison is limited to:
# - success_rate (binary: 1.0 or not)
# - mean_ms (single aggregate)
# - blocked_patterns (safety)
# - required_keys (regression)
# 
# Report structure is flat; no breakdown by error type, performance percentiles, payload diffs
```

**What's Missing:**

| Missing Metric | Why It Matters | Example |
|---|---|---|
| **Error breakdown** | Know *why* failures occur, not just count | "2 failures: both in json parsing, never in core logic" → safe corner case |
| **Performance distribution** | Mean can hide performance cliffs | Baseline: [100ms, 110ms, 115ms]; Candidate: [80ms, 150ms, 160ms] → high variance issue |
| **Payload field diffs** | Spot behavioral changes, not just key presence | Baseline always returns "workers": [w1, w2]; Candidate: [w1] (missing w2 in some runs) |
| **Side effect audit** | Detect mutations, file I/O, network calls | Scanning for `subprocess.run` is good; tracking *what calls succeed* is better |
| **Historical regression** | Compare to *all* prior candidates, not just stable | Candidate v3 vs stable is good; v3 vs v1, v2 (to spot trend) is better |
| **Timeout/resource** | Detect unbounded loops or memory leaks | Candidate consistently hits 120s timeout (vs 30s baseline) |

**Practical Improvements:**

1. **Richer execution report**
   ```json
   {
     "schema_version": "promotion.v2",
     "execution": {
       "baseline": {
         "runs": 3,
         "success_rate": 1.0,
         "successes": 3,
         "errors": [],
         "performance": {
           "runs_ms": [450, 460, 456],
           "mean_ms": 455.3,
           "p50_ms": 456,
           "p95_ms": 460,
           "p99_ms": 460,
           "max_ms": 460,
           "coefficient_of_variation": 0.011
         },
         "payload_stability": {
           "all_identical": true,
           "sample_payload": {...}
         }
       },
       "candidate": {...similar structure...},
       "comparison": {
         "performance_regression": {
           "slowdown_pct": -3.57,
           "variance_change": 0.8,
           "breakdown": "improved mean and stability"
         },
         "behavioral_changes": [
           {
             "field": "workers",
             "baseline_values": [["w1", "w2"], ["w1", "w2"], ["w1", "w2"]],
             "candidate_values": [["w1", "w2"], ["w1"], ["w1", "w2"]],
             "changed_runs": [1],
             "severity": "medium"
           }
         ]
       }
     }
   }
   ```

2. **Payload diff report**
   - For each run, show which fields differ from baseline and by how much
   - Flag non-determinism (same input, different output)
   - Gate: "No payload field should differ by >X% of runs"

3. **Performance profile chart** (text-based for logs)
   ```
   Baseline:      [===|===|===] mean=456ms
   Candidate:     [==|=====|==] mean=440ms (wide variance!)
   Regression:    PASS (slower but within threshold)
   Regression:    WARN (higher variance than baseline)
   ```

4. **Historical comparison matrix**
   ```
   Tool: trust_trend
   Latest 5 candidates vs stable:
   - v20260326: mean 440ms (✓ +3.5% variance but faster)
   - v20260325: mean 445ms (✓ +0.8% variance)
   - v20260324: mean 480ms (✗ -5.3% slowdown, rejected)
   - v20260323: mean 460ms (✓ +1.2% variance)
   - v20260322: [archived stable; mean 456ms]
   
   Trend: Performance stable, variance slightly increasing
   ```

---

### 5. Tool Deprecation & Sunset Workflows

**Current State:**
- No deprecation concept; tools exist in: live (active), stable (candidate baseline), archived (rejected candidates)
- No "deprecated but still callable" state
- Archived candidates can't be inspected post-mortem

**Scenarios AISH doesn't handle:**

| Scenario | Current | Needed |
|----------|---------|--------|
| Tool is "good enough" but maintainer wants to signal "don't build on top of this" | No way to communicate intent | Deprecation state; show warning on calls |
| Early candidate was buggy; useful to see *why* archived, not just the report | Report saved but not easily findable or annotated | Archive with deprecation reason; searchable metadata |
| Tool is being replaced by new version (e.g., trust_trend → trust_trend_v2) | No lineage; both coexist, confusion reigns | Explicit "successor" linkage; orchestrator routes to v2 |
| Tool performs worse over time due to env drift (new Python, libs) | Promotion was fine 2 months ago; silently degraded | Auto-recertification workflow; alert if confidence drops |

**Practical Improvements:**

1. **Deprecation state & metadata**
   ```json
   // In versions_root/deprecated/
   "trust_trend": {
     "deprecated_at": "2026-04-01T10:00:00Z",
     "reason": "Replaced by trust_trend_v2 (better uncertainty handling)",
     "successor": "trust_trend_v2",
     "expected_removal_date": "2026-05-01",
     "replacement_instructions": "Update calls from trust_trend to trust_trend_v2; API identical"
   }
   ```

2. **Deprecation command**
   ```
   aish deprecate-tool trust_trend --reason "..." --successor trust_trend_v2 --removal-date 2026-05-01
   ```
   - Marks live/stable/archived as deprecated but still callable
   - Logs deprecation event to audit trail
   - `aish list-versions` shows deprecation status

3. **Graceful replacement workflow**
   ```
   aish promote-tool trust_trend_v2 --repo <path>  # new tool promoted
   aish soft-replace trust_trend --with trust_trend_v2  # existing calls remain working but logged
   # Over time, migrate users to v2
   aish hard-replace trust_trend --with trust_trend_v2  # now fails with migration error
   ```

4. **Auto-recertification gate**
   ```
   aish recertify-tool trust_trend --repo <path>  # re-run full promotion gates
   ```
   - Runs current trust_trend (stable) against current environment
   - If gates fail, marks as "confidence=low" and alerts
   - Can tie into orchestrator to avoid auto-spawning workers if tool_confidence < threshold

---

### 6. Integration Points & Extension Hooks

**Current State:**
- `run_promotion()` is monolithic; gates are hard-coded in `_standard_compare_schema()`
- No way to add custom gates (e.g., "passes tests in Trade repo", "doesn't slow down orchestrator")
- No hooks for pre/post promotion events
- No plugin architecture for new comparison strategies

**Problems:**

```python
# To add a custom gate, you must:
# 1. Modify _standard_compare_schema() directly
# 2. Edit promotion_pipeline.py and re-deploy
# 3. Risk breaking other tools
```

**Practical Improvements:**

1. **Gate plugin system**
   ```python
   # In promotion_gates/ (new directory)
   class PromotionGate(ABC):
       def evaluate(self, baseline: Dict, candidate: Dict) -> GateResult:
           pass
   
   # Tools can register custom gates
   # promotion_gates/trust_trend_custom.py
   class TestIntegrationGate(PromotionGate):
       def evaluate(self, baseline, candidate):
           # Run custom tests; check if candidate passes
           result = run_trade_integration_test()
           return GateResult(pass=result.success, reason=result.message)
   
   # In orchestrate or promote command:
   gates = load_gates("trust_trend")  # finds standard + custom gates
   results = [g.evaluate(baseline, candidate) for g in gates]
   ```

2. **Promotion lifecycle hooks**
   ```python
   # Before promotion runs
   on_promotion_start(tool_name, candidate_id)
   
   # After promotion decides
   on_promotion_decision(tool_name, candidate_id, decision, report)
   
   # After promotion applies (candidate → stable → live)
   on_promotion_applied(tool_name, candidate_id)
   ```
   - Hooks can write logs, publish metrics, send alerts
   - Allows external systems to react (e.g., CI/CD, monitoring dashboards)

3. **Report enrichment API**
   ```python
   # In report JSON, allow plugins to add data
   report = run_promotion(...)
   report = enrich_report(report, enrichers=[...])
   # Enrichers can add: test results, code coverage, security scan results, etc.
   ```

4. **Custom comparison strategies**
   ```
   aish promote-tool trust_trend --repo <path> --comparison-strategy "percentile_sensitive"
   ```
   - Standard strategy: mean-based (current)
   - Percentile-sensitive: gates based on p95 (avoid tail latency regression)
   - Variance-aware: penalizes high variance even if mean is good
   - Custom: user-defined comparison logic

---

### 7. Missing Metrics & Audit Trails

**Current State:**
- Usage tracking: basic append-only log in `aish_usage.json` (timestamp, command, tool, success, duration)
- Promotion report: single JSON file per promotion (no cross-tool index)
- No trend analysis: can't ask "How many promotions succeeded/failed over last month?"
- No audit of decision reasoning: report shows gates passed/failed but not why each gate was chosen

**Missing Context:**

| Missing | Current | Needed |
|---------|---------|--------|
| **Decision audit** | Report shows gate decisions but not parameters | Record: which gate config was used? Why that config? Who triggered promotion? |
| **Failure analysis** | Rejections are logged but not aggregated | "Last 5 rejections: 3 for performance, 2 for safety" → actionable pattern |
| **Promotion velocity** | Time to promotion unknown | From candidate creation to promotion decision: hours? days? |
| **Candidate lifecycle** | Candidates just sit until promoted or archived | How old is current candidate? How often do we create new candidates? |
| **Tool-level metrics** | Per-tool stats don't exist | trust_trend has X promotions, Y rejections; what's the trend? |
| **Environmental factors** | Context-free gates | Was slowdown gate applied on small repo or large? Does it matter? |

**Practical Improvements:**

1. **Promotion audit log** (structured)
   ```json
   // In agent_logs/promotion_audit.jsonl
   {
     "timestamp": "2026-03-26T02:39:53Z",
     "event": "promotion_started",
     "tool": "trust_trend",
     "candidate_id": "v20260326_023946_candidate",
     "triggered_by": "orchestrator_workflow",
     "gates_to_run": ["correctness", "performance", "regression", "safety", "custom_integration"]
   }
   {
     "timestamp": "2026-03-26T02:40:12Z",
     "event": "gate_evaluated",
     "gate": "performance",
     "config": {"max_slowdown_pct": 5.0, "env": "default"},
     "result": {"pass": true, "slowdown_pct": -3.57, "reason": "candidate faster than baseline"}
   }
   {
     "timestamp": "2026-03-26T02:40:30Z",
     "event": "promotion_decided",
     "decision": "promote",
     "all_gates_pass": true,
     "report_path": "agent_logs/promotion_trust_trend_20260326_023953.json"
   }
   ```

2. **Promotion dashboard data**
   ```json
   // In agent_logs/promotion_metrics.json (updated after each promotion)
   {
     "tools": {
       "trust_trend": {
         "total_candidates": 5,
         "promotions": {
           "succeeded": 2,
           "rejected": 3
         },
         "rejection_reasons": {
           "performance": 2,
           "regression": 1
         },
         "current_stable": "v20260326_023946_candidate",
         "time_to_promotion_avg_minutes": 45.2,
         "age_of_current_stable_days": 2
       }
     }
   }
   ```

3. **Promotion query command**
   ```
   aish show-promotions --tool trust_trend --window 30d
   # Output: decision (promote/reject), timestamp, slowdown%, reason, details
   
   aish show-rejections --tool trust_trend --reason performance
   # Output: why did these candidates get rejected? Trends observable?
   ```

4. **Decision reasoning export**
   ```
   aish analyze-promotion-decision --report path/to/promotion_*.json
   # Output: decision tree showing which gate thresholds mattered most
   # "Decision was driven primarily by performance gate; correctness always passed"
   ```

5. **Candidate lifecycle tracking**
   ```json
   // Optional: in versions_root/candidate/*/lifecycle.json
   {
     "candidate_id": "v20260326_023946_candidate",
     "created_at": "2026-03-26T01:00:00Z",
     "created_from": "stable_v20260325_180000",
     "promotion_attempts": 1,
     "first_promotion_at": "2026-03-26T02:39:53Z",
     "final_status": "promoted",
     "age_at_promotion_minutes": 99.7,
     "notes": "Generated by orchestrator_autonomous_worker_5"
   }
   ```

---

## Summary: Recommended Priority Order

### Tier 1 (High Impact, Medium Effort)
1. **Rollback mechanism** — Removes risk of bad promotions; enables faster iteration
2. **Exit code distinction** (rejection vs error) — Makes orchestrator/CI logic clearer
3. **Gate configuration file** — Unblocks per-tool tuning without code changes
4. **Richer promotion report** — Catches subtle behavioral regressions
5. **Promotion audit log** — Enables root cause analysis of failures

### Tier 2 (Medium Impact, Medium Effort)
6. **Canary gate** (live sample testing) — Detects integration failures early
7. **Deprecation support** — Enables tool migration without confusion
8. **Versionable stable snapshots** — Supports safer rollback; audit trail

### Tier 3 (Nice-to-Have, Higher Effort)
9. **Gate plugin system** — Enables org-specific gates (e.g., security, cost)
10. **Adaptive thresholds** — Auto-tighten gates based on observed production data
11. **Performance viz** (percentile charts) — Makes decisions more transparent
12. **Candidate lifecycle metadata** — Enables trend analysis

---

## Example: Applying Improvements to Production Scenario

**Scenario:** Promote a new version of `trust_trend`; it passes all gates but crashes in orchestrator after 10 minutes of load.

**Today:**
- Promotion applied; stable_command and live_command both updated
- Agent loop calls trust_trend; crashes; orchestrator logs error
- Manual intervention: git revert, rebuild, redeploy
- Time to recovery: 30+ minutes
- Root cause unknown (no audit trail of what changed)

**With Improvements:**
1. **Checkpoint + rollback**: Promotion created versioned snapshot; auto-detect crash pattern
   - `"consecutive_errors": 15, "threshold": 3 → auto_revert triggered`
   - Promotion rolled back in <1 minute
   
2. **Audit log**: Shows exactly which gate should have caught this
   - "Canary gate tested on 5 samples from agent_logs; all passed"
   - "But live orchestrator uses 124 workers; canary used 1 sample"
   - Gate thresholds adjusted: now canary_sample_count = 100
   
3. **Richer report**: Behavioral change was missed because basic regression gate only checked key presence
   - New report shows: "payload.workers field changed from [w1,w2,w3] to [w1] in run 2"
   - Catches non-determinism; marks candidate for deeper inspection
   
4. **Decision audit**: Decision log shows who promoted, when, and which config
   - `triggered_by: "admin_manual", gates_config: "trust_trend_strict"`
   - Next time, can audit if wrong config was used

5. **Metrics**: Post-mortems easier
   - "Last 3 promotions: 1 succeeded, 2 failed in production"
   - "All 3 used trust_trend_strict gate; rejection rate 67%"
   - Recommendation: relax gate thresholds; too many false failures

---

## Implementation Roadmap (Rough)

| Phase | Work | Effort | Value |
|-------|------|--------|-------|
| **v1.1** | Rollback snapshots, exit code distinction, audit log | 2 days | HIGH |
| **v1.2** | Gate config file, richer report, canary gate | 3 days | HIGH |
| **v1.3** | Deprecation support, promotion query commands | 2 days | MEDIUM |
| **v1.4** | Gate plugin system, lifecycle metadata | 3 days | MEDIUM-HIGH |
| **v2.0** | Multi-tool support (lift PILOT_TOOL restriction) | 5 days | CRITICAL |

---

## Notes

- **No over-engineering**: Each improvement addresses a specific production failure mode
- **Backward compatible**: All improvements can be additive (new gates, new fields, new commands)
- **Pilot-first mentality**: v1.1–v1.4 assume single-tool pilot; v2.0 is generalization breakpoint
- **Observable, not prescriptive**: Improvements focus on visibility + audit; policy (gate thresholds, rollback strategy) remains with operator

