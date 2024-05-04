"""
Sample wrapper for the Keep-away environment. 
This wrapper is used to make the environment compatible with the OpenAI Gym API.

"""



import akro
import gym
import numpy as np
from gym import spaces
from gymnasium.utils import EzPickle
from gymnasium.utils import seeding
from keepaway.envs.keepaway_env import KeepawayEnv
from keepaway.config.game_config import get_config

class KeepawayWrapper(KeepawayEnv):
    
    def __init__(self,centralized,config, *args, **kwargs):
        super().__init__(config,*args, **kwargs)
        
        self.reward_range = (-np.inf, np.inf)
        self.viewer = None
        self.action_space = gym.spaces.Discrete(self.actions)
        
        observation_size = self.obs_size()

        self._obs_low = np.array([-1] * observation_size)
        self._obs_high = np.array([1] * observation_size)

    
        self.observation_space = gym.spaces.Box(
            low=np.array(self._obs_low * self.num_agents),
            high=np.array(self._obs_high * self.num_agents),
        )
        
    
        self.pickleable = False

        self.state_size = observation_size
        self.state_space = spaces.Box(
            low=-1, high=1, shape=(self.state_size,), dtype="float32"
        )
        # self._reward = super().reward()

        self.episode_limit = 100000
        self.metric_name = "EvalAverageReturn"
        self.run_flag = False

    def obs_size(self):
        state = super().get_obs_size()
        return state
    
    def render(self, mode="human"):
        super().render()

    def close(self):
        super().close()

    def launch_game(self):
        launch = super().launch_game()
        return launch
    
    def reset(self):
        import copy
        obses = copy.deepcopy(super().reset())
        return obses

    def step(self, actions):

        reward, terminated, info = super().step(actions)
        return super().get_obs(),super().get_reward().value, terminated, info
        
    def __del__(self):
        super().close()

