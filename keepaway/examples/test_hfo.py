"""
Test HFO Handconded Agent

"""

import time
from absl import logging
logging.set_verbosity(logging.DEBUG)
from keepaway.envs.hfo_env import HFOEnv
from keepaway.envs.policies.hfo_handcoded_agent import HFOHandcodedPolicy
from keepaway.config.game_config import get_config
config = get_config()["hfo"]


def main():
    env = HFOEnv(config)
    episodes = 10
    print("Training episodes")
    print("launching game")
    env.launch_game()
    policy = HFOHandcodedPolicy(config)
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