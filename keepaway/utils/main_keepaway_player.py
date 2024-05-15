#!/usr/bin/python3

"""
    This file is the main file for the keepaway player. It is called by the keepaway environment to start the player.
    It initializes the player and runs the player.
"""

from keepaway.utils.keepaway_player import KeepawayPlayer


def main(
    team_name,
    i,
    is_goalie,
    shared_values,
    manager,
    lock,
    event,
    event_from_subprocess,
    main_process_event,
    world,
    obs,
    last_action_time,
    reward,
    terminated,
    proximity_adj_mat,
    proximity_threshold,
):
    agent = KeepawayPlayer(
        team_name,
        shared_values,
        manager,
        lock,
        event,
        event_from_subprocess,
        main_process_event,
        world,
        obs,
        last_action_time,
        reward,
        terminated,
        proximity_adj_mat,
        proximity_threshold,
    )
    if not agent.handle_start():
        agent.handle_exit()
        return
    agent.run()


if __name__ == "__main__":
    main(
        team_name,
        i,
        is_goalie,
        shared_values,
        manager,
        lock,
        event,
        event_from_subprocess,
        main_process_event,
        world,
        obs,
        last_action_time,
        reward,
        terminated,
        proximity_adj_mat,
        proximity_threshold,
    )
