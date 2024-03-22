"""
This configuration file describes the keepaway environment. 
It is used to define the number of keepers, takers, limit and pitch size for each keepaway game. 

"""

game_play = {
    "3v2":{
        "num_keepers": 3,
        "num_takers": 2,
        "limit": 10,
        "pitch_size": 20,
    },
    "4v3":{
        "num_keepers": 4,
        "num_takers": 3,
        "limit": 10,
        "pitch_size": 30,
    },
    "5v4":{
        "num_keepers": 5,
        "num_takers": 4,
        "limit": 10,
        "pitch_size": 40,
    },
}

def get_config():
    return game_play

