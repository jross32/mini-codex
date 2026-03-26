from dataclasses import dataclass, field

@dataclass
class Animal:
    species: str
    biome: str
    health: float = 100.0
    upkeep: float = 500.0
    keeper: str = 'trained'

@dataclass
class ZooState:
    cash: float = 50000.0
    day: int = 1
    prestige: int = 0
    animals: list = field(default_factory=list)
    reviews: list = field(default_factory=list)