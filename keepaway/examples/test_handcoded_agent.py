import time
import matplotlib.pyplot as plt
from absl import logging
logging.set_verbosity(logging.DEBUG)
from keepaway.envs.keepaway_env import KeepawayEnv
from keepaway.envs.policies.handcoded_agent import HandcodedPolicy
from keepaway.config.game_config import get_config

config = get_config()["3v1"]


def main():
    env = KeepawayEnv(config)
    episodes = 10
    env._launch_game()
    policy = HandcodedPolicy(config)
    env.render()
    reward_list = []
    for e in range(episodes):
        print(f"Episode {e}")
        env.reset()
        terminated = False
        episode_reward = 0
        env.start()
        while not terminated:
            obs = env.get_obs()
            # print(obs)
            actions, agent_infos = policy.get_actions(obs)
            reward, terminated, info = env.step(actions)
<<<<<<< Updated upstream
            time.sleep(0.15)
=======
            # print("reward ", reward, "terminated ", terminated, "info ", info)
            # print("matrix jfjfj ", env.get_proximity_adj_mat())
            # time.sleep(0.15)
>>>>>>> Stashed changes
            episode_reward += reward
        time.sleep(0.5)
        reward_list.append(reward)  

    plt.plot(range(episodes), reward_list)
    plt.show()
    print(reward_list)
    print(sum(reward_list)/len(reward_list))
    print("closing game")
    env.close()

if __name__ == "__main__":
    main()