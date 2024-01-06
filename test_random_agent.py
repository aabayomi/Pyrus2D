from __future__ import absolute_import, division, print_function

import time
from absl import logging
from env import KeepawayEnv
from experiments.policies.random_agent import RandomPolicy
logging.set_verbosity(logging.DEBUG)


def main():
    env = KeepawayEnv()
    episodes = 10
    print("Training episodes")
    print("launching game")
    env._launch_game()
    agents = env.num_keepers
    policy = RandomPolicy()

    for e in range(episodes):
        print(f"Episode {e}")
        env.reset()
        terminated = False
        episode_reward = 0
        env.start()

        while not terminated:
            obs = env.get_obs()
            actions, agent_infos = policy.get_actions(obs,greedy=False)
            # print(actions)
            reward, terminated, info = env.step(actions)
            time.sleep(0.15)
            episode_reward += reward

    print("closing game")
    env.close()

if __name__ == "__main__":
    main()