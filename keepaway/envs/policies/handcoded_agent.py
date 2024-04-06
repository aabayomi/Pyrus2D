""" 
Implementation for handcoded policy for keepaway.

Handcoded policy keepaway adapted from Adaptive Behavior '05 article
* Stone, Sutton, and Kuhlmann.

"""

import numpy as np

class HandcodedPolicy():
    def __init__(self, config=None):
        """Initializes the policy."""
        if config is not None:
            self.num_keepers = config["num_keepers"]
            self.num_takers = config["num_takers"]
        else:
            self.num_keepers = 3
            self.num_takers = 2

        # self.num_keepers = 3
        # self.num_takers = 2

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
        """Returns the action for the agent in the keep-away domain."""

        # print("obs ", obs)

        scores = [None] * self.num_keepers

        # set current agent index to a very small value
        
        if isinstance(obs, dict):
            obs = obs["state_vars"]
        else:
            obs = obs


        if self.num_keepers == 3:
            start_idx = 7
        elif self.num_keepers == 4:
            start_idx = 10
        elif self.num_keepers == 5:
            start_idx = 13

        last_index = (len(obs) - 1) - self.num_takers 

        nearest_opp_k_dist = obs[start_idx : start_idx + self.num_takers]
        nearest_opp_k_angle = obs[last_index + 1 : ]
        
        if len(nearest_opp_k_dist) > 0:
            if nearest_opp_k_dist[0] > self.distance_threshold:
                return 0

        for i in range(self.num_keepers):
            if i == agent_id - 1:
                scores[i] = -1000000.0
            else:
                scores[i] = (
                    self.dist_weight * obs[start_idx + i]
                    + obs[last_index + i]
                )  

        best = np.argmax(scores)
        if scores[best] > self.hold_distance:
            return best + 1
        else:
            return 0

    def get_actions(self, obs):
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
