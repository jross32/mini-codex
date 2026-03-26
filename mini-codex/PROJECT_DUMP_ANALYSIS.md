# Project Dump Classification & Benchmark Planning

## Survey Overview

Total projects in `project_dump`: **11 directories**

Current benchmark coverage:
- ✅ LifeOS_2 (monolith single-file)
- ✅ cog (modular 2-file chain)

---

## All Projects Classified

### 1. **apaR** — Full-stack Flask → TypeScript/React application
**Size:** Medium (~150 files total)  
**Python Files:** ~13 modules in backend  
**Structure:** 
```
backend/app/
  main.py (entrypoint via factory pattern)
  __init__.py (create_app factory)
  config.py, db.py, data_store.py
  admin.py, auth.py, models.py, routes.py, cli.py
  user_context_routes.py, seed.py, snapshots.py, stats.py

frontend/
  src/ (TypeScript/React with components, routes, context)
```

**Type:** Modular mixed backend+frontend  
**Entry Point:** `backend/app/__init__.py::create_app()` factory pattern  
**Key Pattern:** Many modules with central imports (9 modules imported in __init__.py)  
**What It Tests:**
- ✅ Central __init__ with multiple module imports
- ✅ Mixed technology stack detection (Flask + React)
- ✅ Multi-level modular structure
- ❌ Does it skip frontend properly?
- ❌ Which module does it try to read second? (admin, auth, routes, etc.)

**Good For Testing:** Import selection when 9 options exist

---

### 2. **LifeOS** — Monolithic Flask application (older variant)
**Size:** Large (~9K LOC single file)  
**Python Files:** 1 main file + templates/static  
**Structure:**
```
LifeOS/
  app.py (9000+ lines)
  data/
  static/ (CSS)
  templates/ (11+ HTML files)
```

**Type:** Monolith (single-file architecture)  
**Entry Point:** `app.py`  
**Key Pattern:** Same domain as LifeOS_2 but older iteration  
**Duplicate Status:** ⚠️ **Very similar to LifeOS_2** (different feature set, similar structure)  
**Good For Testing:** Redundant—already covered by LifeOS_2

---

### 3. **WhatAPC** — Minimal Flask monolith
**Size:** Small (~1.5K LOC)  
**Python Files:** 1 file (app.py with embedded models)  
**Structure:**
```
WhatAPC/
  app.py (monolith with Flask + SQLAlchemy models inline)
  requirements.txt
  whatapc.db
```

**Type:** Monolith (single-file) but tiny  
**Entry Point:** `app.py`  
**Key Pattern:** Inline database models in single file  
**Good For Testing:** ❌ Not useful—too small, already covered by LifeOS_2, no interesting patterns

---

### 4. **WhatAPC_2** — Modern Vite React frontend with single-file backend
**Size:** Large (~50+ files frontend, 1 Python file)  
**Python Files:** 1 file  
**Structure:**
```
WhatAPC_2/
  frontend/
    src/ (React + Vite, tailwind config, TypeScript)
    node_modules/, dist/, public/
  backend/
    app.py (monolith)
```

**Type:** Frontend-heavy + monolith backend  
**Entry Point:** `backend/app.py`  
**Key Pattern:** Modern frontend stack with venv/.gitignore filtering needed  
**What It Tests:**
- ✅ Proper node_modules/ filtering
- ✅ Modern build artifacts (dist/, node_modules/) handling
- ✅ Vite/TypeScript structure recognition
- ❌ Does it skip frontend entirely?
- ❌ Does venv filtering work?

**Good For Testing:** Frontend filtering + node_modules handling

---

### 5. **Trade** — Crypto trading bot with modular backend
**Size:** Large (~25+ Python files, structured backend)  
**Python Files:** ~25 modules  
**Structure:**
```
Trade/
  START_HERE.py (welcome guide)
  backend/
    main.py (imports from local submodules)
      → config.py, logger.py, data, strategy, trading, backtest
    config.py
    logger.py
    database.py
    models/
      __init__.py, user.py, model.py
    strategy/
      __init__.py, strategy.py
    trading/
      __init__.py, bot.py, paper_trading.py
    api/, broker/, backtest/, schemas/
    requirements.txt
  crypto_bot/ (optional ML models)
  frontend/
```

**Type:** Large modular backend + optional frontend  
**Entry Point:** `backend/main.py` (script style, imports subpackages)  
**Key Pattern:** 
- Deep package hierarchy (models/, strategy/, trading/)
- Script calling subpackage functions
- 6+ imports from first read: config, logger, data, strategy, trading, backtest

