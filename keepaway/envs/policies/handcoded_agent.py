""" 
Implementation for handcoded policy for keepaway.

Handcoded policy keepaway adapted from Adaptive Behavior '05 article
* Stone, Sutton, and Kuhlmann.

"""

import numpy as np

class HandcodedPolicy(object):
    def __init__(self):
        """Initializes the policy."""

        self.num_keepers = 3
        self.num_takers = 2

        ## this is same as beta in the paper stone et al. 2005
        self.hold_distance = 90.0
        ## this is same as alpha in the paper stone et al. 2005.
        self.dist_weight = 4.0

        self.distance_threshold = 5.0

    def is_full_observation(self, obs):
        """Returns True if the observation is complete.
        Args:
            obs: dict of observations for each agent.
        Returns:
        """
        for i in obs.keys():
            if obs[i] is None:
                return False
            if obs[i]["state_vars"] is None:
                return False
            if len(obs[i]["state_vars"]) < 13:
                return False
        return True

    def select_agent_action(self, obs, agent_id):
        """Returns the action for the agent in the keepaway domain."""

        scores = [None] * self.num_keepers

        # set current agent index to a very small value
        scores[agent_id - 1] = -1000000.0

        my_distance_to_taker = obs["state_vars"][7 : 7 + self.num_takers]
        if my_distance_to_taker[0] > self.distance_threshold:
            return 0

        for i in range(self.num_keepers):
            if i == agent_id - 1:
                pass
            else:
                scores[i] = (
                    self.dist_weight * obs["state_vars"][7 + i]
                    + obs["state_vars"][9 + i]
                )  

        best = np.argmax(scores)
        if scores[best] > self.hold_distance:
            return best + 1
        else:
            return 0

    def get_actions(self, obs, greedy=False):
        """Returns the actions for the agents in the keepaway domain."""

        agent_ids = obs.keys() 
        ## Hold threshold (alpha)
        ## beta : Dist/Ang ratio (beta)

        ## Check if no observations are available.
        actions = [None] * len(agent_ids)
        for id, agent_obs in obs.items():
            if agent_obs is None:
                actions[id - 1] = 0
            else:
                a = self.select_agent_action(agent_obs, id)
                # print(id,a)
                actions[id - 1] = a
        return actions, {}
