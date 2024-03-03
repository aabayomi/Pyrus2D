""" 
keepaway.base Implementation.

Always Hold policy keepaway.baseline adapted from Adaptive Behavior '05 article
* Stone, Sutton, and Kuhlmann.

"""


class AlwaysHoldPolicy(object):
    def __init__(self):
        pass

    def get_actions(self, obs, greedy=False):
        agent_ids = obs.keys()  # {1, 2, 3}
        actions = [None] * len(agent_ids)
        for id, agent_obs in obs.items():
            if agent_obs is None:
                actions[id - 1] = 0
            else:
                a = 0
                actions[id - 1] = a

        return actions, {}
