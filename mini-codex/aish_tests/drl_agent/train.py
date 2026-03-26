import argparse
import random
from pathlib import Path

import gymnasium as gym
import numpy as np
import torch

from drl_agent.config import DQNConfig
from drl_agent.dqn_agent import DQNAgent


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


def main() -> int:
    parser = argparse.ArgumentParser(description="Train a simple DQN agent.")
    parser.add_argument("--steps", type=int, default=None, help="Override max training steps.")
    parser.add_argument("--model-out", default="models/dqn_cartpole.pt", help="Output path for model state dict.")
    args = parser.parse_args()

    cfg = DQNConfig()
    if args.steps is not None:
        cfg.max_steps = args.steps

    set_seed(cfg.seed)

    env = gym.make(cfg.env_id)
    obs, _ = env.reset(seed=cfg.seed)

    obs_dim = int(env.observation_space.shape[0])
    action_dim = int(env.action_space.n)

    agent = DQNAgent(obs_dim, action_dim, cfg)

    episode_return = 0.0
    returns = []

    for step in range(1, cfg.max_steps + 1):
        action = agent.select_action(obs)
        nxt_obs, reward, terminated, truncated, _ = env.step(action)
        done = bool(terminated or truncated)

        agent.remember((obs, action, float(reward), nxt_obs, done))
        loss = agent.train_step()

        obs = nxt_obs
        episode_return += float(reward)

        if done:
            returns.append(episode_return)
            obs, _ = env.reset()
            episode_return = 0.0

        if step % 2000 == 0:
            recent = returns[-10:] if returns else [0.0]
            print(
                f"step={step} epsilon={agent.epsilon():.3f} "
                f"avg_return_last10={np.mean(recent):.2f} loss={loss:.4f}"
            )

    model_path = Path(args.model_out)
    model_path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(agent.q_net.state_dict(), model_path)
    print(f"saved_model={model_path}")

    env.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
