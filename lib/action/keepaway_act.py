import functools

from lib.debug.debug import log
from lib.debug.level import Level

# from pyrusgeom.soccer_math import *
from pyrusgeom.angle_deg import AngleDeg
from lib.action.stop_ball import StopBall
from lib.action.basic_actions import TurnToPoint
from lib.player.soccer_action import BodyAction
from lib.rcsc.game_time import GameTime
from lib.rcsc.server_param import ServerParam
from pyrusgeom.rect_2d import Rect2D
from pyrusgeom.size_2d import Size2D
from pyrusgeom.line_2d import Line2D
from pyrusgeom.vector_2d import Vector2D
from pyrusgeom.segment_2d import Segment2D
from pyrusgeom.circle_2d import Circle2D



from lib.player.soccer_action import NeckAction
from lib.rcsc.server_param import ServerParam
from lib.rcsc.types import GameModeType, ViewWidth
from lib.player.world_model import WorldModel

from pyrusgeom.geom_2d import AngleDeg

# from lib.action.neck_scan_field import NeckScanField
from lib.action.neck_turn_to_ball import NeckTurnToBall
from lib.debug.debug import log
from lib.player.soccer_action import NeckAction

from lib.player.soccer_action import *
from lib.action.kick_table import KickTable, Sequence
from lib.debug.level import Level

import math as math

# from lib.rcsc.server_param import ServerParam as SP
import pyrusgeom.soccer_math as smath
from pyrusgeom.geom_2d import *

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from lib.player.world_model import WorldModel
    from lib.player.player_agent import PlayerAgent

DEFAULT_SCORE = 100.0

from pyrusgeom.vector_2d import Vector2D

from lib.action.neck_body_to_point import NeckBodyToPoint
from lib.action.neck_turn_to_relative import NeckTurnToRelative
from lib.action.view_wide import ViewWide
from lib.debug.debug import log
from lib.player.soccer_action import BodyAction

from typing import TYPE_CHECKING

from lib.rcsc.types import ViewWidth

if TYPE_CHECKING:
    from lib.player.player_agent import PlayerAgent


SoccerCommand BasicPlayer::searchBall() {
  static Time timeLastSearch;
  static SoccerCommand soc;
  static int iSign = 1;
  VecPosition posBall = WM->getBallPos();
  VecPosition posAgent = WM->getAgentGlobalPosition();
  AngDeg angBall = (posBall - WM->getAgentGlobalPosition()).getDirection();
  AngDeg angBody = WM->getAgentGlobalBodyAngle();

  if (WM->getCurrentTime().getTime() == timeLastSearch.getTime())
    return soc;

  if (WM->getCurrentTime() - timeLastSearch > 3)
    iSign = (isAngInInterval(angBall, angBody,
                             VecPosition::normalizeAngle(angBody + 180)))
            ? 1
            : -1;

  //  if( iSign == -1 )
  // angBall = VecPosition::normalizeAngle( angBall + 180 );

  soc = turnBodyToPoint(posAgent + VecPosition(1.0,
                                               VecPosition::normalizeAngle(angBody + 60 * iSign), POLAR));
  Log.log(556, "search ball: turn to %f s %d t(%d %d) %f", angBall, iSign,
          WM->getCurrentTime().getTime(), timeLastSearch.getTime(),
          soc.dAngle);
  timeLastSearch = WM->getCurrentTime();
  return soc;
}

class SearchBall(BodyAction):
    def __init__(self):
        pass

    def execute(self, agent: "PlayerAgent"):
        log.debug_client().add_message("SearchBall/")
        wm = agent.world()
        if wm.ball().seen():
            return
        ball_pos = wm.ball().pos()
        pos = wm.self().pos()
        ball_angle = (ball_pos - wm.self().pos()).dir()
        body_angle = wm.self().body()


    # def find_ball(self, agent: "PlayerAgent"):
    #     wm = agent.world()
    #     # print(wm.ball().pos())
    #     # print("find ball/")

    #     if agent.effector().queued_next_view_width() is not ViewWidth.WIDE:
    #         agent.set_view_action(ViewWide())

    #     my_next = wm.self().pos() + wm.self().vel()
    #     face_angle = (
    #         (wm.ball().seen_pos() - my_next).th()
    #         if wm.ball().seen_pos().is_valid()
    #         else (my_next * -1).th()
    #     )

    #     search_flag = wm.ball().lost_count() // 3
    #     if search_flag % 2 == 1:
    #         face_angle += 180.0

    #     face_point = my_next + Vector2D(r=10, a=face_angle)
    #     NeckBodyToPoint(face_point).execute(agent)

    # def scan_all_field(self, agent: "PlayerAgent"):
    #     wm = agent.world()
    #     # print(wm.ball().pos())
    #     # print("find ball/")

    #     if agent.effector().queued_next_view_width() is not ViewWidth.WIDE:
    #         agent.set_view_action(ViewWide())

    #     turn_moment = (
    #         wm.self().view_width().width()
    #         + agent.effector().queued_next_view_width().width()
    #     )
    #     turn_moment /= 2
    #     agent.do_turn(turn_moment)
    #     agent.set_neck_action(NeckTurnToRelative(wm.self().neck()))

    