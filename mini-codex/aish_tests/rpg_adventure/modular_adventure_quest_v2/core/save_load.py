"""V2 save/load functions"""
import json
from pathlib import Path

def save_game(player, save_path):
    p = Path(save_path)
    p.parent.mkdir(exist_ok=True)
    p.write_text(json.dumps(player), encoding='utf-8')
    return True


def load_game(save_path):
    p = Path(save_path)
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding='utf-8'))

