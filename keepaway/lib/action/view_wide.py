from keepaway.lib.player.soccer_action import ViewAction
from keepaway.lib.rcsc.types import ViewWidth

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from keepaway.lib.player.player_agent import PlayerAgent


class ViewWide(ViewAction):
    def execute(self, agent: 'PlayerAgent'):
        return agent.do_change_view(ViewWidth.WIDE)