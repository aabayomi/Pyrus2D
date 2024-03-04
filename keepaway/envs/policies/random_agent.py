""" 
Implementation for random policy for keepaway.

Random policy keepaway.baseline adapted from Adaptive Behavior '05 article
* Stone, Sutton, and Kuhlmann.

"""

import random


class RandomPolicy(object):
    def __init__(self):
        pass

    def get_actions(self, obs, num_keepers=None, greedy=False):
        """
        Returns a random action for each agent.
        """
        agents_ids = obs.keys()
        actions = []
        for idx in agents_ids:
            a = random.randint(0, num_keepers)
            if a != idx:
                actions.append(a)
            else:
                l = [num for num in range(0, num_keepers + 1) if num != idx]
                actions.append(random.choice(l))

        # print("randoms actions: ", actions)
        return actions, {}
