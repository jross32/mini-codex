# fast_evaluate

Deterministic evaluation tool built on fast_prepare.

## What it returns

- Evaluation score and rating
- Confirmed checks from preparation output
- Primary orientation doc, follow-ups, and compact step plan

## Usage

```bash
python ai_repo_tools/main.py fast_evaluate
python ai_repo_tools/main.py fast_evaluate 20000
```

The optional numeric argument is `max_files` forwarded to fast_prepare.
