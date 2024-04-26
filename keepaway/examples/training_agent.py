import time
import yaml
import argparse
import os
import numpy as np
import matplotlib.pyplot as plt
from absl import logging
from keepaway.envs.keepaway_env import KeepawayEnv
from keepaway.envs.policies.random_agent import RandomPolicy
from keepaway.envs.policies.always_hold import AlwaysHoldPolicy
from keepaway.envs.policies.handcoded_agent import HandcodedPolicy
from keepaway.config.game_config import get_config
from tc import ValueFunctionWithTile

config = get_config()["3v1"]
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


def epsilon_greedy(Q, state_index): #10 x 5 x 5 x 3
    epsilon = 0.1
    s = np.random.binomial(1, epsilon)
    if(s == 1):
        return np.random.randint(0, 4)
    else:
        return np.argmax(Q[state_index])

def train_agent(env_configs, agent_config, nepisode, nsteps):

    if agent_config.get('policy') == 'random':
        policy = RandomPolicy(env_configs)
    elif agent_config.get('policy') == 'always-hold':
        policy = AlwaysHoldPolicy(env_configs)
    elif agent_config.get('policy') == 'handcoded':
        policy = HandcodedPolicy(env_configs)
    # elif agent_config.get('policy') == 'epsilon_greedy':
    #     policy = epsilon_greedy(env_configs)
    else:
        raise ValueError(f"Unknown policy: {agent_config.get('policy')}")

    env_configs = get_config()["3v1"]
    env = KeepawayEnv(env_configs)
    env._launch_game()
    env.render()
    time.sleep(1)
    
    state_low = np.zeros(13)
    state_high = np.array([28.29, 28.29, 28.29, 28.29, 28.29, 28.29, 28.29, 28.29, 28.29, 28.29, 28.29, 90, 90]) #come back to make last two 90
    V = ValueFunctionWithTile(
        state_low,
        state_high,
        num_tilings=10,
        tile_width=np.array([8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 29, 29])) 
    
    Q = np.zeros((10*10*5*5, 4)) 

    e = np.zeros((10*10*5*5, 4))

    gamma = 0.999
    alpha = 0.125
    _lambda = 1
    reward_list=[]
    bin_size = 500
    policy = HandcodedPolicy(env_configs)
    #state_vars [] -> [tile-coding index] = s
    #initialize Q(s, a) arbitrariliy as q

    #Initialize model array M(S, A)
    #planning_iterations = n
    sum_of_reward = 0
    for episodes in range(nepisode):
    #     #initialize e(s, a) = 0 for all s, a
        print(f"Episode {episodes}")
        env.reset()
        _obs = env.get_obs()
        
        obs = _obs[2]
        while(type(obs) == dict and 'state_vars' in obs):
            obs = obs['state_vars']
        state_index = V.get_feature_vector(obs)
        action = epsilon_greedy(Q, state_index)
        done = False
        env.start()
        while not done:
            obs = env.get_obs()[2]
            reward, done, _ = env.step([np.random.randint(0, 4), action, np.random.randint(0, 4)])
            if not done:
                continue
            # obs = env.get_obs()
            
            while(type(obs) == dict and 'state_vars' in obs):
                obs = obs['state_vars']

            # print("obs ", obs)
            next_state_index = V.get_feature_vector(obs)
            next_action = epsilon_greedy(Q, next_state_index)
            next_Q_value = Q[next_state_index, next_action]
            current_Q_value = Q[state_index, action]
            delta = reward + gamma * next_Q_value - current_Q_value
            e[state_index, action] = 1

            for i in range(10*5*5*10):
                for l in range(4):
                    Q[i, l] += alpha * delta * e[i, l]
                    e[i, l] = gamma * _lambda * e[i, l]
            action = next_action
            # print(np.any(Q))
            # print(Q[np.where(Q!=0)])
            # print(np.any(e))
            # print(e[np.where(e!=0)])
            # print(Q,e)
        sum_of_reward += reward
        if(episodes % bin_size == bin_size - 1):
            reward_list.append(sum_of_reward/bin_size)
            print(reward_list)
            sum_of_reward = 0
        time.sleep(0.25)

        #for i in range(n):
        # perform Q learning over all M(S, A)
    plt.plot(range(int(nepisode/bin_size)), reward_list)
    plt.show()
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

    train_agent(environment, agent, args.nepisode, args.nsteps)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Train an agent with specific configurations.')
    parser.add_argument('--gc', type=str, default='3v2',
                        help='Configuration to use, defines the number of keepers e.g., "3v2", "4v3", or "5v4"')
    parser.add_argument('--num_timesteps', type=int, default=int(2e6),
                        help='Number of timesteps to run for.')
    parser.add_argument('--nepisode', type=int, default=10,
                        help='Number of episodes')
    parser.add_argument('--nsteps', type=int, default=128,
                        help='Number of environment steps per epoch; batch size is nsteps * nenv')
    parser.add_argument('--policy', type=str, default='handcoded',
                        help='Policy to use, e.g., "handcoded", "always-hold", "random"')
    # main()
    args = parser.parse_args()
    run(args)