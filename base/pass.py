from lib.action.hold_ball import HoldBall
from lib.action.neck_scan_players import NeckScanPlayers
from lib.action.smart_kick import SmartKick
from typing import List
from base.generator_action import KickAction, ShootAction, KickActionType
from base.generator_dribble import BhvDribbleGen
from base.generator_pass import BhvPassGen
from base.generator_shoot import BhvShhotGen
from base.generator_clear import BhvClearGen

from typing import TYPE_CHECKING

from lib.debug.debug import log
from lib.messenger.pass_messenger import PassMessenger

if TYPE_CHECKING:
    from lib.player.world_model import WorldModel
    from lib.player.player_agent import PlayerAgent


class Pass:
    def __init__(self):
        pass
    def execute(self, agent: "PlayerAgent"):


    def kick_to():
        pass
