""" 
Implementation for random policy for keepaway.

Random policy keepaway.baseline adapted from Adaptive Behavior '05 article
* Stone, Sutton, and Kuhlmann.

"""

import random


class RandomPolicy:
    def __init__(self, config=None):
        """Initializes the policy."""
        if config is not None:
            self.num_keepers = config["num_keepers"]
            self.num_takers = config["num_takers"]

    def get_actions(self, obs):
        """
        Returns a random action for each agent.
        """
        agents_ids = obs.keys()
        actions = []
        for idx in agents_ids:
            a = random.randint(0, self.num_keepers)
            if a != idx:
                actions.append(a)
            else:
                l = [num for num in range(0, self.num_keepers + 1) if num != idx]
                actions.append(random.choice(l))
        return actions, {}
