from keepaway.envs import keepaway_env

import gym
from gym.envs.registration import register
import logging

logger = logging.getLogger(__name__)

register(
    id='keepaway-v0',
    entry_point='keepaway.envs:keepaway_env.KeepawayEnv',
)