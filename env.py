# from __future__ import absolute_import
# from __future__ import division
# from __future__ import print_function


# from keepaway.env.multiagentenv import MultiAgentEnv


import atexit
from warnings import warn
from operator import attrgetter
from copy import deepcopy
import numpy as np
import enum
import math
from absl import logging
from subprocess import Popen
import yaml
from optparse import OptionParser
import yaml
import sys
import time

import team_config
from lib.player.basic_client import BasicClient
from lib.player.world_model import WorldModel
import multiprocessing
import base.main_keepaway_player as kp
import atexit


# from lib.player import WorldModel


# class KeepawayEnv(MultiAgentEnv):
class KeepawayEnv:
    """Keepaway environment for multi-agent reinforcement learning scenarios version 0.1.0."""

    def __init__(self, pitch_size=20, sparse_reward=False):
        """
        Initialize a keepaway environment.
        ----------------------------------------------------------------
        Parameters:

        """

        self.num_keepers = 3
        self.num_takers = 2

        self.pitch_size = pitch_size
        self.sparse_reward = sparse_reward

        self.actions = 2  # 0: hold, 1: pass

        self._episode_count = 0
        self._episode_steps = 0
        self._total_steps = 0
        self._obs = None
        self.force_restarts = 0
        # self.last_action = np.zeros((self.num_keepers, self.n_actions))

        self._world = WorldModel("real")  # for all agents
        self._world.observations = {agent: None for agent in range(self.num_keepers)}
        self._client: BasicClient = BasicClient()

        self._lock = self._world
        self._event = multiprocessing.Event()
        self._barrier = multiprocessing.Barrier(3)

        ### Event implementation
        # self._event =
        self._event_from_subprocess = multiprocessing.Event()
        self._main_process_event = (
            multiprocessing.Event()
        )  # To be set by main process to wake up all subprocesses

        # self._obs = self._world._obs
        # self._state = self._world._state
        self._actions = [0] * 4
        # self._time_list = [0,0,0,0]
        # Create a shared list to hold the count for each process
        self._shared_values = multiprocessing.Array("i", self._actions)

        manager = multiprocessing.Manager()
        # self._shared_values = manager.list([0, 0, 0, 0])
        self._keepers = [
            multiprocessing.Process(
                target=kp.main,
                args=(
                    "keepers",
                    i,
                    False,
                    self._shared_values,
                    self._barrier,
                    self._lock,
                    self._event,
                    self._event_from_subprocess,
                    self._main_process_event,
                    self._world,
                ),
                name="keeper",
            )
            for i in range(self.num_keepers)
        ]

        # self._takers = [
        #     multiprocessing.Process(
        #         target=kp.main,
        #         args=(
        #             "takers",
        #             i,
        #             False,
        #             self._shared_values,
        #             self._barrier,
        #             self._lock,
        #             self._event,
        #             self._event_from_subprocess,
        #             self._main_process_event,
        #             self._world,
        #         ),
        #         name="takers",
        #     )
        #     for i in range(self.num_takers)
        # ]

        self._render = []
        self._sleep = time

        # Try to avoid leaking SC2 processes on shutdown : fix this manage ..
        # atexit.register(lambda: self.close())

    def _launch_monitor(self) -> int:
        """Launches the monitor."""
        logging.debug("Built the command to connect to the server")

        monitor_cmd = f"soccerwindow2 &"
        # monitor_cmd = f"rcssmonitor --server-port={options.port}"
        popen = Popen(monitor_cmd, shell=True)
        return popen

    def _parse_options(self, args=None, **defaults):
        """
        Parses the given list of args, defaulting to sys.argv[1:].
        Retrieve other options from the YAML config file.
        """

        # Load the default values from YAML file
        with open("config.yml", "r") as ymlfile:
            config = yaml.safe_load(ymlfile)

        parser = OptionParser()
        options, _ = parser.parse_args(args)
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
                "game_log_compression": 1,
                "game_log_dir": options.log_dir if options.log_game else None,
                "game_log_fixed": 1 if options.log_game else 0,
                "game_log_fixed_name": log_name if options.log_game else None,
                "game_log_version": 5 if options.log_game else 0,
                "game_logging": 0,
                "olcoach_port": options.online_coach_port,
                "port": options.port,
                "stamina_inc_max": 3500,
                "fullstate_l": int(options.fullstate),
                "fullstate_r": int(options.fullstate),
                "synch_mode": int(options.synch_mode),
                "synch_offset": 60,
                "synch_see_offset": 0,
                "text_log_compression": 1 if options.log_text else 0,
                "text_log_dir": options.log_dir if options.log_text else None,
                "text_log_fixed": 1 if options.log_text else 0,
                "text_log_fixed_name": log_name if options.log_text else None,
                "text_logging": 0,
                "use_offside": 0,
                "visible_angle": 360 if not options.restricted_vision else None,
            }.items()
            if val is not None
        ]

        # Build rcssserver command, and fork it off.
        print(server_options)
        command = ["rcssserver"] + server_options
        popen = Popen(command)

        return popen

    def _launch_game(self):
        """Launch a keepaway game instance."""
        options = self._parse_options()
        self._render.append(self._launch_server(options))
        self._render.append(self._launch_monitor())

    def reset(self):
        """Reset the environment. Required after each full episode."""
        self._episode_steps = 0

        self.last_action = np.zeros((self.n_agents, self.n_actions))

        return self.get_obs(), self.get_state()

    def reward(self):
        """
        returns the reward for the current state
        """
        reward = self.time().cycle() - self._last_decision_time().cycle()

        return reward

    def _restart(self):
        self.full_restart()

    def full_restart(self):
        """Restart the environment. Required after each full episode."""
        # TODO process management utility

        self._launch_game()
        self.force_restarts += 1

    def start(self):
        print("starting")
        for i in range(self.num_keepers):
            self._keepers[i].start()
        
        # self._sleep.sleep(0.5)

        # for i in range(self.num_takers):
        #    self._takers[i].start() 
        atexit.register(self.close)

    def close(self):
        """Close the environment. No other method calls possible afterwards."""
        for p in self._keepers:
            p.terminate()
        for r in self._render:
            r.terminate()
        # for t in self._takers:
        #     t.terminate()

    def get_avail_agent_actions(self, agent_id):
        """Returns the available actions for agent_id."""
        print(self._actions)

        # print("size of all players ", len(self._world._all_players))
        # print("actions ", self._world._available_actions, "at time ", self._world.time())
        return self._shared_values[agent_id]
    
    def observe(self):
        # for all agents
        state = 0
        reward = 0
        terminated = False
        info = {}
        return state, reward, terminated

    def step(self, actions):
    # -> tuple[
    #     dict[AgentID, ObsType],
    #     dict[AgentID, float],
    #     dict[AgentID, bool],
    #     dict[AgentID, bool],
    #     dict[AgentID, dict]]:
        """A single environment step. Returns reward, terminated, info.

        Args: 
            actions: list of actions for each agent
        
        Returns:
            Tuple of time-step data for each agent
        
            
        applies all actions to the
        send an action signal and return observation
        """
        rewards = {}

        # print(actions)
        ## main process waits for child process to finish
        # self._barrier.wait()
        # print("Main Process: Waking up all subprocesses!")
        # self._main_process_event.set()
        # print("Main process completed.")

       
        return self.observe()