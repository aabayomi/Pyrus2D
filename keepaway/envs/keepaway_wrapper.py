# # Using local gym
from keepaway.envs import KeepawayEnv
import gym
import numpy as np


class KeepawayWrapper(KeepawayEnv):
    def __init__(self, centralized, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.reward_range = (-np.inf, np.inf)
        self.viewer = None
        self.action_space = gym.spaces.Discrete(self.n_actions)
        self.agent_obs_dim = np.sum(
            [
                np.prod(self.get_obs_move_feats_size()),
                np.prod(self.get_obs_enemy_feats_size()),
                np.prod(self.get_obs_ally_feats_size()),
                np.prod(self.get_obs_own_feats_size()),
            ]
        )
        self.observation_space_low = [0] * self.agent_obs_dim
        self.observation_space_high = [1] * self.agent_obs_dim
        self.observation_space = gym.spaces.Box(
            low=np.array(self.observation_space_low),
            high=np.array(self.observation_space_high),
        )
        self.centralized = centralized
        if centralized:
            self.observation_space = gym.spaces.Box(
                low=np.array(self.observation_space_low * self.n_agents),
                high=np.array(self.observation_space_high * self.n_agents),
            )
        self.pickleable = False

        def reset(self):
            obses = super().reset()[0]
            if not self.centralized:
                return obses
            else:
                return np.concatenate(obses)

        def step(self, actions):
            reward, terminated, info = super().step(actions)
            if not self.centralized:
                return super().get_obs(), [reward] * self.n_agents, \
                        [terminated] * self.n_agents, info 
            else:
                return np.concatenate(super().get_obs()), reward, terminated, info
