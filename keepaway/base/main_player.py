#!/usr/bin/python3
from keepaway.base.sample_player import SamplePlayer
from keepaway.lib.player.basic_client import BasicClient
from keepaway.lib.player.player_agent import PlayerAgent
import sys
import team_config


def main():
    agent = SamplePlayer()
    if not agent.handle_start():
        agent.handle_exit()
        return
    agent.run()


if __name__ == "__main__":
    main()
