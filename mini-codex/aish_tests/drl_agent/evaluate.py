import argparse

import gymnasium as gym
import numpy as np
import torch

from drl_agent.config import DQNConfig
from drl_agent.dqn_agent import DQNAgent


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate trained DQN agent.")
    parser.add_argument("--model", default="models/dqn_cartpole.pt", help="Path to trained model.")
    parser.add_argument("--episodes", type=int, default=None, help="Number of eval episodes.")
    args = parser.parse_args()

    cfg = DQNConfig()
    if args.episodes is not None:
        cfg.eval_episodes = args.episodes

    env = gym.make(cfg.env_id)
    obs_dim = int(env.observation_space.shape[0])
    action_dim = int(env.action_space.n)

    agent = DQNAgent(obs_dim, action_dim, cfg)
    state_dict = torch.load(args.model, map_location=agent.device)
    agent.q_net.load_state_dict(state_dict)
    agent.q_net.eval()

    returns = []
    for ep in range(cfg.eval_episodes):
        obs, _ = env.reset(seed=cfg.seed + ep)
        done = False
        ep_return = 0.0
        while not done:
            action = agent.select_action(obs, greedy=True)
            obs, reward, terminated, truncated, _ = env.step(action)
            done = bool(terminated or truncated)
            ep_return += float(reward)
        returns.append(ep_return)

    print(f"episodes={cfg.eval_episodes} mean_return={np.mean(returns):.2f} std_return={np.std(returns):.2f}")
    env.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
