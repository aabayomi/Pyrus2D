from functools import partial
# from envs.multiagentenv import MultiAgentEnv
# from envs.keepaway import KeepawayEnv
from experiments.envs.multiagentenv import MultiAgentEnv
from experiments.envs.keepaway import KeepawayEnv
import sys
import os

def env_fn(env, **kwargs) -> MultiAgentEnv:
    return env(**kwargs)

REGISTRY = {}
REGISTRY["ka"] = partial(env_fn, env=KeepawayEnv)