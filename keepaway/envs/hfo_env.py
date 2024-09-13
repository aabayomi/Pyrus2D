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
        super(HFOEnv, self).__init__(config)
        self.config = config
        self.hfo = None
        self.process = None
        self.team_name = config.get('team_name', 'BASE')
        self.num_agents = config.get('num_agents', 1)
        self.defense_agents = config.get('defense_agents', [])
        self.offense_agents = config.get('offense_agents', [])
        self.defense_npcs = config.get('defense_npcs', [])
        self.offense_npcs = config.get('offense_npcs', [])
        