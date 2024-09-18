"""
HFO Handcoded Policy

"""

## TODO: create an action table.

import numpy as np
class HFOHandcodedPolicy:
    def __init__(self, config=None):
        """
        Initializes the HFO handcoded agent.
        """
        self.old_ball_pos_x = -1
        self.old_ball_pos_y = 0
        self.epsilon = 0
        self.num_times_overall = {}
        self.num_times_kickable = {}

        for action in range(hfo.NUM_HFO_ACTIONS):
            self.num_times_overall[action] = 0
            self.num_times_kickable[action] = 0

        self.misc_tracked = {"max_kickable_dist": 0}

    def get_actions(self, obs):
        """
        Returns the actions for the agents.
        """
        state = obs
        if episode_start:
            if (state[3] >= -1) and (state[3] <= 1):
                self.old_ball_pos_x = state[3]
            if (state[4] >= -1) and (state[4] <= 1):
                self.old_ball_pos_y = state[4]
            episode_start = False
        if (self.epsilon > 0) and (random.random() < self.epsilon):
            # do_random_defense_action(state, hfo_env)
            return 0
        else:
            self.old_ball_pos_x = state[3]
            self.old_ball_pos_y = state[4]
            return 1

        # if status == hfo.SERVER_DOWN:
        #     for action in range(hfo.NUM_HFO_ACTIONS):
        #         if num_times_overall[action]:
        #             print("Overall times {0!s}: {1:d}".format(hfo_env.actionToString(action),
        #                                             num_times_overall[action]))
        #     for action in range(hfo.NUM_HFO_ACTIONS):
        #         if num_times_kickable[action]:
        #             print("Kickable times {0!s}: {1:d}".format(hfo_env.actionToString(action),
        #                                              num_times_kickable[action]))
        #     print("Max kickable dist: {0:n}".format(misc_tracked['max_kickable_dist']))
        #     hfo_env.act(hfo.QUIT)
        #     exit()

        # print("Episode {0:d} ended with {1:s}".format(episode,
        #                                           hfo_env.statusToString(status)))
