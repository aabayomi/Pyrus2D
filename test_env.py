from __future__ import absolute_import, division, print_function

import time
from os import replace

import numpy as np
import random
from absl import logging
# from env import KeepawayEnv

logging.set_verbosity(logging.DEBUG)

from env import KeepawayEnv


def main():
    env = KeepawayEnv()
    episodes = 1
    print("Training episodes")
    # env.reset()
    print("launching game")
    env._launch_game()
    agents = env.num_keepers

    for e in range(episodes):
        print(f"Episode {e}")
        # env.reset()
        terminated = False
        episode_reward = 0
        env.start()
        while not terminated:
            # obs = env.get_obs()
            # print(f"Obs size: {obs[0].shape}")
            # state = env.get_state()
            # cap = env.get_capabilities()
            # env.render()  # Uncomment for rendering
            ##
            ## at a time step, select a all actions for all agents
            ## if not kickable action pass
            ## else if the is a kickable action wait
            ## select action
            ## take action

            actions = []
            for agent_id in range(agents + 1):
                avail_actions = env.get_avail_agent_actions(agent_id)
                # avail_actions_ind = np.nonzero(avail_actions)[0]
                # print(f"Agent {agent_id} avail actions: {avail_actions}")
                # action = random.choice(avail_actions)
                # print(f"Agent {agent_id} action: {avail_actions}")
                actions.append(avail_actions)
            
            print(f"Actions: {actions}")
            reward, terminated, _ = env.step(actions)
            time.sleep(0.15)
            episode_reward += reward
    
    

    print("closing game")
    env.close()


def test_player_logic():
    env = KeepawayEnv()
    episodes = 1
    print("Training episodes")
    # env.reset()
    print("launching game")
    env.start()



def test():
    agents = 3
    observations = {agent: None for agent in range(2, agents + 2) }
    print(observations)

if __name__ == "__main__":
    # test()
    main()
    # test_player_logic()
