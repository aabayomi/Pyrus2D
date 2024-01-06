from math import exp

from pyrusgeom.soccer_math import bound

import team_config
from base.strategy import Strategy
from lib.debug.debug import log
from lib.messenger.ball_goalie_messenger import BallGoalieMessenger
from lib.messenger.ball_messenger import BallMessenger
from lib.messenger.ball_player_messenger import BallPlayerMessenger
from lib.messenger.ball_pos_vel_messenger import BallPosVelMessenger
from lib.messenger.goalie_messenger import GoalieMessenger
from lib.messenger.goalie_player_messenger import GoaliePlayerMessenger
from lib.messenger.messenger import Messenger
from lib.messenger.messenger_memory import MessengerMemory
from lib.messenger.one_player_messenger import OnePlayerMessenger
from lib.messenger.recovery_message import RecoveryMessenger
from lib.messenger.stamina_messenger import StaminaMessenger
from lib.messenger.three_player_messenger import ThreePlayerMessenger
from lib.messenger.two_player_messenger import TwoPlayerMessenger
from lib.rcsc.game_time import GameTime
from lib.rcsc.server_param import ServerParam
from lib.rcsc.types import UNUM_UNKNOWN, GameModeType, SideID

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from lib.player.player_agent import PlayerAgent
    from lib.player.object_player import PlayerObject
    from lib.player.world_model import WorldModel


class ObjectScore:
    def __init__(self, n=UNUM_UNKNOWN, score=-1000, player=None):
        self.number = n
        self.score = score
        self.player: PlayerObject = player


class KeepawayCommunication:
    def __init__(self):
        self._current_sender_unum: int = UNUM_UNKNOWN
        self._next_sender_unum: int = UNUM_UNKNOWN
        self._ball_send_time: GameTime = GameTime(0, 0)
        self._teammate_send_time: list[GameTime] = [GameTime(0, 0) for i in range(12)]
        self._opponent_send_time: list[GameTime] = [GameTime(0, 0) for i in range(12)]
        self._time_last_say = -5
    
    def should_say_ball(self, agent: "PlayerAgent"):
        wm = agent.world()
        SS = ServerParam.i()
        condition1 = (wm.time() - self._time_last_say) >= SS.player_hear_decay()
        condition2 = wm.time().cycle() > 0
        return condition1 and condition2
    
    def say_recovery(self, agent: "PlayerAgent"):
        current_len = agent.effector().get_say_message_length()
        available_len = ServerParam.i().player_say_msg_size() - current_len
        if available_len < Messenger.SIZES[Messenger.Types.RECOVERY]:
            return False

        agent.add_say_message(RecoveryMessenger(agent.world().self().recovery()))
        log.sw_log().communication().add_text(
            "(sample communication) say self recovery"
        )
        return True
    # def make_say_message(self):
    def make_say_message(self,agent, soc, str_msg):
        from base.tools import Tools

        wm = agent.world()
        pos_ball = wm.ball().pos()
        vel_ball = wm.ball().vel()
        SS = ServerParam.i()
        i_diff = 0

        # my_encoder = SayMsgEncoder()
        command = self._last_body_command[-1]
        pred_ball_pos, pred_ball_vel = Tools.predict_ball_after_command(wm, command, pos_ball,vel_ball)
        # pos_ball_pred = self.WM.predict_ball_info_after_command(soc)             
        pos_agent_pred = wm.predict_agent_pos_after_command(soc)

        ##TODO - refactor this to be in player object
        maximal_kick_dist = (
            wm.self().player_type().kickable_margin()
            + wm.self().player_type().player_size()
            + SS.ball_size()
        )

        # Checking conditions for good information about the ball.
        if ((wm.get_time_change_information(OBJECT_BALL) == wm.self().time() and
             wm.ball().dist_from_self() < 20.0 and
             wm.get_time_last_seen(OBJECT_BALL) == wm.self().time()) or
            (wm.ball().dist_from_self() < SS.visible_distance() and
             self.WM.get_time_last_seen(OBJECT_BALL) == wm.self().time()) or
            (wm.ball().dist_from_self() < maximal_kick_dist and
             pos_ball_pred.get_distance_to(pos_agent_pred) > maximal_kick_dist)):
            
            if wm.ball().dist_from_self() < maximal_kick_dist:
                if soc.command_type == CMD_KICK:
                    pos_ball, vel_ball = Tools.predict_ball_after_command(wm, command, pos_ball,vel_ball)
                    pos_agent = self.WM.predict_agent_pos(1, 0)
                    if pos_ball.get_distance_to(pos_agent) > maximal_kick_dist + 0.2:
                        i_diff = 1

                if i_diff == 0:
                    pos_ball = wm.ball().pos()
                    vel_ball = VecPosition(0, 0)

            # Log and encode the message
            LogDraw.log_circle("ball sending", pos_ball, 1.1, 90, False, COLOR_BLUE)
            agent.add(BallInfo(pos_ball.x, pos_ball.y, vel_ball.x, vel_ball.y, 1 - i_diff))


        


