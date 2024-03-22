from keepaway.config.game_config import get_config

def config(name):
    con = get_config()[name]
    return con