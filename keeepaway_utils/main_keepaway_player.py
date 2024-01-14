#!/usr/bin/python3
from keeepaway_utils.keepaway_player import KeepawayPlayer
from lib.player.basic_client import BasicClient
from lib.player.player_agent import PlayerAgent
import sys
import team_config


def main(team_name, i, is_goalie, shared_values, manager, lock, event, event_from_subprocess, main_process_event, world, obs,last_action_time,reward,terminated):
    agent = KeepawayPlayer(team_name,shared_values, manager, lock, event,event_from_subprocess, main_process_event, world,obs,last_action_time,reward,terminated)
    if not agent.handle_start():
        agent.handle_exit()
        return
    # print("Starting agent {}".format(i))
    agent.run()


if __name__ == "__main__":
    main(team_name, i, is_goalie, shared_values, manager, lock, event,event_from_subprocess, main_process_event, world,obs,last_action_time,reward,terminated)
