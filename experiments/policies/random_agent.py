""" 
Author: Abayomi Adekanmbi and Peter Stone
Base Implementation for handcoded policy for keepaway.

Random policy baseline adapted from Adaptive Behavior '05 article
* Stone, Sutton, and Kuhlmann.

"""

import random

class RandomPolicy(object): 
    def __init__(self):
        pass
    def get_actions(self,obs, greedy=False):
        """
            Returns a random action for each agent.
        """
        agents_ids = obs.keys()
        actions = []
        for idx in agents_ids:
            a = random.randint(1, 3)
            if a != idx:
                actions.append(a)
            else:
                l = [1, 2, 3]
                l.remove(idx)
                actions.append(random.choice(l))

        # print("randoms actions: ", actions)
        return actions, {}

