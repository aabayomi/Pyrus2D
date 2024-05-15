import time
from absl import logging
from keepaway.envs.keepaway_wrapper import KeepawayWrapper
from keepaway.envs.policies.random_agent import RandomPolicy
from keepaway.config.game_config import get_config
logging.set_verbosity(logging.DEBUG)


config = get_config()["3v2"]


def main():
    env = KeepawayWrapper(False,config)
    episodes = 3
    env.launch_game()
    policy = RandomPolicy(config)
    env.render()
    for e in range(episodes):
        print(f"Episode {e}")
        env.reset()
        terminated = False
        episode_reward = 0
        env.start()
        while not terminated:
            obs = env.get_obs()
            actions, agent_infos = policy.get_actions(obs)
            obs, reward, terminated, info = env.step(actions)
            # print(f"Obs: {obs}" ,f"Reward: {reward}", f"Terminated: {terminated}", f"Info: {info}", f"Actions: {actions}")
            time.sleep(0.15)
            episode_reward += reward

    print("closing game")
    env.close()

if __name__ == "__main__":
    main()