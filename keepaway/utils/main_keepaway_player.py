"""
This file is the main file for the keepaway player. It is called by the keepaway environment to start the player.
It creates an instance of the KeepawayPlayer class and calls the run method of the class.
"""
#!/usr/bin/python3
from keepaway.utils.keepaway_player import KeepawayPlayer



def main(team_name, i, is_goalie, shared_values, manager, lock, event, event_from_subprocess, main_process_event, world, obs,last_action_time,reward,terminated,proximity_adj_mat,proximity_threshold):
    agent = KeepawayPlayer(team_name,shared_values, manager, lock, event,event_from_subprocess, main_process_event, world,obs,last_action_time,reward,terminated,proximity_adj_mat,proximity_threshold)
    if not agent.handle_start():
        agent.handle_exit()
        return
    agent.run()



if __name__ == "__main__":
    main(team_name, i, is_goalie, shared_values, manager, lock, event,event_from_subprocess, main_process_event, world,obs,last_action_time,reward,terminated,proximity_adj_mat,proximity_threshold)
