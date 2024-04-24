
"""
Wrapper for the reward function of the keep-away environment.
An example for encouraging passing the ball among keepers.

"""

import gym

class CheckpointReward(gym.RewardWrapper):
  """ Reward shaping for the keepaway environment."""

  def __init__(self, env):
    gym.RewardWrapper.__init__(self, env)
    self._collected_checkpoints = {}
    self._num_checkpoints = self.num_keepers
    self._checkpoint_reward = 1

  def reset(self):
    self._collected_checkpoints = {}
    return self.env.reset()


  ## Test the reward function
  def reward(self, reward):
    """ Reward is given for a successful pass"""
    observation = self.env.observation()
    if observation is None:
      return reward

    for i in range(self.num_keepers):
        keeper = observation[i]
        if keeper[0] == 1:
            keeper_id = keeper[1]
            if keeper_id not in self._collected_checkpoints:
                self._collected_checkpoints[keeper_id] = 1
            reward += self._checkpoint_reward
    return reward