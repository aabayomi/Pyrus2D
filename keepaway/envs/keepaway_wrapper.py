"""
Example Keepaway Wrapper useful for environment
customization.  

"""

from keepaway.envs.keepaway_env import KeepawayEnv
from gymnasium.utils import EzPickle
from gymnasium.utils import seeding
# from gymnasium import spaces
import akro
import gym
from gym import spaces
from keepaway.config.game_config import get_config
# from pettingzoo.utils.env import ParallelEnv
# from pettingzoo.utils.conversions import (
#     parallel_to_aec as from_parallel_wrapper,
# )
# from pettingzoo.utils import wrappers
import numpy as np

from keepaway.envs.spaces import MultiAgentActionSpace, MultiAgentObservationSpace


# def parallel_env(max_cycles=None, **ka_args):
#     if max_cycles is None:
#         map_name = ka_args.get("map_name", "3v2")
#         # print(map_name)
#         # print(get_config())
#         max_cycles = get_config()[map_name]["limit"]
#         print(max_cycles)
#     return _parallel_env(max_cycles, **ka_args)

# def raw_env(max_cycles=None, **ka_args):
#     return from_parallel_wrapper(parallel_env(max_cycles, **ka_args))

# def make_env(raw_env):
#     def env_fn(**kwargs):
#         env = raw_env(**kwargs)
#         env = wrappers.AssertOutOfBoundsWrapper(env)
#         env = wrappers.OrderEnforcingWrapper(env)
#         return env

#     return env_fn

# class keepaway_env(ParallelEnv):
from keepaway.envs.multiagentenv import MultiAgentEnv

