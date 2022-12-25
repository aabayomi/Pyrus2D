from enum import Enum


class OUT_OPTION(Enum):
    STDOUT = 'std'
    UNUM= 'unum'

TEAM_NAME = "PYRUS"
OUT = OUT_OPTION.STDOUT
HOST= 'localhost'
PLAYER_PORT = 6000
TRAINER_PORT = 6001
COACH_PORT = 6002
DEBUG_CLIENT_PORT = 6032