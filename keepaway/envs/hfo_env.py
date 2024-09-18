import atexit
from warnings import warn
from operator import attrgetter
import copy
import numpy as np
from absl import logging
from subprocess import Popen
import yaml
import time
from keepaway.lib.player.world_model import WorldModel
import multiprocessing
import keepaway.utils.main_keepaway_player as kp
import atexit
from keepaway.envs.multiagentenv import MultiAgentEnv
import os

config_dir = os.getcwd() + "/config"

class HFOEnv(MultiAgentEnv):
    """ Half Field Offense Environment for multi-agent reinforcement learning scenarios version 0.1.0.
        Python portable version of the HFO environment.
    """
    def __init__(self, config):
        self.config = config
        self.defense_agents = config["defense_agents"]
        self.offense_agents = config["offense_agents"]
        self.defense_npcs = config["defense_npcs"]
        self.offense_npcs = config["offense_npcs"]

        self.actions  = 2
        self._episode_count = 0
        self._episode_steps = 0
        self._total_steps = 0
        self.force_restarts = 0
        self.episode_limit = 1000
        self.timeouts = 0
        self.continuing_episode = False
        self.num_agents = self.defense_agents + self.offense_agents + self.defense_npcs + self.offense_npcs

        self._last_action = None
        manager = multiprocessing.Manager()
        self._world = WorldModel("real", self.offense_agents, manager)  # for all agents

        self._lock = self._world
        self._event = multiprocessing.Event()
        self._barrier = multiprocessing.Barrier(self.offense_agents)

        ## Event implementation
        self._event_from_subprocess = multiprocessing.Event()
        self._main_process_event = (
            multiprocessing.Event()
        )  

        self._actions = [0] * 2
        self._shared_values = multiprocessing.Array("i", self._actions)

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

        self._terminal_time = None

        self.renderer = None

        self._keepers = [
            multiprocessing.Process(
                target=kp.main,
                args=(
                    "offense",
                    i,
                    False,
                    self._shared_values,
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
                name="offense",
            )
            for i in range(self.offense_agents)
        ]

        self._takers = [
            multiprocessing.Process(
                target=kp.main,
                args=(
                    "defense",
                    i,
                    False,
                    self._shared_values,
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
                name="defense",
            )
            for i in range(self.defense_agents)
        ]

        self._server = []
        self._render = []
        self._sleep = time

    def _launch_monitor(self) -> int:
        """Launches the monitor."""
        
        logging.debug("Built the command to connect to the server")
        monitor_cmd = f"soccerwindow2 &"
        popen = Popen(monitor_cmd, shell=True)
        return popen
    
    def load_agent_config(self, file_path):
        with open(file_path) as f:
            return yaml.safe_load(f)

    def _parse_options(self) -> object:
        """
        Parses the given list of args, defaulting to sys.argv[1:].
        Retrieve other options from the YAML config file.
        """

        with open(f"{config_dir}/server-config-hfo.yml", "r") as yml:
            config = yaml.safe_load(yml)

        class ConfigOptions:
            pass

        options = ConfigOptions()
        for key, value in config.items():
            if not getattr(options, key, None):
                setattr(options, key, value)
        return options
    
    def _launch_server(self, options) -> int:
        """Launch the RCSS Server and Monitor"""

        # options.field_length = self.pitch_size
        # options.field_width = self.pitch_size

        log_name = f"{time.strftime('%Y%m%d%H%M%S')}"

        server_options = [
            f"server::{opt}={val}"
            for opt, val in {
                "coach": int(options.coach),
                "coach_port": int(options.coach_port),
                "forbid_kick_off_offside": 1,
                "half_time": -1,

                # "keepaway": int(not options.coach),
                # "keepaway_start": options.game_start,
                # "keepaway_length": int(options.field_length),
                # "keepaway_width": int(options.field_width),
                # "keepaway_logging": 1 if options.log_keepaway else 0,
                # "keepaway_log_dir": options.log_dir if options.log_keepaway else None,
                # "keepaway_log_fixed": 1 if options.log_keepaway else 0,
                # "keepaway_log_fixed_name": log_name if options.log_keepaway else None,

                "hfo_logging": 1 if options.log_hfo else 0,
                "server::hfo_log_dir": options.log_dir if options.log_hfo else None,
                "hfo": 1 if options.hfo else 0,
                "coach_w_referee": 1 if options.coach_w_referee else 0,
                "hfo_max_trial_time": options.hfo_max_trial_time,
                "hfo_max_trials": options.hfo_max_trials,
                "hfo_max_frames": options.hfo_max_frames, 
                'hfo_offense_on_ball': options.hfo_offense_on_ball,
                # "server::random_seed=%i ' \
                "hfo_max_untouched_time": options.hfo_max_untouched_time,
                "hfo_min_ball_pos_x": options.hfo_min_ball_pos_x,
                "hfo_max_ball_pos_x": options.hfo_max_ball_pos_x,
                "hfo_min_ball_pos_y": options.hfo_min_ball_pos_y,
                "hfo_max_ball_pos_y": options.hfo_max_ball_pos_y,
                "say_msg_size": 1000,
                "record_messages": 1,

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
        ##
        command = ["rcssserver"] + server_options
        popen = Popen(command)

        return popen
    
    def launch_game(self)-> None:
        """Launch a keepaway game instance."""
        options = self._parse_options()
        self._server.append(self._launch_server(options))

    def reset(
        self,
    )-> tuple:
        
        """Reset the environment. Required after each full episode."""

        self._episode_steps = 0
        self._total_steps = 0
        self.last_action = None
        self._episode_reward = []
        self.info = {}
        if self._world._terminated.get_lock():
            self._world._terminated.value = False

        return (self._obs)
    
    def reward(self):
        """returns the reward for the current state"""
        r = self._world.time().cycle() - self._terminal_time.cycle()
        return r
    
    def _restart(self) -> None:
        self.full_restart()

    def full_restart(self) -> None:
        """Restart the environment. Required after each full episode."""

        self.close()
        self.start()
        self.force_restarts += 1

    
    def start(self) -> None:
        """Start the players. Required before any other method calls."""

        if self._episode_count == 0:
            for i in range(self.offense_agents):
                self._keepers[i].start()

            self._sleep.sleep(0.5)

            for i in range(self.defense_agents):
                self._takers[i].start()

            self._sleep.sleep(2.0)

            ## uncomment to include some coaching
            # self._coach[0].start()

            atexit.register(self.close)
            self._episode_count += 1
        else:
            pass

    def close(self) -> None:
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

    def render(self, mode="human") -> None:
        """Render the environment using the monitor."""
        self._render.append(self._launch_monitor())
        self.renderer = mode


    ## MultiAgentEnv methods
    def get_obs(self) -> dict:
        """Returns the observation for all agents."""
        return self._obs

    def get_reward(self) -> int:
        """Returns the rewards for all agents."""
        return self._reward

    def get_obs_agent(self, agent_id) -> dict:
        """Returns the observation for agent_id."""
        return self._obs[agent_id]

    def get_total_actions(self) -> int:
        """Returns the total number of actions an agent could ever take."""
        return self.actions

    def get_obs_size(self):
        """Returns the shape of the observation."""
        ## this should change based on the number of agents
        return 13


    
    ## Environment methods
    def step(self, actions):
        """A single environment step. Returns reward, terminated, info.

        Args:
            actions: list of actions for each agent

        Returns:
            Tuple of time-step data for each agent


        applies all actions to the
        send an action signal and return observation.
        
        """

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
                pass
                # total_reward = self._reward.value
            else:
                total_reward += copy.deepcopy(self._reward.value)

            self._terminal_time = self._world.time()
        if terminated:
            self._episode_count += 1

            ## check if processes are still running
            if not self._check_process():
                self._restart()
        return total_reward, terminated, info
