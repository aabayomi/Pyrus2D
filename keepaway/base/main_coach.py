#!/usr/bin/python3
from keepaway.lib.player.basic_client import BasicClient
from keepaway.base.sample_coach import SampleCoach

from keepaway.config import team_config
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
