"""Reinforcement learning algorithms which use NumPy as a numerical backend."""
from keepaway.garage.np.algos.base import RLAlgorithm
from keepaway.garage.np.algos.batch_polopt import BatchPolopt
from keepaway.garage.np.algos.cem import CEM
from keepaway.garage.np.algos.cma_es import CMAES
from keepaway.garage.np.algos.meta_rl_algorithm import MetaRLAlgorithm
from keepaway.garage.np.algos.nop import NOP
from keepaway.garage.np.algos.off_policy_rl_algorithm import OffPolicyRLAlgorithm

__all__ = [
    'RLAlgorithm', 'BatchPolopt', 'CEM', 'CMAES', 'MetaRLAlgorithm', 'NOP',
    'OffPolicyRLAlgorithm'
]
