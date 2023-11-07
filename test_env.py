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
    episodes = 3
    print("Training episodes")
    print("launching game")
    env._launch_game()
    agents = env.num_keepers

    for e in range(episodes):
        print(f"Episode {e}")
        env.reset()
        terminated = False
        episode_reward = 0
        env.start()

        while not terminated:
            obs = env.get_obs()
            # print(f"Obs: {obs}")
            # actions, agent_infos = policy.get_actions(obs,
            #         avail_actions, greedy=greedy)

            # obs, reward, terminated, info = env.step(actions[0])
            actions = []
            for agent_id in range(agents + 1):
                avail_actions = env.get_avail_agent_actions(agent_id)
                actions.append(avail_actions)

            # print(f"Actions: {actions}")
            reward, terminated, _ = env.step(actions)
            if terminated:
                print("terminated", e)
            # print(reward, terminated, _)

            time.sleep(0.15)
            episode_reward += reward

    print("closing game")
    env.close()







if __name__ == "__main__":
    # test()
    main()
    # test_player_logic()
