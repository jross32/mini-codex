from typing import Tuple

import numpy as np
import torch
from torch import nn

from drl_agent.config import DQNConfig
from drl_agent.network import QNetwork
from drl_agent.replay_buffer import ReplayBuffer


class DQNAgent:
    def __init__(self, obs_dim: int, action_dim: int, cfg: DQNConfig):
        self.cfg = cfg
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        self.q_net = QNetwork(obs_dim, action_dim, cfg.hidden_size).to(self.device)
        self.target_net = QNetwork(obs_dim, action_dim, cfg.hidden_size).to(self.device)
        self.target_net.load_state_dict(self.q_net.state_dict())
        self.target_net.eval()

        self.optimizer = torch.optim.Adam(self.q_net.parameters(), lr=cfg.lr)
        self.loss_fn = nn.SmoothL1Loss()

        self.replay = ReplayBuffer(cfg.replay_capacity)
        self.action_dim = action_dim
        self.step_count = 0

    def epsilon(self) -> float:
        progress = min(1.0, self.step_count / float(self.cfg.epsilon_decay_steps))
        return self.cfg.epsilon_start + progress * (self.cfg.epsilon_end - self.cfg.epsilon_start)

    def select_action(self, obs: np.ndarray, greedy: bool = False) -> int:
        if (not greedy) and (np.random.random() < self.epsilon()):
            return int(np.random.randint(self.action_dim))

        with torch.no_grad():
            obs_t = torch.as_tensor(obs, dtype=torch.float32, device=self.device).unsqueeze(0)
            q_values = self.q_net(obs_t)
            return int(torch.argmax(q_values, dim=1).item())

    def remember(self, transition: Tuple[np.ndarray, int, float, np.ndarray, bool]) -> None:
        self.replay.add(transition)

    def train_step(self) -> float:
        if len(self.replay) < max(self.cfg.min_replay_size, self.cfg.batch_size):
            return 0.0

        batch = self.replay.sample(self.cfg.batch_size)
        obs, acts, rewards, nxt_obs, dones = zip(*batch)

        obs_t = torch.as_tensor(np.array(obs), dtype=torch.float32, device=self.device)
        acts_t = torch.as_tensor(np.array(acts), dtype=torch.long, device=self.device).unsqueeze(1)
        rewards_t = torch.as_tensor(np.array(rewards), dtype=torch.float32, device=self.device)
        nxt_obs_t = torch.as_tensor(np.array(nxt_obs), dtype=torch.float32, device=self.device)
        dones_t = torch.as_tensor(np.array(dones), dtype=torch.float32, device=self.device)

        q_pred = self.q_net(obs_t).gather(1, acts_t).squeeze(1)

        with torch.no_grad():
            nxt_q = self.target_net(nxt_obs_t).max(dim=1).values
            q_target = rewards_t + self.cfg.gamma * (1.0 - dones_t) * nxt_q

        loss = self.loss_fn(q_pred, q_target)

        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()

        self.step_count += 1
        if self.step_count % self.cfg.target_update_steps == 0:
            self.target_net.load_state_dict(self.q_net.state_dict())

        return float(loss.item())
