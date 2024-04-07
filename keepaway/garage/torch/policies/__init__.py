"""PyTorch Policies."""
from keepaway.garage.torch.policies.base import Policy
from keepaway.garage.torch.policies.deterministic_mlp_policy import (
    DeterministicMLPPolicy)
from keepaway.garage.torch.policies.gaussian_mlp_policy import GaussianMLPPolicy

__all__ = ['DeterministicMLPPolicy', 'GaussianMLPPolicy', 'Policy']
