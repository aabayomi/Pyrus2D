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
from vf import CentValueFunction
import random
import torch.nn as nn
import torch
import torch.optim as optim

config = get_config()["3v2"]
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

    env_configs = get_config()["3v2"]
    env = KeepawayEnv(env_configs)
    env._launch_game()
    env.render()
    time.sleep(1)
    
    
    
    Q = np.zeros((50, 4)) 

    e = np.zeros((50, 4))

    model_count = np.zeros((50, 4))

    gamma = 0.999
    alpha = 0.125
    _lambda = 1
    reward_list=[]
    bin_size = 1
    k = 0.5
    policy = RandomPolicy(env_configs)
    
    #state_vars [] -> [tile-coding index] = s
    #initialize Q(s, a) arbitrariliy as q

    #Initialize model array M(S, A)
    planning_iterations = 50
    sum_of_reward = 0
    vf = CentValueFunction(state_size=13)
    optimizer = optim.Adam(vf.parameters(), lr=0.01)
    criterion = nn.MSELoss()

    for episodes in range(nepisode):
        states = []
        observations = []
        predicted_state_reps = []
        actions = []
        next_states = []
        next_reward = []

    #     #initialize e(s, a) = 0 for all s, a
        print(f"Episode {episodes} out of nepisode {nepisode}")
        env.reset()
        # print("reset")
        _obs = env.get_obs()
        # print("obs")
        
        obs = _obs[2]
        while(type(obs) == dict and 'state_vars' in obs):
            obs = obs['state_vars']
        
        observations.append(obs)
        
        
        value_function = vf(obs)
        predicted_state_reps.append(value_function)
        state_index = max(0, min(49, int((value_function * 10) + 25 + 0.5)))

        
        # print(vf(obs))

        action = epsilon_greedy(Q, state_index)
        done = False
        env.start()
        while not done:
            obs = env.get_obs()[2]
            reward, done, _ = env.step([np.random.randint(0, 4), action, np.random.randint(0, 4)])
            
           
            # obs = env.get_obs()
            
            while(type(obs) == dict and 'state_vars' in obs):
                obs = obs['state_vars']

            # print("obs ", obs)
            # next_state_index = V.get_feature_vector(obs)
            value_function = vf(obs)
            observations.append(obs)
            predicted_state_reps.append(value_function)

            next_state_index = max(0, min(49, int((value_function * 10) + 25 + 0.5)))
            # print("next_state_index ", next_state_index)
            # print(vf(obs))
            next_action = epsilon_greedy(Q, next_state_index)
            next_Q_value = Q[next_state_index, next_action]
            current_Q_value = Q[state_index, action]
            delta = reward + gamma * next_Q_value - current_Q_value
            e[state_index, action] = 1

            states.append(state_index)
            actions.append(action)
            next_states.append(next_state_index)
            next_reward.append(reward)


            for i in range(50):
                for l in range(4):
                    Q[i, l] += alpha * delta * e[i, l]
                    e[i, l] = gamma * _lambda * e[i, l]

            state_index = next_state_index
            action = next_action
          
        sum_of_reward += reward
        
        ## Train CVF
        for obs in observations:
            # print(state)
            # print(sum_of_rewar
            loss = criterion(vf(obs), torch.tensor(float(sum_of_reward), dtype=torch.float32, requires_grad=True))
            optimizer.zero_grad()
            loss.backward()


        if(episodes % bin_size == bin_size - 1):
            # print("Sum of reward ", sum_of_reward)
            reward_list.append(sum_of_reward/bin_size)
            # print(reward_list)
            sum_of_reward = 0

        time.sleep(0.25)
        for _ in range(planning_iterations):
            index = np.random.randint(0, len(states))
            random_state = states[index]
            random_action = actions[index]
            random_next_state = next_states[index]
            random_reward = next_reward[index] + k * np.sqrt(model_count[random_state, random_action])
            max_q = np.NINF
            for possible_action in range(4):
                max_q = max(max_q, Q[random_next_state, possible_action])
            Q[random_state, random_action] += alpha * (random_reward + gamma * max_q - Q[random_state, random_action])

            model_count[random_state, random_action] = 0
            for state in states:
                for action in actions:
                    if(state != random_state and action != random_action):
                        model_count[state, action] += 1


    print("The reward_list ", reward_list)
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
