"""Engine runtime for the cyberpunk bar simulation."""

from dataclasses import dataclass


@dataclass
class Engine:
    mode: str = "cyberpunk_bar"
    tick: int = 0

    def next_tick(self) -> int:
        self.tick += 1
        return self.tick

    def run(self) -> None:
        print(f"Running {self.mode} engine at tick {self.tick}")