**What It Tests:**
- ✅ Multi-level import chains (should select one of 6)
- ✅ Package structure with __init__.py pattern
- ✅ Deterministic selection with many imports
- ✅ Preference for core vs utility modules
- ❌ Does agent read database.py or strategy.py second? (What's more important?)
- ❌ Can it handle nested modules correctly?

**Good For Testing:** Large modular project with many imports + multi-level chains

---

### 6. **drl** — Deep Reinforcement Learning package
**Size:** Medium (~12 Python files in core package)  
**Python Files:** Structured package  
**Structure:**
```
drl/
  example_train.py (entry script)
  ultimate_drl/
    __init__.py
    config.py
    agents/
      ensemble_agent.py
    envs/
      trading_env.py
    models/
      policies.py
    training/
      walkforward.py, reward_functions.py, augmentations.py
    utils/
      metrics.py, data_utils.py
  scripts/
  requirements.txt
```

**Type:** Modular package with nested structure  
**Entry Point:** `example_train.py` (imports from drl_agent_core — external package?)  
**Key Pattern:** Imports external `drl_agent_core` package, not local modules  
**What It Tests:**
- ⚠️ Only imports external packages from example_train.py?
- ❌ If local, would test nested package imports

**Duplicate Note:** Very similar domain to Trade (both trading/ML) but different architecture

---

### 7. **nf** — Large meta-analysis utility project
**Size:** VERY LARGE (~200+ Python files)  
**Python Files:** Extensive tools + versions  
**Structure:**
```
nf/
  AI_START_HERE.md (official guide)
  ai_repo_tools/ (toolkit for repo analysis)
    data_flow/ (10+ versions of data flow analysis tools)
  api_sniffer/ (API discovery)
  apa_url_discovery/ (URL discovery)
  repo_runs/ (output caches)
  results/ (analysis results)
  docs/
```

**Type:** Large utility/research toolkit  
**Entry Point:** Multiple tools (repo_map, ai_read, symbol_graph, etc.)  
**Key Pattern:** 
- Self-referential: Uses `ai_repo_tools` internally
- Many deprecated versions (dataflowV0.3, V0.4, … V0.9)
- Experimental/evolved codebase

**What It Tests:**
- ✅ Massive project (200+ files—scalability test)
- ✅ Deprecated file handling (ignore V0.3-V0.8?)
- ✅ Multiple entry points
- ❌ Will agent get confused by many versions?
- ❌ Can it identify "latest" version?

**Good For Testing:** Very large projects + deprecated code navigation

---

### 8. **spammer** — API discovery & testing tool
**Size:** Small (~7 Python files)  
**Python Files:** Test suite + API sniffer  
**Structure:**
```
spammer/
  apa_api_sniffer_v2.py (async API discovery)
  apa_url_discovery.py
  tests/
    test_sniffer.py, test_modes.py
    run_all_tests.py
  apa_api_captures/ (output data)
  test_sniffer.py, test_functional.py (root-level duplicates?)
```

**Type:** Small utility/test project  
**Entry Point:** `apa_api_sniffer_v2.py` (Playwright-based async tool)  
**Key Pattern:** 
- Tests directory with separate test files
- Root-level test files (duplication?)
- Async/playwright testing

**What It Tests:**
- ❌ Too small—only 7 files, not much import complexity
- ✅ Test directory structure
- ✅ Async import detection (playwright, asyncio)

**Good For Testing:** Small project (not particularly useful for import-following)

---

## Coverage Matrix

| Project | Size | Type | Already Tested? | New Test Value? |
|---------|------|------|-----------------|-----------------|
| **LifeOS_2** | Large | Monolith 1-file | ✅ YES | — |
| **cog** | Small | Modular 2-file | ✅ YES | — |
| **LifeOS** | Large | Monolith 1-file | ❌ NO | ⚠️ Duplicate of LifeOS_2 |
| **WhatAPC** | Small | Monolith 1-file | ❌ NO | ❌ Too small, redundant |
| **WhatAPC_2** | Med | Monolith + Frontend | ❌ NO | ✅ Tests frontend filtering |
| **apaR** | Medium | Modular 9-module | ❌ NO | ✅ **HIGH VALUE** — Many imports |
| **Trade** | Large | Modular 20+ files | ❌ NO | ✅ **HIGH VALUE** — Deep structure + many imports |
| **drl** | Small | Nested package | ❌ NO | ⚠️ Depends on if local imports exist |
| **nf** | HUGE | Utility toolkit | ❌ NO | ✅ Scalability test, complex |
| **spammer** | Small | Util + tests | ❌ NO | ❌ Too small |

---

## Identified Missing Benchmark Categories

### ✅ Already Covered
1. **Large single-file monolith** ← LifeOS_2
2. **Deterministic multi-file selection** ← cog

### ❌ NOT Yet Covered
1. **Many-to-one import pattern** (9+ modules importing from shared __init__) ← **apaR fills this**
2. **Large modular project with 20+ files + multi-level packages** ← **Trade fills this**
3. **Frontend filtering (node_modules, dist/, .venv handling)** ← WhatAPC_2 or apaR
4. **Nested package structure depth** (agents/strategy/models/) ← Trade
5. **Import priority with 5+ choices** (should agent prefer core_ai over simulation?) ← Trade (6 choices: config, logger, data, strategy, trading, backtest)
6. **Very large utility project** (200+ files) ← nf

---

## Recommended New Benchmark Cases

### **TOP PRIORITY**: 2 cases to add next

#### **BENCHMARK 3: apaR — Flask Full-Stack with Many Central Imports**

**Why this one first:**
- Tests import selection with 9 available modules (not just 2)
- Central patterns: admin, auth, routes most important? Or order matters?
- Same benchmark suite repeatable: "which do you select after app/__init__.py?"
- Isolate backend (ignore frontend) properly

**Expected Pattern:**
```
repo_map → ai_read (backend/app/__init__.py)
  → select_related_file() → [admin, auth, config, data_store, db, models, routes, user_context_routes, cli]
  → agent must select ONE (deterministic)
  → ai_read (second module)
```

**Good For Testing:**
- ✅ Many-to-one import selection (freq-based would select: routes? config? or alphabetical fallback?)
- ✅ Frontend/backend separation (does it correctly identify backend as primary?)
- ✅ Database + auth patterns (common in web apps)
- ✅ Mixed import styles (relative + package imports)

**Edge Case to Watch:**
- Does agent prefer `routes` (most likely critical) over `config`?
- Or does frequency win and favor what's imported most?

---

#### **BENCHMARK 4: Trade — Large Modular Crypto Bot with Deep Structure**

**Why this one second:**
- Largest Python codebase after nf
- Tests real multi-level import chains: strategy/ → bot.py → broker/
- Real-world domain (crypto trading = complex state machine)
- 6 imports from main.py (vs 4 in cog)

**Expected Pattern:**
```
repo_map → ai_read (backend/main.py)
  → identifies imports: [config, logger, data, strategy, trading, backtest]
  → select_related_file() → [config.py, logger.py, database.py, ...]
  → agent must select ONE
  → ai_read (second module)
    → that module may import OTHER locals (recursive chains)
```

**Good For Testing:**
- ✅ Import priority when many exist (config/logger are setup, strategy/trading are domain)
- ✅ Multi-level import chains (strategy.py → bot.py → paper_trading.py)
- ✅ Package structure with __init__.py patterns
- ✅ Real dependency graph (respects actual importance)
- ✅ Agents/models/strategy/trading domain separation

**Distinguishes from apaR:**
- apaR: many imports from ONE file (__init__.py)
- Trade: imports from SCRIPT calling subpackages → deeper chains

---

## NOT Recommended (yet)

| Project | Reason |
|---------|--------|
| **LifeOS** | Duplicate of LifeOS_2—same structure, same size, same limitations |
| **WhatAPC** | Too small (1.5K LOC), no import complexity, monolith already tested |
| **spammer** | Too small (7 files), no interesting import patterns |
| **drl** | Unclear if local imports exist; likely imports external `drl_agent_core` |
| **nf** | Save for later—200+ files is for scalability stress test, not baseline |
| **WhatAPC_2** | Could do later for "frontend filtering" but apaR already tests this |

---

## Summary & Next Steps

### ✅ Current Baseline (Solid Checkpoint)
- ✅ Monolith handling (10K+ lines) → LifeOS_2
- ✅ Deterministic frequency-based import selection → cog
- ✅ Proper filtering (.venv, node_modules) → both
- ✅ Honest uncertainty (no false follow-ups) → both

### 🎯 Recommended Next Benchmarks
1. **apaR** — Tests "which module when 9 exist"
2. **Trade** — Tests "multi-level chains + 6 imports + domain separation"

### 📊 Metrics to Track
For each benchmark, measure:
- ✅ Step count (repo_map → ai_read → select → ai_read N)
- ✅ File selection determinism (always picks same file)
- ✅ Whether frequency beats alphabetical ordering
- ✅ Synthesis quality (does it understand each module's role?)

---
