# Benchmark Runner & Regression Check Specification

## Purpose

Define measurable, repeatable test cases for agent behavior validation across iterations.

Each benchmark case documents expected behavior so that code changes can be validated against baseline without manual inspection.

---

## Benchmark Case: LifeOS_2 (Monolith)

**Type:** Monolithic single-file architecture

**Command:**
```
python -m agent.agent_loop --goal "analyze the codebase structure and relationships" \
  --repo "c:\Users\justi\Desktop\Coding Projects\project_dump\LifeOS_2\LifeOS_2" \
  --max-steps 10
```

### Expected Behavior

| Metric | Expected | Notes |
|--------|----------|-------|
| **Exit code** | 0 | No crashes |
| **Step count** | 3 | repo_map, ai_read, test_select |
| **Files read** | 1 | app.py only (10,871 lines) |
| **Follow-ups** | 0 | No second ai_read |
| **Status** | "complete" | Agent reaches natural end |
| **Tool sequence** | repo_map → ai_read → test_select | Exact order, no deviations |

### What Counts as a Failure

❌ Step count ≠ 3
❌ Files read > 1 (means fabricating follow-ups)
❌ Exit code ≠ 0
❌ Tool sequence !== [repo_map, ai_read, test_select]
❌ Reads files from .venv, node_modules, site-packages
❌ Status ≠ "complete"

### Success Criteria (Pass/Fail)

✅ **Pass** if all metrics match expected
✅ **Pass** if synthesis mentions 200+ functions or major classes
✅ **Pass** if no false dependencies invented

---

## Benchmark Case: cog (Modular)

**Type:** Modular multi-file with local imports

**Command:**
```
python -m agent.agent_loop --goal "analyze the codebase structure and relationships" \
  --repo "c:\Users\justi\Desktop\Coding Projects\project_dump\cog\cog" \
  --max-steps 10
```

### Expected Behavior

| Metric | Expected | Notes |
|--------|----------|-------|
| **Exit code** | 0 | No crashes |
| **Step count** | 4 | repo_map, ai_read (app.py), ai_read (follow-up), test_select |
| **Files read** | 2 | app.py (382 lines), then one of: core_ai.py, simulation.py, database.py |
| **Follow-ups** | 1 | Exactly one follow-up read |
| **Status** | "complete" | Agent reaches natural end |
| **Tool sequence** | repo_map → ai_read → ai_read → test_select | Two ai_read calls |
| **First file** | app.py | Entry point |
| **Second file** | core_ai.py | (Highest probability; see note below) |

### Note on Second File

Current agent selects based on set iteration order (non-deterministic).

**Acceptable second reads:** core_ai.py, simulation.py, database.py, or tools/safety.py
(Any local import match is acceptable until import ranking policy is formalized)

**Not acceptable:** stdlib/third-party files, files outside project root

### What Counts as a Failure

❌ Step count < 4 (means no follow-up)
❌ Step count > 5 (means over-reading)
❌ Files read ≠ 2
❌ Exit code ≠ 0
❌ First file ≠ app.py
❌ Second file is from .venv, site-packages, or non-project
❌ Tool sequence !== [repo_map, ai_read, ai_read, test_select]
❌ Status ≠ "complete"

### Success Criteria (Pass/Fail)

✅ **Pass** if all metrics match expected (with note on second file flexibility)
✅ **Pass** if app.py imports are correctly extracted
✅ **Pass** if second read is a real local import match
✅ **Pass** if synthesis recognizes multi-file structure

---

## Regression Check Routine

Run both benchmarks after any code change:

```bash
# LifeOS_2 case
python -m agent.agent_loop --goal "analyze the codebase structure and relationships" \
  --repo "c:\Users\justi\Desktop\Coding Projects\project_dump\LifeOS_2\LifeOS_2" \
  --max-steps 10

# cog case
python -m agent.agent_loop --goal "analyze the codebase structure and relationships" \
  --repo "c:\Users\justi\Desktop\Coding Projects\project_dump\cog\cog" \
  --max-steps 10
```

### Quick Pass/Fail Check

Extract from trace:
- ✅ LifeOS_2: 3 steps, 1 file read, status=complete
- ✅ cog: 4 steps, 2 files read, status=complete

If either fails, revert change and investigate.

---

## Known Instabilities (Track These)

### 1. Import Selection Order (set iteration)

**Status:** ⚠️ Known issue
**Impact:** cog case may select different follow-up file across runs
**Fix:** Requires deterministic ranking policy (not yet implemented)
**Workaround:** Accept any valid local import as second file

### 2. File Ordering in known_files

**Status:** ⚠️ Minor
**Impact:** First file selection may vary if multiple .py files at root
**Fix:** Requires stable sort in parse_repo_map_result
**Workaround:** LifeOS_2 and cog each have clear single entry point

---

## Future Benchmark Additions

When adding new benchmark cases (Frontend-Heavy, Mixed/Noisy, etc.):

1. Define expected step count and file list
2. Document what imports should be extracted (if any)
3. List acceptable follow-up files
4. Define failure modes
5. Add to regression check routine
