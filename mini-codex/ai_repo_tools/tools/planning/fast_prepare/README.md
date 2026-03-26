# fast_prepare

Deterministic preflight/preparation planner built on fast_process.

## What it returns

- Primary orientation doc and follow-up references
- Preparation steps (read + run) for quick agent setup
- Confirmed deterministic checks for output integrity

## Usage

```bash
python ai_repo_tools/main.py fast_prepare
python ai_repo_tools/main.py fast_prepare 20000
```

The optional numeric argument is `max_files` forwarded to fast_process/fast_analyze.
