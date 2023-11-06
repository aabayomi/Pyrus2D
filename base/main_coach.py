#!/usr/bin/python3
from lib.player.basic_client import BasicClient
from base.sample_coach import SampleCoach

import team_config
import sys


def main():
    agent = SampleCoach()
    print(agent.handle_start())
    if not agent.handle_start():
        # print("Failed to start") 
        agent.handle_exit()
        return
    print("Starting Coach")
    agent.run()


if __name__ == "__main__":
    main()
