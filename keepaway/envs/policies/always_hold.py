""" 
Implementation for always-hold policy for keepaway.

Always Hold policy keepaway adapted from Adaptive Behavior '05 article
* Stone, Sutton, and Kuhlmann.

"""


class AlwaysHoldPolicy(object):
    def __init__(self, config=None):
        if config is not None:
            self.num_keepers = config["num_keepers"]
            self.num_takers = config["num_takers"]
        else:
            self.num_keepers = 3
            self.num_takers = 2

    def get_actions(self, obs, greedy=False):
        agent_ids = obs.keys()  # {1, 2, 3}
        actions = [0] * self.num_keepers
        for id, agent_obs in obs.items():
            if agent_obs is None:
                actions[id - 1] = 0
            else:
                a = 0
                actions[id - 1] = a
        return actions, {}
