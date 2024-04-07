"""PyTorch algorithms."""
from keepaway.garage.torch.algos._utils import _Default  # noqa: F401
from keepaway.garage.torch.algos._utils import compute_advantages  # noqa: F401
from keepaway.garage.torch.algos._utils import filter_valids  # noqa: F401
from keepaway.garage.torch.algos._utils import make_optimizer  # noqa: F401
from keepaway.garage.torch.algos._utils import pad_to_last  # noqa: F401
from keepaway.garage.torch.algos.ddpg import DDPG
# VPG has to been import first because it is depended by PPO and TRPO.
from keepaway.garage.torch.algos.vpg import VPG
from keepaway.garage.torch.algos.ppo import PPO  # noqa: I100
from keepaway.garage.torch.algos.trpo import TRPO
from keepaway.garage.torch.algos.maml_ppo import MAMLPPO  # noqa: I100
from keepaway.garage.torch.algos.maml_trpo import MAMLTRPO
from keepaway.garage.torch.algos.maml_vpg import MAMLVPG

__all__ = ['DDPG', 'VPG', 'PPO', 'TRPO', 'MAMLPPO', 'MAMLTRPO', 'MAMLVPG']
