# fast_analyze

Deterministic single-pass repository analysis optimized for speed.

## What it returns

- File count and scan duration
- Top file extensions and top directories
- Orientation docs (AI_START_HERE.md, START_HERE.md, README.md)
- Existing path references extracted from orientation docs

## Usage

```bash
python ai_repo_tools/main.py fast_analyze
python ai_repo_tools/main.py fast_analyze 20000
```

The optional numeric argument is `max_files`.
