"""
    This file contains the SoccerAgent class which is the base class for all the agents.    
"""

import argparse
from keepaway.config import team_config
from keepaway.lib.player.basic_client import BasicClient


class SoccerAgent:
    def __init__(self):
        self.load_config()  # Load configuration first
        self._client = BasicClient()
        self._goalie = False

    def load_config(self):
        self.team_name = team_config.TEAM_NAME
        self.out_option = team_config.OUT
        self.host = team_config.HOST
        self.player_port = team_config.PLAYER_PORT
        self.coach_port = team_config.COACH_PORT
        self.trainer_port = team_config.TRAINER_PORT

    def init_impl(self, goalie: bool) -> bool:
        pass

    def handle_start(self) -> bool:
        pass

    def run(self):
        pass

    def handle_exit(self):
        pass
