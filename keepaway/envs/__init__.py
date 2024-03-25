from functools import partial
from keepaway.envs.keepaway_env import KeepawayEnv
from keepaway.envs.multiagentenv import MultiAgentEnv

def env_fn(env, **kwargs):
    return env(**kwargs)

def env_(env_class, **kwargs):
    """Wrapper function to create environments with dynamic configurations."""
    return env_fn(env=env_class, **kwargs)

REGISTRY = {}
# REGISTRY["keepaway"] = partial(env_fn, env=KeepawayEnv)
REGISTRY["keepaway"] = lambda **kwargs: env_(KeepawayEnv, **kwargs)


# from keepaway.envs.keepaway_wrapper import KeepawayEnv
# __all__ = [
#     "KeepawayEnv",
# ]

