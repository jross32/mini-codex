"""Generic entity model reused by all game types"""
from dataclasses import dataclass, field
from typing import Dict, Any

class Entity:
    """Universal entity"""
    def __init__(self, entity_id, name, stats):
        self.entity_id = entity_id
        self.name = name
        self.stats = stats

    def get_stat(self):
        return self.stats.get(key, 0)

