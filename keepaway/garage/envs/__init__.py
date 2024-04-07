"""Garage wrappers for gym environments."""

from keepaway.garage.envs.base import GarageEnv
from keepaway.garage.envs.base import Step
from keepaway.garage.envs.env_spec import EnvSpec
# from garage.envs.grid_world_env import GridWorldEnv
# from garage.envs.half_cheetah_dir_env import HalfCheetahDirEnv
# from garage.envs.half_cheetah_vel_env import HalfCheetahVelEnv
from keepaway.garage.envs.normalized_env import normalize
# from garage.envs.point_env import PointEnv
# from garage.envs.task_onehot_wrapper import TaskOnehotWrapper

__all__ = [
    'GarageEnv', 'Step', 'EnvSpec', 'normalize'
]
