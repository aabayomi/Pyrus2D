from __future__ import absolute_import, division, print_function

import time
from absl import logging
logging.set_verbosity(logging.DEBUG)
from env import KeepawayEnv
from experiments.policies.handcoded_agent import HandcodedPolicy


def main():
    env = KeepawayEnv()
    episodes = 20
    env._launch_game()
    agents = env.num_keepers
    policy = HandcodedPolicy()

    for e in range(episodes):
        print(f"Episode {e}")
        env.reset()
        terminated = False
        episode_reward = 0
        env.start()

        while not terminated:
            obs = env.get_obs()
            actions, agent_infos = policy.get_actions(obs,greedy=True)
            # print("actions ", actions)
            reward, terminated, info = env.step(actions)
            print("reward ", reward, "terminated ", terminated, "info ", info)
            time.sleep(0.15)
            episode_reward += reward

    print("closing game")
    env.close()

if __name__ == "__main__":
    main()