# DRL Agent Test Project

A minimal Deep Q-Network (DQN) agent for CartPole using Gymnasium + PyTorch.

## Setup

```bash
pip install -r requirements.txt
```

## Train

```bash
python train.py --steps 20000 --model-out models/dqn_cartpole.pt
```

## Evaluate

```bash
python evaluate.py --model models/dqn_cartpole.pt --episodes 10
```

## Files

- drl_agent/config.py: training hyperparameters
- drl_agent/network.py: Q-network MLP
- drl_agent/replay_buffer.py: replay memory
- drl_agent/dqn_agent.py: epsilon-greedy DQN logic
- train.py: training loop
- evaluate.py: deterministic policy evaluation
