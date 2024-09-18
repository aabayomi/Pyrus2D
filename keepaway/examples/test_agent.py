import time
import yaml
import argparse
import os
from absl import logging
from keepaway.envs.keepaway_env import KeepawayEnv
from keepaway.envs.policies.random_agent import RandomPolicy
from keepaway.envs.policies.always_hold import AlwaysHoldPolicy
from keepaway.envs.policies.handcoded_agent import HandcodedPolicy
from keepaway.config.game_config import get_config

from absl import flags, app


# Edit the configuration path if needed(this is the default path)
agent_config_path = os.getcwd() + "/config/sample_agent_config.yml"


def load_agent_config(file_path):
    with open(file_path) as f:
        return yaml.safe_load(f)


def setup_environment(config):
    # print(f"Environment setup with configuration: {config}")
    config = get_config()[config]
    return config


def setup_agent(policy):
    # print(f"Agent setup with policy: {policy}")
    agent_config = policy
    return agent_config


def test_agent(env_configs, agent_config, nepisode, nsteps):
    print(f"nepisode: {nepisode}, nsteps: {nsteps}")

    if agent_config.get("policy") == "random":
        policy = RandomPolicy(env_configs)
    elif agent_config.get("policy") == "always-hold":
        policy = AlwaysHoldPolicy(env_configs)
    elif agent_config.get("policy") == "handcoded":
        policy = HandcodedPolicy(env_configs)
    else:
        raise ValueError(f"Unknown policy: {agent_config.get('policy')}")

    env = KeepawayEnv(env_configs)
    env.launch_game()
    env.render()
    time.sleep(1)
    for e in range(nepisode):
        env.reset()
        terminated = False
        episode_reward = 0
        env.start()
        while not terminated:
            obs = env.get_obs()
            actions, agent_infos = policy.get_actions(obs)
            reward, terminated, info = env.step(actions)
            episode_reward += reward
    env.close()


def run(args):
    agent_configs = load_agent_config(agent_config_path)
    env_config = args.gc
    agent_config = agent_configs.get(args.policy, {})

    if not env_config:
        raise ValueError(f"Unknown environment configuration: {args.gc}")
    if not agent_config:
        raise ValueError(f"Unknown agent configuration: {args.policy}")

    environment = setup_environment(env_config)
    agent = setup_agent(agent_config)

    # print(f"Training agent with configuration: {agent}")
    # print(f"Training agent with environment configuration: {environment}")

    test_agent(environment, agent, args.nepisode, args.nsteps)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Train an agent with specific configurations."
    )
    parser.add_argument(
        "--gc",
        type=str,
        default="3v2",
        help='Configuration to use, defines the number of keepers e.g., "3v2", "4v3", or "5v4"',
    )
    parser.add_argument(
        "--num_timesteps",
        type=int,
        default=int(2e6),
        help="Number of timesteps to run for.",
    )
    parser.add_argument("--nepisode", type=int, default=5, help="Number of episodes")
    parser.add_argument(
        "--nsteps",
        type=int,
        default=128,
        help="Number of environment steps per epoch; batch size is nsteps * nenv",
    )
    parser.add_argument(
        "--policy",
        type=str,
        default="handcoded",
        help='Policy to use, e.g., "handcoded", "always-hold", "random"',
    )

    args = parser.parse_args()
    run(args)
