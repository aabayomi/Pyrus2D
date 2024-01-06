from __future__ import absolute_import, division, print_function

import time
from absl import logging
logging.set_verbosity(logging.DEBUG)
from env import KeepawayEnv
from experiments.policies.handcoded_agent import HandcodedPolicy


def run(args):
    """Run the cg command."""
    def train_keepaway(args):
        """Train the model."""
        env = gym.make(args.env)
