from keepaway.config.game_config import get_config

def config(name):
    c = get_config()[name]
    return c