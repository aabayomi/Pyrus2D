from keepaway.lib.action.neck_scan_field import NeckScanField
from keepaway.lib.action.scan_field import ScanField
from keepaway.lib.debug.level import Level
from pyrusgeom.angle_deg import AngleDeg
from keepaway.base.strategy_formation import StrategyFormation

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from keepaway.lib.player.player_agent import PlayerAgent


class Bhv_BeforeKickOff:
    def __init__(self):
        pass

    def execute(self, agent: "PlayerAgent"):
        unum = agent.world().self().unum()
        st = StrategyFormation.i()
        target = st.get_pos(unum)
        if target.dist(agent.world().self().pos()) > 1.0:
            agent.do_move(target.x(), target.y())
            agent.set_neck_action(NeckScanField())
            return True
        ScanField().execute(agent)
        return True
