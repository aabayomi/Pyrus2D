"""
This configuration file describes the keep-away environment. 
It is used to define the number of keepers, takers, limit and pitch size for each keepaway game. 

"""

game_play = {
    "3v2": {
        "num_keepers": 3,
        "num_takers": 2,
        "limit": 10,
        "pitch_size": 20,
        "sparse_reward": False,
    },
    "4v3": {
        "num_keepers": 4,
        "num_takers": 3,
        "limit": 10,
        "pitch_size": 30,
        "sparse_reward": False,
    },
    "5v4": {
        "num_keepers": 5,
        "num_takers": 4,
        "limit": 10,
        "pitch_size": 40,
        "sparse_reward": False,
    },
    "hfo": {
        "offense_agents": 1,
        "defense_agents": 1,
        "offense_npcs": 0,
        "defense_npcs": 0,
        
        "limit": 10,
        "pitch_size": 20,
        "sparse_reward": False,
        "epsilon": 0.1,
    },
}


def get_config():
    return game_play
