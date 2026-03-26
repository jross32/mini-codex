"""Roguelike dungeon subsystem"""
class DungeonGenerator:
    def __init__(self, seed):
        self.seed = seed

    def generate(self):
        return {'rooms': 10, 'seed': self.seed}

