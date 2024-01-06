from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import atexit
from warnings import warn
from operator import attrgetter
import copy
import numpy as np
import enum
import math
from absl import logging
from subprocess import Popen
import yaml
from optparse import OptionParser
import time
from lib.player.world_model import WorldModel
import multiprocessing
import base.main_keepaway_player as kp
import atexit
import base.main_coach as main_c
from envs.multiagentenv import MultiAgentEnv


class KeepawayEnv(MultiAgentEnv):
    # class KeepawayEnv:
    """Keepaway environment for multi-agent reinforcement learning scenarios version 0.1.0."""

    def __init__(self, pitch_size=20, sparse_reward=False):
        """
        Initialize a keepaway environment.
        ---------------------------------
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
        self.force_restarts = 0
        self.episode_limit = 1000
        self.timeouts = 0
        self.continuing_episode = False

        self._last_action = None
        manager = multiprocessing.Manager()
        self._world = WorldModel("real", manager)  # for all agents
        # self._world.observations = {agent: None for agent in range(self.num_keepers)}

        self._lock = self._world
        self._event = multiprocessing.Event()
        self._barrier = multiprocessing.Barrier(3)

        ### Event implementation
        self._event_from_subprocess = multiprocessing.Event()
        self._main_process_event = (
            multiprocessing.Event()
        )  # To be set by main process to wake up all subprocesses

        # self._obs = self._world._obs
        # self._state = self._world._state

        self._actions = [0] * 3
        # self._time_list = [0,0,0,0]
        # Create a shared list to hold the count for each process
        self._shared_values = multiprocessing.Array("i", self._actions)

        # self._world.observations =
        self._obs = self._world._obs
        # self._last_action_time = self._world._last_action_time
        #
        # self.last_action_time = [0] * 4
        # self._last_action_time = multiprocessing.Array("i", self.last_action_time)
        # Use a joint value instead
        self.last_action_time = 0
        self._last_action_time = multiprocessing.Value("i", self.last_action_time)

        # self._rewards = [0] * 4
        # self._reward = multiprocessing.Array("i", self._rewards)
        self._reward = self._world._reward
        # self._rewards = multiprocessing.Value("i", self._reward )

        ## episode
        # self.terminated = False
        # self._terminated = multiprocessing.Value('b', self.terminated)
        self._terminated = self._world._terminated
        # print("workd terminated ", self._world._terminated.value)

        self._episode_reward = []

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
                    self._obs,
                    self._last_action_time,
                    self._reward,
                    self._terminated,
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
                ),
                name="takers",
            )
            for i in range(self.num_takers)
        ]

        ## TODO: add coach
        # self._coach = [multiprocessing.Process(target=main_c.main)]
        # coach = mp.Process(target=main_c.main)
        # coach.start()

        self._render = []
        self._sleep = time

    def _launch_monitor(self) -> int:
        """Launches the monitor."""
        logging.debug("Built the command to connect to the server")

        monitor_cmd = f"soccerwindow2 &"
        # monitor_cmd = f"rcssmonitor --server-port={6000}"
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

        options = self._parse_options()
        self._render.append(self._launch_server(options))
        self._render.append(self._launch_monitor())

    def reset(self):
        """Reset the environment. Required after each full episode."""

        print("resetting")

        self._episode_steps = 0
        self._total_steps = 0
        self.last_action = None
        self._episode_reward = []
        # self._reward = self._world._reward
        # self._terminated =
        # self._world._terminated = multiprocessing.Value('b', False)
        if self._world._terminated.get_lock():
            self._world._terminated.value = False
        # self._world._terminated = multiprocessing.Value('b', False)
        return

    def reward(self):
        """
        returns the reward for the current state
        """
        return self._reward.value

    def _restart(self):
        self.full_restart()

    def full_restart(self):
        """Restart the environment. Required after each full episode."""
        # TODO process management utility

        self._launch_game()
        self.force_restarts += 1

    def start(self):
        print("starting")
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
            print("already started")

    def close(self):
        """Close the environment. No other method calls possible afterwards."""

        for p in self._keepers:
            p.terminate()
        for r in self._render:
            r.terminate()
        for t in self._takers:
            t.terminate()

        # self._coach[0].terminate()

    def get_avail_agent_actions(self, agent_id):
        """Returns the available actions for agent_id."""
        return self._shared_values[agent_id]

    def get_obs(self):
        return self._obs

    def step(self, actions):
        """A single environment step. Returns reward, terminated, info.

        Args:
            actions: list of actions for each agent

        Returns:
            Tuple of time-step data for each agent


        applies all actions to the
        send an action signal and return observation.
        """

        # do i need this ..
        if not actions:
            self.agents = []
            return {}, {}, {}, {}, {}

        # actions_int = [int(a) for a in actions]
        actions_int = actions
        self._total_steps += 1
        self._episode_steps += 1
        total_reward = 0
        ## not needed just for keepsake.
        info = {}
        terminated = False

        # passes the actions from the main process to the subprocesses.
        # this should update the shared values.

        self._actions = copy.deepcopy(actions_int)

        # print("actions ", self._actions)
        self._shared_values = multiprocessing.Array("i", self._actions)

        self._observation = self._world._obs
        game_state = self._world._terminated.value
        if game_state == 1:
            terminated = True
            ## check details for sparse ( sparse implementation will take into account the
            ## number of successful passes)
            if not self.sparse_reward:
                # total_reward += self.reward()
                total_reward = self._reward.value
                pass
            else:
                ## not implemented yet
                total_reward = self._reward.value

        # elif self._episode_steps >= self.episode_limit:
        #     terminated = True
        #     total_reward += self.reward()
        #     if self.continuing_episode:
        #         info["episode_limit"] = True
        #     self.timeouts += 1

        if terminated:
            self._episode_count += 1

        # print("world terminated ", self._world._terminated.value)
        return total_reward, terminated, info
