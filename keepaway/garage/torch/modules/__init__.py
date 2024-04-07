"""Pytorch modules."""

from keepaway.garage.torch.modules.gaussian_mlp_module import \
    GaussianMLPIndependentStdModule, GaussianMLPModule, \
    GaussianMLPTwoHeadedModule
from keepaway.garage.torch.modules.mlp_module import MLPModule
from keepaway.garage.torch.modules.multi_headed_mlp_module import MultiHeadedMLPModule

__all__ = [
    'MLPModule', 'MultiHeadedMLPModule', 'GaussianMLPModule',
    'GaussianMLPIndependentStdModule', 'GaussianMLPTwoHeadedModule'
]