class keepaway_env(KeepawayEnv):

    def __init__(self, env):
        super().__init__()
        self.cycles = 1000
        self.env = env
        self.env.reset()
        self.reset_flag = 0
        ## TODO: Check if this is the right way to do it
        self.agents, self.action_spaces = self._init_agents()
        self.num_agents = len(self.agents)
        
        

        self.action_spaces = MultiAgentActionSpace(self.action_spaces)
        self.action_space = self.action_spaces[0]
        # print("action space ", self.action_spaces)

        observation_size = env.get_obs_size()
        self._obs_low = np.array([-1] * observation_size)
        self._obs_high = np.array([1] * observation_size)

        # print("num agents ", self.num_agents)
        self.ob = MultiAgentObservationSpace([akro.Box(self._obs_low, self._obs_high) for _ in range(3)])
        # self.observation_space = self.ob[0]

        self._obs_low = np.array([-1] * observation_size)
        self._obs_high = np.array([1] * observation_size)
    
        self.observation_space = gym.spaces.Box(self._obs_low, self._obs_high)
        self.observation_space = akro.Box(
                low=np.array(list(self.observation_space.low) * 3),
                high=np.array(list(self.observation_space.high) * 3)
            )


        # print("observation space ", self.observation_space)

        # print("agents ", self.agents)
        self.possible_agents = self.agents[:]
        observation_size = env.get_obs_size()
        # print("obs size ", observation_size)

         ##should be abstracted into a wrapper 
        self.alive_mask = np.array([True] * self.num_agents)
        self.threshold = 2
        self.self_connected_adj = False
        self.inv_D = False
        self.pickleable = True
        

        # self.observation_spaces = {
        #     name: akro.Dict(
        #         {
        #             "observation": akro.Box(
        #                 low=-1,
        #                 high=1,
        #                 shape=(observation_size,),
        #                 dtype="float32",
        #             ),
        #             "action_mask": akro.Box(
        #                 low=0,
        #                 high=1,
        #                 shape=(self.action_spaces[name].n,),
        #                 dtype=np.int8,
        #             ),
        #         }
        #     )
        #     for name in self.agents
        # }
        

        # self.observation_s = self.obs()
        # print("observation space ", MultiAgentObservationSpace([spaces.Box(self._obs_low, self._obs_high) for _ in range(self.num_agents)]))

        state_size = env.get_state_size()
        # print("state size ", state_size)
        self.state_space = spaces.Box(low=-1, high=1, shape=(state_size,), dtype="float32")
        self._reward = 0
        self.episode_limit = 100000
        self.metric_name = 'EvalAverageReturn'
        self.run_flag = False
        self.centralized = True
    

    def obs(self):
       o = [spaces.Box(self._obs_low, self._obs_high) for _ in range(self.num_agents)]
       p = MultiAgentObservationSpace(o)
       return o

    def observation_space(self, agent):
        # print("agent ", self.observation_spaces)
        return self.observation_spaces[agent]
    
    def obs_space(self, agent):
        # return self.observation_spaces["keeper_1"]["observation"]
        return self.observation_spaces[agent]

    def act_space(self, agent):
        # return self.action_spaces["keeper_1"]
        return self.action_spaces[agent]
    
    def action_space(self, agent):
        return self.action_spaces[agent]
    
    
    def _init_agents(self):
        agents = []
        action_spaces = []
        self.agents_id = {}
        keeper_count = 1
        taker_count = 1

        for agent_id in range(self.env.num_keepers):
            # Define action space using gym's Discrete space
            unit_action_space = akro.Discrete(3)
            action_spaces.append(unit_action_space)
            agents.append(agent_id + 1)
            # if self.env._agents()[agent_id].name == "keeper":
            #     agent_type = "keeper"
            #     agents.append(f"{agent_type}_{keeper_count}")
            #     self.agents_id[agents[-1]] = keeper_count
            #     action_spaces[agents[-1]] = unit_action_space
            #     keeper_count += 1
            # else:
            #     agent_type = "taker"
            #     agents.append(f"{agent_type}_{taker_count}")
            #     self.agents_id[agents[-1]] = taker_count
            #     action_spaces[agents[-1]] = unit_action_space
            #     taker_count += 1

        # print("agents id ", self.agents_id)

        # for agent_name, action_space in action_spaces.items():
        #     print("action space ", type(action_space))
        #     print("agent name ", agent_name)
        #     assert isinstance(action_space, gym.spaces.Space), \
        #         f"The action space for {agent_name} is not a valid gym Space instance."

        return agents, action_spaces
        # return agents, action_spaces
    
    
    # def _init_agents(self):
    #     last_type = ""
    #     agents = []
    #     action_spaces = {}
    #     self.agents_id = {}
    #     keeper_count = 1
    #     taker_count = 1
      

    #     for agent_id in range(len(self.env._agents())):
    #         unit_action_space = akro.Discrete(
    #             self.env.get_total_actions()
    #         )  # no-op in dead units is not an action
            
    #         # unit_action_space = spaces.Discrete(
    #         #     self.env.get_total_actions()
    #         # )  # no-op in dead units is not an action

    #         if self.env._agents()[agent_id].name == "keeper":
    #             agent_type = "keeper"
    #             agents.append(f"{agent_type}_{keeper_count}")
    #             self.agents_id[agents[-1]] = keeper_count
    #             action_spaces[agents[-1]] = unit_action_space
    #             keeper_count += 1
    #         else:
    #             agent_type = "taker"
    #             agents.append(f"{agent_type}_{taker_count}")
    #             self.agents_id[agents[-1]] = taker_count
    #             action_spaces[agents[-1]] = unit_action_space
    #             taker_count += 1

    #         # if agent_type == last_type:
    #         #     i += 1
    #         # else:
    #         #     i = 0

    #         # agents.append(f"{agent_type}_{i}")
    #         # self.agents_id[agents[-1]] = agent_id + 1
    #         # action_spaces[agents[-1]] = unit_action_space
    #         last_type = agent_type
    #     print("agents id ", self.agents_id)
    #     return agents, action_spaces
    
    
    def render(self, mode="human"):
        self.env.render(mode)

    def close(self):
        self.env.close()

    def launch_game(self):
        return super()._launch_game()


    def reset(self, seed=None, options=None):
        self.env._episode_count = 1
        # self.env.reset()
        # self.agents = self.possible_agents[:]
        # self.frames = 0
        # self.terminations = {agent: False for agent in self.possible_agents}
        # self.truncations = {agent: False for agent in self.possible_agents}
        return self.env.reset()
        # return self._observe_all()

    def get_avail_actions(self):
        """Returns the available actions for agent_id."""
        avail_actions = [[1] * self.action_space.n for _ in range(self.num_keepers)]
        if not self.centralized:
            return avail_actions
        else:
            return np.concatenate(avail_actions)
    

    
    def get_agent_id(self, agent):
        return self.agents_id[agent]
    
    
    def _all_rewards(self, reward):
        all_rewards = [reward] * len(self.agents)
        return {
            agent: reward for agent, reward in zip(self.agents, all_rewards)
        }
    
    def _observe_all(self):
        all_obs = []
        for agent in self.agents:
            agent_id = self.get_agent_id(agent)
            obs = self.env.get_obs_agent(agent_id)
            action_mask = self.env.get_avail_agent_actions(agent_id)
            print("action mask ", action_mask)
            action_mask = action_mask[1:]
            action_mask = np.array(action_mask).astype(np.int8)
            obs = np.asarray(obs, dtype=np.float32)
            all_obs.append({"observation": obs, "action_mask": action_mask})
        return {agent: obs for agent, obs in zip(self.agents, all_obs)}
    
    def step(self, actions):
        r,t,info = super().step(actions)
        # r,t,info = self.env._step(actions)
        # print("rewards ", r, "term ", t, "info ", info)
        return r,t,info

    
    def _all_terms_truncs(self, terminated=False, truncated=False):
        terminations = [True] * len(self.agents)

        if not terminated:
            for i, agent in enumerate(self.agents):
                agent_done = False
                agent_id = self.get_agent_id(agent)
                # agent_info = self.env.get_unit_by_id(agent_id)
                agent_info = {}
                # if agent_info.health == 0:
                #     agent_done = True
                terminations[i] = agent_done

        terminations = {a: bool(t) for a, t in zip(self.agents, terminations)}
        truncations = {a: truncated for a in self.agents}

        return terminations, truncations
    
    # def step(self, all_actions):
    #     action_list = [0] * self.env.n_agents
    #     for agent in self.agents:
    #         agent_id = self.get_agent_id(agent)
    #         if agent in all_actions:
    #             if all_actions[agent] is None:
    #                 action_list[agent_id] = 0
    #             else:
    #                 action_list[agent_id] = all_actions[agent] + 1
    #     self._reward, terminated, info = self.env.step(action_list)
    #     self.frames += 1
    #     all_infos = {agent: {} for agent in self.agents}
    #     # all_infos.update(smac_info)
    #     all_terms, all_truncs = self._all_terms_truncs(
    #         terminated=terminated, truncated=(self.frames >= self.max_cycles)
    #     )
    #     all_rewards = self._all_rewards(self._reward)
    #     all_observes = self._observe_all()

    #     self.agents = [agent for agent in self.agents if not all_terms[agent]]
    #     self.agents = [agent for agent in self.agents if not all_truncs[agent]]

    #     return all_observes, all_rewards, all_terms, all_truncs, all_infos
    
    def state(self):
        return self.env.get_state()
    
    # def __del__(self):
    #     self.env.close()
    


# env = make_env(raw_env)


# class _parallel_env(keepaway_env, EzPickle):
#     metadata = {"render.modes": ["human"], "name": "sc2"}

#     def __init__(self, max_cycles, **ka_args):
#         EzPickle.__init__(self, max_cycles, **ka_args)
#         env = KeepawayEnv(**ka_args)
#         super().__init__(env, max_cycles)


