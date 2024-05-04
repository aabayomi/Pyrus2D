import time
from absl import logging
from keepaway.envs.keepaway_env import KeepawayEnv
from keepaway.envs.policies.random_agent import RandomPolicy
from keepaway.config.game_config import get_config
logging.set_verbosity(logging.DEBUG)

config = get_config()["5v4"]

def main():
    env = KeepawayEnv(config)
    episodes = 10
    print("Training episodes")
    print("launching game")
    env.launch_game()
    policy = RandomPolicy(config)
    env.render()
    for e in range(episodes):
        print("Episode: {}".format(e))
        env.reset()
        terminated = False
        episode_reward = 0
        env.start()

        while not terminated:
            obs = env.get_obs()
            actions, agent_infos = policy.get_actions(obs)
            # print(actions)
            reward, terminated, info = env.step(actions)
            time.sleep(0.15)
            episode_reward += reward

    print("closing game")
    env.close()


if __name__ == "__main__":
    main()
