
""" Keep-away environment OpenAI Gym test.
    
    Test to run the environment twice.

"""

import unittest
import gym
from absl.testing import parameterized

# class GymTest(parameterized.TestCase):
    
#         @parameterized.parameters(
#             ("keepaway-v0", 3, 3, 3),
#             ("keepaway-v0", 3, 3, 3),
#             ("keepaway-v0", 3, 3, 3),
#         )
#         def test_create_env(self, env_name, num_agents, num_keepers, num_takers):
#             env = gym.make(env_name)
#             self.assertEqual(env.num_agents, num_agents)
#             self.assertEqual(env.num_keepers, num_keepers)
#             self.assertEqual(env.num_takers, num_takers)
#             self.assertEqual(env.action_space.shape, (num_agents, 2))
#             self.assertEqual(env.observation_space.shape, (num_agents, 2))
#             self.assertEqual(env.reward_range, (-float("inf"), float("inf")))


class GymTest(parameterized.TestCase):
     def test_environment(self):
        # Tests it is possible to create and run an environment twice.
        for _ in range(2):
            env = gym.make('keepaway.envs:keepaway_env.KeepawayEnv',
                            stacked=True)
            env.reset()
        for _ in range(10):
            _, _, done, _ = env.step(env.action_space.sample())
            if done:
                env.reset()
        env.close()


if __name__ == '__main__':
  unittest.main()
    