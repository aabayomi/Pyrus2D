from __future__ import absolute_import
from __future__ import division
from __future__ import print_function


# from keepaway.env.multiagentenv import MultiAgentEnv


# from smac.env.starcraft2.maps import get_map_params
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
from time import strftime


from lib.player import WorldModel


# class KeepawayEnv(MultiAgentEnv):
class KeepawayEnv():
    """Keepaway environment for multi-agent reinforcement learning scenarios version 0.1.0."""

    def __init__(self, pitch_size=20, sparse_reward=False):
        """Initialize a keepaway environment.
        ----------------------------------------------------------------
        Parameters:

        """

        self.num_keepers = 3
        self.num_takers = 2

        self.pitch_size = pitch_size
        self.sparse_reward = sparse_reward

        self.actions = 2  # 0: hold, 1: pass

        self.keepers = []
        self.takers = []

        self._episode_count = 0
        self._episode_steps = 0
        self._total_steps = 0
        self._obs = None
        self.force_restarts = 0
        self.last_action = np.zeros((self.num_keepers, self.n_actions))
        self._world = WorldModel()  # for all agents

        # Try to avoid leaking SC2 processes on shutdown : fix this manage ..
        atexit.register(lambda: self.close())

    def _launch_monitor(self) -> None:
        """Launches the monitor."""

        monitor_cmd = f"soccerwindow2 &"
        # monitor_cmd = f"rcssmonitor --server-port={options.port}"
        Popen(monitor_cmd, shell=True)

    def _parse_options(self, args=None):
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

        log_name = f"{strftime('%Y%m%d%H%M%S')}"

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
        Popen(command)

    def _launch_game(self, options):
        """Launch a keepaway game instance."""

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
        # self._sc2_proc.close()
        self._launch(options=self._parse_options())
        self.force_restarts += 1

    def step_async(self, actions):
        """Game state Abstraction"""
        """ what are syncing ??
            1. This should only be there is action to take. 
            2. Agent class should have a step method takes and obs and return some action . 
         
        """

        import multiprocessing
        import time
        import base.main_keepaway_player as kp

        manager = multiprocessing.Manager()
        # shared_values = manager.list([0, 0, 0])
        lock = manager.Lock()
        event = multiprocessing.Event()


        world = self._world

        barrier = multiprocessing.Barrier(3)

        # Create a shared list to hold the count for each process
        shared_values = multiprocessing.Array("i", world._time)

        # Create and start three processes, passing the index of count_list each should increment
        processes = []
        for i in range(3):
            # p = multiprocessing.Process(target=count, args=(barrier, count_list, i))
            p = multiprocessing.Process(target=kp.main, args=("keepers", i, False,shared_values,barrier,lock,event), name="keeper")
            processes.append(p)
            p.start()

    def step(self, actions):
        """A single environment step. Returns reward, terminated, info."""

        actions_int = [int(a) for a in actions]
        self.last_action = np.eye(self.actions)[np.array(actions_int)]

        sc_actions = []

        for a_id, action in enumerate(actions_int):
            ## TODO: add hand coded, random utility
            sc_action = self.get_agent_action(a_id, action)

            if sc_action:
                sc_actions.append(sc_action)

            ## pass in simulator action



## test cases

def main():
    env = KeepawayEnv()
    env.step_async([0, 1, 0, 1, 0])


if __name__ == "__main__":
    main()
