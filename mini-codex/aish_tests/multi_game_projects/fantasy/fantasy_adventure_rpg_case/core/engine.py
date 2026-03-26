"""Config-driven multi-game engine runtime"""
import json
from pathlib import Path

class Engine:
    """Main engine runtime for any game mode"""
    def __init__(self, mode, tick):
        self.mode = mode
        self.tick = tick

    def run(self):
        print(f'Running {self.mode} engine at tick {self.tick}')


def load_mode(path):
    return Path(path).read_text(encoding='utf-8')

