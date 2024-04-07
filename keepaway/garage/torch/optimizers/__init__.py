"""PyTorch optimizers."""
from keepaway.garage.torch.optimizers.conjugate_gradient_optimizer import (
    ConjugateGradientOptimizer)
from keepaway.garage.torch.optimizers.differentiable_sgd import DifferentiableSGD

__all__ = ['ConjugateGradientOptimizer', 'DifferentiableSGD']
