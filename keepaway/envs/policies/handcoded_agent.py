""" 
Implementation for handcoded policy for keepaway.

Handcoded policy keepaway adapted from Adaptive Behavior '05 article
* Stone, Sutton, and Kuhlmann.

"""

import numpy as np


class HandcodedPolicy:
    def __init__(self, config=None):
        """Initializes the policy."""
        if config is not None:
            self.num_keepers = config["num_keepers"]
            self.num_takers = config["num_takers"]
        else:
            self.num_keepers = 3
            self.num_takers = 2

        ## this is same as beta in the paper stone et al. 2005
        self.hold_distance = 90.0
        ## this is same as alpha in the paper stone et al. 2005.
        self.dist_weight = 4.0

        self.distance_threshold = 10.0

    def select_agent_action(self, obs, agent_id):
        """
        Returns the ac in the keep-away domain.
        """

        scores = [0] * self.num_keepers

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

        # set current agent index to a very small value
        scores[agent_id - 1] = -1000000.0
        my_distance_to_taker = obs[start_idx : start_idx + self.num_takers]
        if my_distance_to_taker[0] > self.distance_threshold:
            return 0

        for i in range(self.num_keepers):
            if i == agent_id - 1:
                pass
            else:
                a = self.dist_weight * obs[start_idx + i] + obs[last_index + i]
                scores[i] = a

        best = np.argmax(scores)
        if scores[best] < self.hold_distance:
            return best
        else:
            return 0

    def get_actions(self, obs):
        """Returns the actions for the agents in the keep-away domain.
            Hold threshold (alpha)
            beta : Dist/Ang ratio (beta)
        Args:
            obs: dict of observations for each agent.
        Returns:
            actions: list of actions for each agent.
            agent_infos: dict of agent information.
        """

        agent_ids = obs.keys()

        ## Check if no observations are available.
        actions = [0] * len(agent_ids)

        for id, agent_obs in obs.items():
            if agent_obs is None:
                actions[id - 1] = 0
            else:
                a = self.select_agent_action(agent_obs, id)
                actions[id - 1] = a
        return actions, {}
