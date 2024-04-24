import random
import time
import numpy as np
from keepaway.envs.pettingzoo import ka2pz
from keepaway.envs.policies.random_agent import RandomPolicy

# def main():
#     """
#     run a random agent policy

#     """
#     env = ka2pz.env()
#     episodes = 10
#     total_reward = 0
#     done = False
#     completed_episodes = 0
#     policy = RandomPolicy()

#     for e in range(episodes):
#         print(f"Episode {e}")
#         info = env.reset()
#         terminated = False
#         episode_reward = 0
#         env.start()
#         env.render()

#         while not terminated:
#             obs = env.get_obs()
#             actions, agent_infos = policy.get_actions(obs, greedy=False)
#             # print(actions)
#             reward, terminated, info = env.step(actions)
#             time.sleep(0.15)
#             episode_reward += reward

#         total_reward += episode_reward

#     print("closing game")
#     env.close()
#     print("Average total reward", total_reward / episodes)


def main():
    """
    Runs an env object with random actions.
    """
    env = ka2pz.env()
    episodes = 10

    total_reward = 0
    done = False
    completed_episodes = 0

    while completed_episodes < episodes:
        env.reset()
        for agent in env.agent_iter():
            env.render()

            obs, reward, terms, truncs, _ = env.last()
            total_reward += reward
            if terms or truncs:
                action = None
            elif isinstance(obs, dict) and "action_mask" in obs:
                action = random.choice(np.flatnonzero(obs["action_mask"]))
            else:
                action = env.action_spaces[agent].sample()
            env.step(action)

        completed_episodes += 1

    env.close()

    print("Average total reward", total_reward / episodes)


if __name__ == "__main__":
    main()
