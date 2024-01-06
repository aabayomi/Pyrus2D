""" 
Author: Abayomi Adekanmbi and Peter Stone
Base Implementation for handcoded policy for keepaway.

Always Hold policy baseline adapted from Adaptive Behavior '05 article
* Stone, Sutton, and Kuhlmann.

"""

class AlwaysHoldPolicy(object):
    def __init__(self):
        pass
    def get_actions(self,obs,avail_actions, greedy=False):
       return 0