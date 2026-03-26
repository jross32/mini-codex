
"""Custom policy/network hooks.

Right now, the ensemble agent uses Stable-Baselines3 default MLP policies,
but this module is where you would define custom LSTM/attention networks
and plug them into SB3 via policy_kwargs.
"""

# Example skeleton for a custom feature extractor if you want to extend later:
#
# import torch as th
# from torch import nn
# from stable_baselines3.common.torch_layers import BaseFeaturesExtractor
#
#
# class TemporalAttentionExtractor(BaseFeaturesExtractor):
#     """Toy example of a temporal attention-based feature extractor."""
#
#     def __init__(self, observation_space, features_dim: int = 128):
#         super().__init__(observation_space, features_dim)
#         n_input = observation_space.shape[0]
#         self.net = nn.Sequential(
#             nn.Linear(n_input, 256),
#             nn.ReLU(),
#             nn.Linear(256, features_dim),
#             nn.ReLU(),
#         )
#
#     def forward(self, observations: th.Tensor) -> th.Tensor:
#         return self.net(observations)
