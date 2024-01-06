
from __future__ import absolute_import, division, print_function

import time
from os import replace
import numpy as np
import random
from absl import logging
logging.set_verbosity(logging.DEBUG)
from env import KeepawayEnv

def test():
    agents = 3
    observations = {agent: None for agent in range(2, agents + 2)}
    print(observations)


def test_player_logic():
    env = KeepawayEnv()
    episodes = 1
    print("Training episodes")
    # env.reset()
    print("launching game")
    env.start()