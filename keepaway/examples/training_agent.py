import time
import yaml
import os
from absl import logging
from keepaway.envs.keepaway_env import KeepawayEnv
from keepaway.envs.policies.random_agent import RandomPolicy
from keepaway.envs.policies.always_hold import AlwaysHoldPolicy
from keepaway.envs.policies.handcoded_agent import HandcodedPolicy
from keepaway.config.game_config import get_config

from absl import flags, app
FLAGS = flags.FLAGS


# Edit the configuration path if needed(this is the default path)
agent_config_path = os.getcwd() + "/config/sample_agent_config.yml"


# Environment
flags.DEFINE_string('config', '3v2', 'Configuration to use, defines the number of keepers e.g., "3v2" , "4v3" or 5v4')
flags.DEFINE_integer('num_timesteps', int(2e6),
                     'Number of timesteps to run for.')
flags.DEFINE_integer('nepisode', 10, 'Number of episodes ')
flags.DEFINE_integer('nsteps', 128, 'Number of environment steps per epoch; '
                     'batch size is nsteps * nenv')

# Algorithm
flags.DEFINE_string('policy', 'handcoded', 'Policy to use, e.g., "handcoded", "always-hold", "random"')


def load_agent_config(file_path):
    with open(file_path) as f:
        return yaml.safe_load(f)
    

def setup_environment(config):
    # print(f"Environment setup with configuration: {config}")
    config = config
    return config

def setup_agent(policy):
    # print(f"Agent setup with policy: {policy}")
    agent_config = policy
    return agent_config


def train_agent(env_config, agent_config):

    if agent_config.get('policy') == 'random':
        policy = RandomPolicy()
    elif agent_config.get('policy') == 'always-hold':
        policy = AlwaysHoldPolicy()
    elif agent_config.get('policy') == 'handcoded':
        policy = HandcodedPolicy()
    else:
        raise ValueError(f"Unknown policy: {agent_config.get('policy')}")

    env = KeepawayEnv(env_config)
    env._launch_game()

    for e in range(FLAGS.nepisode):
        env.reset()
        terminated = False
        episode_reward = 0
        env.start()
        while not terminated:
            obs = env.get_obs()
            actions, agent_infos = policy.get_actions(obs, greedy=True)
            reward, terminated, info = env.step(actions)
            episode_reward += reward
    print("closing game")
    env.close()

    
def main(argv):
    del argv  # Unused

    # Load configurations
    # print(get_config())

    env_configs = get_config()
    agent_configs = load_agent_config(agent_config_path)

    # Select specific configurations based on flags
    env_config = env_configs.get(FLAGS.config)
    agent_config = agent_configs.get(FLAGS.policy, {})
    

    if not env_config:
        raise ValueError(f"Unknown environment configuration: {FLAGS.env_config}")
    if not agent_config:
        raise ValueError(f"Unknown agent configuration: {FLAGS.agent_config}")

    # Setup environment and agent using the selected configurations
    environment = setup_environment(env_config)
    agent = setup_agent(agent_config)

    # Train the agent
    train_agent(environment, agent)

if __name__ == '__main__':
    app.run(main)
