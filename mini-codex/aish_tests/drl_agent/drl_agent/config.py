from dataclasses import dataclass


@dataclass
class DQNConfig:
    env_id: str = "CartPole-v1"
    seed: int = 7

    gamma: float = 0.99
    lr: float = 1e-3
    batch_size: int = 64
    replay_capacity: int = 50_000
    min_replay_size: int = 1_000
    target_update_steps: int = 500

    epsilon_start: float = 1.0
    epsilon_end: float = 0.05
    epsilon_decay_steps: int = 20_000

    max_steps: int = 40_000
    eval_episodes: int = 10
    hidden_size: int = 128
