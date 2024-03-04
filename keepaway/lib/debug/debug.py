import sys
from logging import Logger

# from keepaway.config import team_config
from keepaway.config import team_config
from keepaway.lib.debug.debug_client import DebugClient
from keepaway.lib.debug.os_logger import get_logger
from keepaway.lib.debug.sw_logger import SoccerWindow_Logger
from keepaway.lib.rcsc.game_time import GameTime
import os

up_one_dir = os.path.dirname(os.getcwd())
logs_dir  = os.path.join(up_one_dir, "logs")

class DebugLogger:
    def __init__(self):
        self._sw_log: SoccerWindow_Logger = SoccerWindow_Logger('NA', 1, GameTime(0, 0))
        self._os_log: Logger = get_logger(0, False)
        self._debug_client: DebugClient = None

    def setup(self, team_name, unum, time):
        sys.stderr = open(f'{logs_dir}/player-{unum}.err', 'w')
        self._sw_log = SoccerWindow_Logger(team_name, unum, time)
        self._os_log = get_logger(unum, team_config.OUT == team_config.OUT_OPTION.TEXTFILE)
        self._debug_client = DebugClient()

    def sw_log(self):
        return self._sw_log

    def os_log(self):
        return self._os_log

    def debug_client(self):
        return self._debug_client

    def update_time(self, t: GameTime):
        self._time.assign(t.cycle(), t.stopped_cycle())


log = DebugLogger()
