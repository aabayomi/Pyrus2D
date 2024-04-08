import atexit
from warnings import warn
from operator import attrgetter
import copy
import numpy as np
from absl import logging
from subprocess import Popen
import yaml
from optparse import OptionParser
import time
from keepaway.lib.player.world_model import WorldModel
import multiprocessing
import keepaway.utils.main_keepaway_player as kp
import atexit
from keepaway.envs.multiagentenv import MultiAgentEnv
import os
import signal
import torch

config_dir = os.getcwd() + "/config"

class KeepawayEnv(MultiAgentEnv):
    """Keepaway environment for multi-agent reinforcement learning scenarios version 0.1.0."""

    def __init__(self,**kwargs):
        """
        Initialize a keep-away environment.
        ---------------------------------
    
        Parameters obtained from kwargs:
        - num_keepers: Number of keepers in the environment.
        - num_takers: Number of takers in the environment.
        - pitch_size: Size of the pitch (field).

        """
        super().__init__()

        default_num_keepers = 3
        default_num_takers = 2
        default_pitch_size = 20  # Example default value, adjust as needed

        self.num_keepers = kwargs.get('num_keepers', default_num_keepers)
        self.num_takers = kwargs.get('num_takers', default_num_takers)
        self.pitch_size = kwargs.get('pitch_size', default_pitch_size)

        # self.sparse_reward = config["sparse_reward"]   
        self.sparse_reward  = kwargs.get('sparse_reward', default_pitch_size)
        self.actions = self.num_keepers  # 0: hold, 1: pass
        self._episode_count = 0
        self._episode_steps = 0
        self._total_steps = 0
        self.force_restarts = 0
        self.episode_limit = 10000
        self.num_agents = self.num_keepers + self.num_takers
        
        manager = multiprocessing.Manager()
        self._world = WorldModel("real",self.num_keepers ,manager)  # for all agents
        self._lock = self._world
        self._event = multiprocessing.Event()
        self._barrier = multiprocessing.Barrier(self.num_keepers)

        ### Event implementation .
        self._event_from_subprocess = multiprocessing.Event()
        self._main_process_event = (
            multiprocessing.Event()
        )  # To be set by main process to wake up all subprocesses

        self._actions = [0] * self.num_keepers
        self._shared_actions = multiprocessing.Array("i", self._actions)

        self._obs = self._world._obs
        # Use a joint value instead
        self.last_action_time = 0
        self._last_action_time = multiprocessing.Value("i", self.last_action_time)
        self._proximity_adj_mat = None

        ## reward
        self._reward = self._world._reward
        ## episode
        self._terminated = self._world._terminated
        self._episode_reward = []
        self._proximity_threshold = 2

        self.renderer = None
        self._run_flag = False



        self._keepers = [
            multiprocessing.Process(
                target=kp.main,
                args=(
                    "keepers",
                    i,
                    False,
                    self._shared_actions,
                    self._barrier,
                    self._lock,
                    self._event,
                    self._event_from_subprocess,
                    self._main_process_event,
                    self._world,
                    self._obs,
                    self._last_action_time,
                    self._reward,
                    self._terminated,
                    self._proximity_adj_mat,
                    self._proximity_threshold,
                ),
                name="keeper",
            )
            for i in range(self.num_keepers)
        ]

        self._takers = [
            multiprocessing.Process(
                target=kp.main,
                args=(
                    "takers",
                    i,
                    False,
                    self._shared_actions,
                    self._barrier,
                    self._lock,
                    self._event,
                    self._event_from_subprocess,
                    self._main_process_event,
                    self._world,
                    self._obs,
                    self._last_action_time,
                    self._reward,
                    self._terminated,
                    self._proximity_adj_mat,
                    self._proximity_threshold,
                ),
                name="takers",
            )
            for i in range(self.num_takers)
        ]

        ## uncomment to include some coaching
        # self._coach = [multiprocessing.Process(target=main_c.main)]
        # coach = mp.Process(target=main_c.main)
        # coach.start()

        self._server = []
        self._render = []
        self._sleep = time
    
       

    def _is_game_started(self):
        """Check if the game has started."""
        if self._world.game_mode().type() == "play_on":
            return True
        return False
    

    def _agents(self):
        """ Utility to return all agents in the environment. """
        return self._keepers + self._takers


    def _launch_monitor(self) -> int:
        """Launches the monitor."""
        logging.debug("Built the command to connect to the server")
        monitor_cmd = f"soccerwindow2 &"
        # monitor_cmd = f"rcssmonitor --server-port={6000}"
        popen = Popen(monitor_cmd, shell=True)
        return popen
    
    def load_agent_config(self,file_path):
        with open(file_path) as f:
            return yaml.safe_load(f)

    def _parse_options(self, args=None, **defaults):
        """
        Parses the given list of args, defaulting to sys.argv[1:].
        Retrieve other options from the YAML config file.
        """

        # Load the default values from YAML file
        with open(f"{config_dir}/server-config.yml", "r") as ymlfile:
            config = yaml.safe_load(ymlfile)

        class ConfigOptions:
            pass

        options = ConfigOptions()
        # options, _ = parser.parse_args(args)
        # Merging command-line options with YAML defaults
        for key, value in config.items():
            if not getattr(options, key, None):
                setattr(options, key, value)
        return options

    def _launch_server(self, options):
        """Launch the RCSS Server and Monitor"""

        log_name = f"{time.strftime('%Y%m%d%H%M%S')}"

        server_options = [
            f"server::{opt}={val}"
            for opt, val in {
                "coach": int(options.coach),
                "coach_port": int(options.coach_port),
                "forbid_kick_off_offside": 1,
                "half_time": -1,
                "keepaway": int(not options.coach),
                "keepaway_start": options.game_start,
                "keepaway_length": int(options.field_length),
                "keepaway_width": int(options.field_width),
                "keepaway_logging": 1 if options.log_keepaway else 0,
                "keepaway_log_dir": options.log_dir if options.log_keepaway else None,
                "keepaway_log_fixed": 1 if options.log_keepaway else 0,
                "keepaway_log_fixed_name": log_name if options.log_keepaway else None,
                "game_log_compression": 0,
                "game_log_dir": options.game_log_dir if options.log_game else None,
                "game_log_fixed": 1 if options.log_game else 0,
                "game_log_fixed_name": log_name if options.log_game else None,
                "game_log_version": 5 if options.log_game else 0,
                "game_logging": 1,
                "olcoach_port": options.online_coach_port,
                "port": options.port,
                "stamina_inc_max": 3500,
                "fullstate_l": int(options.fullstate),
                "fullstate_r": int(options.fullstate),
                "synch_mode": int(options.synch_mode),
                "synch_offset": 60,
                "synch_see_offset": 0,
                "text_log_compression": 0,
                "text_log_dir": options.game_log_dir if options.log_text else None,
                "text_log_fixed": 1 if options.log_text else 0,
                "text_log_fixed_name": log_name if options.log_text else None,
                "text_logging": 1,
                "use_offside": 0,
                "visible_angle": 360 if not options.restricted_vision else None,
            }.items()
            if val is not None
        ]

        # Build rcssserver command, and fork it off.
        # print(server_options)
        command = ["rcssserver"] + server_options
        popen = Popen(command)

        return popen

    def _launch_game(self):
        """Launch a keepaway game instance."""
        # print("launching game")
        options = self._parse_options()
        # print(options.)
        # args, other_args = parser.parse_known_args()
        self._server.append(self._launch_server(options))

    def reset(self,):
        
        """Reset the environment. Required after each full episode."""

        # print("resetting")
        self._episode_steps = 0
        self._total_steps = 0
        self.last_action = None
        self._episode_reward = []
        self.info = {}
        if self._world._terminated.get_lock():
            self._world._terminated.value = False
        
        return self._obs ,

    def reward(self):
        """
        returns the reward for the current state
        """
        r = self._world.time().cycle() - self._terminal_time.cycle()
        return r
        
    def _check_agents(self):
        """Check if all agents process are running."""
        for p in self._keepers:
            if not p.is_alive():
                return False
        for p in self._takers:
            if not p.is_alive():
                return False
        return True



    def _restart(self):
        self.full_restart()

    def full_restart(self):
        """Restart the environment. Required after each full episode."""
        # TODO process management utility
        self._launch_game()
        self.force_restarts += 1

    def start(self):
        if self._episode_count == 0:
            for i in range(self.num_keepers):
                self._keepers[i].start()

            self._sleep.sleep(0.5)

            for i in range(self.num_takers):
                self._takers[i].start()

            self._sleep.sleep(2.0)
            # print("starting coach")
            # self._coach[0].start()

            atexit.register(self.close)
            self._episode_count += 1
        else:
            pass
            # print("already started")

    def close(self):
        """Close the environment. No other method calls possible afterwards."""
    
        for p in self._keepers:
            p.terminate()

        for s in self._server:
            s.terminate()
        
        for t in self._takers:
            t.terminate()

    
        for r in self._render:
            r.terminate()
            self.renderer = None
        # self._coach[0].terminate()
    
    def render(self, mode= "human"):
        """Render the environment using the monitor."""
        self._render.append(self._launch_monitor())
        self.renderer = mode
    
    
        
    def get_avail_agent_actions(self, agent_id):
        """Returns the available actions for agent_id."""
        l = [3] * self.num_keepers
        # return self._shared_values[agent_id]
        return l

    def get_avail_actions(self):
        """Returns the available actions for agent_id."""
        l = [None] * self.num_keepers
        # return self._shared_values[agent_id]
        for i in range(self.num_keepers):
            l[i] = self.get_avail_agent_actions(i)
        # print("l ", l)
        return l
    
    def get_total_actions(self):
        pass
    
    def get_obs(self):
        # obs = np.frombuffer(self._obs, dtype=np.float64)
        # print("obs ", self._obs) .
        return self._obs
    
    def get_obs_agent(self, agent_id):
        """Returns the observation for agent_id."""
        return self._obs[agent_id]
    
    def get_total_actions(self):
        """Returns the total number of actions an agent could ever take."""
        return self.actions
    
    def get_obs_size(self):
        """Returns the shape of the observation."""
        # print("length ", len(self._obs.values()[0]))
        return len(self._obs.values()[0])
    def get_state_size(self):
        """ Returns the shape of the state. """
        # print("obs size us ", self.get_obs_size() * self.num_agents)
        # print("numbr of keepers ", self.num_keepers)
        return self.get_obs_size() * self.num_keepers
    
    def get_proximity_adj_mat(self):
        adjacent_matrix = np.frombuffer(self._proximity_adj_mat, dtype=np.float64)
        return adjacent_matrix 
    
    def get_state(self):
        """Returns the global state."""

        ## TODO: verify state variables to be for all agents or just one
        ## check for dec execution/
        ## partial observation or state variables 
        # print("obs ," ,self.get_obs())
        obs = self.get_obs().values()
        obs = [item if isinstance(item, np.ndarray) else item['state_vars'] for item in obs]

        # for i, array in enumerate(obs, start=1):
        #     print(f"Length of array {i}: {array.shape[0]}")

        # print("obs ", obs, "len ", len(obs))
        obs_concat = np.concatenate(obs , axis=0)
        # print("obs_concat ", obs_concat, "len ", len(obs_concat))
        return obs_concat

    def step(self, actions):
        """A single environment step. Returns reward, terminated, info.

        Args:
            actions: list of actions for each agent

        Returns:
            Tuple of time-step data for each agent


        applies all actions to the
        send an action signal and return observation.
        """
        if isinstance(actions, torch.Tensor):
            actions = actions.cpu().tolist()

        if not actions:
            self.agents = []
            return {}, {}, {}, {}, {}

        actions_int = actions
        self._total_steps += 1
        self._episode_steps += 1
        total_reward = 0
        info = {}
        terminated = False
        self._actions = copy.deepcopy(actions_int)
        self._shared_values = multiprocessing.Array("i", self._actions)
        self._observation = self._world._obs
        game_state = self._world._terminated.value
        if game_state == 1:
            terminated = True
            if not self.sparse_reward:
                total_reward = self._reward.value
                pass
            else:
                total_reward = self._reward.value

            self._terminal_time = self._world.time()
        if terminated:
            self._episode_count += 1

            ## check if all agents are running
            # if not self._check_agents():
            #     print("restarting")
            #     # self.close()
            #     self._restart()
            #     self.start()
        return total_reward, terminated, info
