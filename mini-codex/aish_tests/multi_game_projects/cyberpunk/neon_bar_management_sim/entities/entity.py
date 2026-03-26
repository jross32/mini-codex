"""Generic entity model reused by all game types."""


class Entity:
    """Universal entity."""

    def __init__(self, entity_id, name, stats):
        self.entity_id = entity_id
        self.name = name
        self.stats = stats

    def get_stat(self, key, default=0):
        return self.stats.get(key, default)
