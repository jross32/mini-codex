import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any


def write_step_log(state, step_record: Dict[str, Any], memory_file: str):
    path = Path(memory_file)
    path.parent.mkdir(parents=True, exist_ok=True)

    entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "state": {
            "goal": state.goal,
            "repo_path": state.repo_path,
            "steps_taken": state.steps_taken,
            "tools_used": state.tools_used,
            "known_files": state.known_files,
            "artifacts": state.artifacts,
            "status": state.status,
        },
        **step_record,
    }

    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    return entry
