# fast_process

Deterministic processing planner built on top of fast_analyze.

## What it returns

- Primary orientation doc to read first
- Recommended follow-up files from explicit orientation references
- Next actions list for fast, repeatable agent handoff
- Dominant extension and summary context

## Usage

```bash
python ai_repo_tools/main.py fast_process
python ai_repo_tools/main.py fast_process 20000
```

The optional numeric argument is `max_files` forwarded to fast_analyze.
