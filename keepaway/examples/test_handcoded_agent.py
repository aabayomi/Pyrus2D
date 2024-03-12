import time
from absl import logging
logging.set_verbosity(logging.DEBUG)
from keepaway.envs.keepaway_env import KeepawayEnv
from keepaway.envs.policies.handcoded_agent import HandcodedPolicy


def main():
    env = KeepawayEnv()
    episodes = 20
    env._launch_game()
    agents = env.num_keepers
    policy = HandcodedPolicy()
    env.render()
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
            # print("reward ", reward, "terminated ", terminated, "info ", info)
            # print("matrix jfjfj ", env.get_proximity_adj_mat())
            time.sleep(0.15)
            episode_reward += reward

    print("closing game")
    env.close()

if __name__ == "__main__":
    main()