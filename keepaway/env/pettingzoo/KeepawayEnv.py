## Petting Zoo Interface for Keep-away

from keepaway.env import KeepawayEnv
from gym.utils import EzPickle
from gym.utils import seeding
from gym import spaces
from pettingzoo.utils.env import ParallelEnv
from pettingzoo.utils.conversions import from_parallel_wrapper
from pettingzoo.utils import wrappers
import numpy as np


max_cycles_default = 1000


def parallel_env(max_cycles=max_cycles_default, **keepaway_args):
    return _parallel_env(max_cycles, **keepaway_args)


def raw_env(max_cycles=max_cycles_default, **keepaway_args):
    return from_parallel_wrapper(parallel_env(max_cycles, **keepaway_args))


def make_env(raw_env):
    def env_fn(**kwargs):
        env = raw_env(**kwargs)
        # env = wrappers.AssertOutOfBoundsWrapper(env)
        # env = wrappers.OrderEnforcingWrapper(env)
        return env

    return env_fn


class keepaway_parallel_env(ParallelEnv):
    def __init__(self, env, max_cycles):
        self.max_cycles = max_cycles
        self.env = env
        self.env.reset()
        self.reset_flag = 0
        self.agents, self.action_spaces = self._init_agents()
        self.possible_agents = self.agents[:]

        observation_size = env.get_obs_size()

        # self.observation_spaces = {
        #     name: spaces.Dict(
        #         {
        #             "observation": spaces.Box(
        #                 low=-1,
        #                 high=1,
        #                 shape=(observation_size,),
        #                 dtype="float32",
        #             ),
        #             "action_mask": spaces.Box(
        #                 low=0,
        #                 high=1,
        #                 shape=(self.action_spaces[name].n,),
        #                 dtype=np.int8,
        #             ),
        #         }
        #     )
        #     for name in self.agents
        # }
        self._reward = 0

        def _init__agents(self):
            ## do include the takes as well
            agents = []
            action_spaces = {}
            self.agents_id = {}

            for agent in self.env.agent_iter():
                agents.append(agent)
                action_spaces[agent] = self.env.action_spaces[agent]
            return agents, action_spaces

        def close(self):
            self.env.close()

        ## fix logic for this.
        def reset(self):
            self.env._episode_count = 1
            self.env.reset()

            self.agents = self.possible_agents[:]
            self.all_dones = {agent: False for agent in self.possible_agents}
            return self._observe_all()

        def _rewards(self, reward):
            all_rewards = [reward] * len(self.agents)
            return {agent: reward for agent, reward in zip(self.agents, all_rewards)}

        def _observations(self):
            ## all observations for all agents.
            all_agents_obs = []
            for agent in self.agents:
                agent_id = agent.unum
                obs = self.env.get_obs_agent(agent_id)
                # no action mask implemented yet is it needed ?
                actions = self.env.get_avail_agent_actions(agent_id)
                all_agents_obs.append({"observation": obs, "actions": actions})

            return {agent: obs for agent, obs in zip(self.agents, all_agents_obs)}

        def _dones(self, step_done=False):
            ## done for all agents.
            # this should be true for all agents
            dones = [True] * len(self.agents)
            if not step_done:
                for i, agent in enumerate(self.agents):
                    agent_done = False
                    agent_id = agent.unum
                    agent_info = self.env.get_unit_by_id(agent_id)  ## could removed.
                    agent_done = agent_info["done"]
                    dones[i] = agent_done

            # return {agent: self.all_dones[agent] for agent in self.agents}
            return {agent: bool(done) for agent, done in zip(self.agents, dones)}

        def step(self, actions):
            ## step for all agents.
            action_list = [0] * self.env.n_agents
            for agent in self.agents:
                agent_id = agent.unum
                if agent in actions:
                    if actions[agent] is None:
                        action_list[agent_id] = 0
                    else:
                        action_list[agent_id] = actions[agent] + 1

            self._reward, terminated, smac_info = self.env.step(action_list)  ##

            # self.frames += 1
            # done = terminated or self.frames >= self.max_cycles
            done = terminated

            all_infos = {agent: {} for agent in self.agents}
            all_dones = self._dones(done)
            all_rewards = self._rewards(self._reward)
            all_observes = self._observations()

            self.agents = [agent for agent in self.agents if not all_dones[agent]]

            return all_observes, all_rewards, all_dones, all_infos

        def __del__(self):
            self.env.close()


env = make_env(raw_env)


class _parallel_env(keepaway_parallel_env, EzPickle):
    # metadata = {"render.modes": ["human"], "name": "sc2"}

    def __init__(self, max_cycles, **smac_args):
        EzPickle.__init__(self, max_cycles, **smac_args)
        # env = StarCraft2Env(**smac_args)
        super().__init__(env, max_cycles)
