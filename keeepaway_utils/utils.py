import math

from pyrusgeom.geom_2d import *
from lib.rcsc.server_param import ServerParam
from lib.rcsc.player_type import PlayerType
from lib.rcsc.game_mode import GameModeType
from lib.action.kick_table import calc_max_velocity
import pyrusgeom.soccer_math as sm

# from lib.rcsc.types import CommandType
from lib.player_command.player_command import CommandType
from pyrusgeom.vector_2d import Vector2D
from pyrusgeom.angle_deg import AngleDeg

from lib.action.turn_to_ball import TurnToBall
from lib.action.neck_body_to_ball import NeckBodyToBall
from base.basic_tackle import BasicTackle
from lib.rcsc.server_param import ServerParam

from keeepaway_utils.keepaway_actions import (
    SmartKick,
    GoToPoint,
    NeckBodyToPoint,
    NeckScanField,
    NeckScanPlayers,
    NeckTurnToBall,
    HoldBall,
)
from keeepaway_utils.tools import Tools


from pyrusgeom.soccer_math import *
from pyrusgeom.rect_2d import Rect2D
from pyrusgeom.vector_2d import Vector2D
from pyrusgeom.line_2d import Line2D
from pyrusgeom.segment_2d import Segment2D
from pyrusgeom.geom_2d import *
from lib.debug.debug import log
from lib.action.intercept import Intercept

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from lib.player.world_model import WorldModel
    from lib.player.object_player import PlayerObject


class Takers:
    """Takers class."""

    @staticmethod
    def get_marking_position(
        wm: "WorldModel", player_pos: Vector2D, distance: float
    ) -> Vector2D:
        """Returns the marking position."""
        ball_pos = wm.ball().pos()
        ball_angle = (ball_pos - player_pos._pos).dir()
        return player_pos._pos + Vector2D.polar2vector(distance, ball_angle)

    @staticmethod
    def mark_opponent(wm: "WorldModel", p, distance, obj, agent: "PlayerAgent"):
        """Mark the given opponent."""

        # pos_mark = get_marking_position(wm, p, distance)
        player_mark_pos = Takers.get_marking_position(wm, p, distance)
        player_pos = p.pos()
        pos_ball = wm.ball().pos()
        if obj == "ball":
            if player_mark_pos.dist(player_pos) < 1.5:
                TurnToBall().execute(agent)
            else:
                GoToPoint(player_mark_pos, 0.2, 100).execute(agent)
            if player_pos.dist(player_mark_pos) < 2.0:
                ang_opp = (p.pos() - player_pos).th()
                ang_ball = (pos_ball - player_pos).th()
                normalized_ang_opp = AngleDeg.normalize_angle(ang_opp + 180)

                if ang_ball.is_within(ang_opp, normalized_ang_opp):
                    ang_opp += 80
                else:
                    ang_opp -= 80

                ang_opp = AngleDeg.normalize_angle(ang_opp)
                target = player_pos + Vector2D(1.0, ang_opp, POLAR)

                return NeckBodyToPoint(target).execute(agent)

        return GoToPoint(player_mark_pos, 0.2, 100).execute(agent)

    @staticmethod
    def mark_most_open_opponent(wm: "WorldModel", agent: "PlayerAgent"):
        """Mark the most open opponent."""
        keepers = wm.opponents()
        if len(keepers) == 0:
            return
        else:
            pos_from = keepers[0].pos()
            min_player = None
            min = 1000
        for p in keepers:
            if p.pos_valid():
                point = p.pos()
                if point.abs_y() == 37:
                    continue
                num = Tools.get_in_set_in_cone(wm, 0.3, pos_from, point)
                if num < min:
                    min = num
                    min_player = p

        return Takers.mark_opponent(wm, min_player, 4.0, "ball", agent)


class Keepers:
    """Keepers class."""

    @staticmethod
    def keeper_with_ball(
        wm: "WorldModel", agent: "PlayerAgent", actions, last_action_time
    ):
        # print("keeper with ball")
        # action = actions[wm.self().unum()]
        action = actions[wm.self().unum() - 1]
        # print(
        #     "agent ",
        #     wm.self().unum(),
        #     " action ",
        #     actions,
        #     "my act ",
        #     actions[wm.self().unum() - 1],
        # )
        Keepers.interpret_keeper_action(wm, agent, action)

    @staticmethod
    def interpret_keeper_action(wm: "WorldModel", agent, action):
        print("interpret actions , ", action)
        if action == 0:
            print("Holding Ball ")
            # hold(wm, agent)
            HoldBall().execute(agent)
        else:
            print("Passing ")
            k = wm.teammates_from_ball()
            if len(k) > 0:
                for tm in k:
                    if tm.unum() == action:
                        temp_pos = tm.pos()
                        # print("passing to player ", tm.unum(), "at pos ", temp_pos)
                        print(
                            "i am ",
                            wm.self().unum(),
                            "at pos ",
                            wm.self().pos(),
                            "passing to player ",
                            tm.unum(),
                            "at pos ",
                            temp_pos,
                        )
                        # ball_to_player.rotate(-wm.ball().vel().th())
                        agent.do_kick_to(tm, 1.5)
                        # agent.do_kick_2(tm, 1.5)
                        ## test pass logic
                        # agent.test_pass(tm, 1.5)
                        # test_kick(wm,agent,temp_pos)
                        agent.set_neck_action(NeckScanPlayers())
                        # agent.do_kick(temp_pos, 0.8)
            # k = wm.messenger_memory().players()
            # if len(k) > 0:
            #     for tm in k:
            #         print("player num ", tm.unum_)
            #         if tm.unum_ == action:
            #             temp_pos = tm.pos_
            #             print("i am ",wm.self().unum(), "passing to player ", tm.unum_, "at pos ", temp_pos)
            #             agent.do_kick_to(tm, 2.0)
            #             agent.set_neck_action(NeckScanPlayers())

            else:
                print("no teammates")
                pass
        return

    ## should be removed ** i dont know just yet
    @staticmethod
    def do_heard_pass_receive(wm: "WorldModel", agent):
        """
        check on pass .

        """
        # print(" checking on pass ")
        # print("pass ball changed .. ", len(wm.messenger_memory().balls()))
        # print("pass time ", wm.messenger_memory().pass_time())
        # print("world model time ", wm.time())
        # print("length of pass ", wm.messenger_memory().pass_())
        # if len(wm.messenger_memory().pass_()) > 0:
        #     print("pass receiver ", wm.messenger_memory().pass_()[0]._receiver)
        # print("memory players ", wm.messenger_memory().players())

        if (
            wm.messenger_memory().pass_time() != wm.time()
            or len(wm.messenger_memory().pass_()) == 0
            or wm.messenger_memory().pass_()[0]._receiver != wm.self().unum()
        ):
            # print("False")
            return False

        self_min = wm.intercept_table().self_reach_cycle()
        intercept_pos = wm.ball().inertia_point(self_min)
        heard_pos = wm.messenger_memory().pass_()[0]._pos

        # print("heard pos ", heard_pos)

        log.sw_log().team().add_text(
            f"(sample player do heard pass) heard_pos={heard_pos}, intercept_pos={intercept_pos}"
        )

        if (
            not wm.kickable_teammate()
            and wm.ball().pos_count() <= 1
            and wm.ball().vel_count() <= 1
            and self_min < 20
        ):
            print(
                "sample player do heard pass) intercepting!", "i am ", wm.self().unum()
            )

            log.sw_log().team().add_text(
                f"(sample player do heard pass) intercepting!, self_min={self_min}"
            )
            log.debug_client().add_message("Comm:Receive:Intercept")
            Intercept().execute(agent)
            agent.set_neck_action(NeckTurnToBall())

        else:
            print(
                "(sample player do heard pass) go to point!,  cycle ",
                self_min,
                " i am ",
                wm.self().unum(),
            )

            log.sw_log().team().add_text(
                f"(sample player do heard pass) go to point!, cycle={self_min}"
            )
            log.debug_client().set_target(heard_pos)
            log.debug_client().add_message("Comm:Receive:GoTo")

            GoToPoint(heard_pos, 1.0, ServerParam.i().max_dash_power()).execute(agent)
            agent.set_neck_action(NeckTurnToBall())

    @staticmethod
    def keeper_support(wm, fastest, agent):
        """
        This method implements the keeper support.
        Keeper support.

        :param wm: WorldModel
        :param fastest: fastest player
        :param agent: PlayerAgent
        """
        from lib.messenger.one_player_messenger import OnePlayerMessenger

        sp = ServerParam.i()
        first_ball_pos = wm.ball().pos()
        min_reach_cycle = Tools.estimate_min_reach_cycle(
            fastest._pos,
            1.0,
            first_ball_pos,
            first_ball_pos.th(),
        )
        # print("min_reach_cycle ", min_reach_cycle)
        ball_vel = wm.ball().vel()
        ball_pos = wm.ball().pos()
        first_ball_speed = ball_vel.r()

        dist_ball = (
            first_ball_speed
            * (1 - pow(sp.ball_decay(), min_reach_cycle))
            / (1 - sp.ball_decay())
        )
        ball_angle = ball_vel.th()
        ball_pos += Vector2D.polar2vector(dist_ball, ball_angle)
        ball_vel += ball_vel * pow(sp.ball_decay(), min_reach_cycle)
        pos_pass_from = ball_pos

        rect = wm.keepaway_rect()
        best_point = Tools.least_congested_point_for_pass_in_rectangle(
            rect, pos_pass_from
        )

        if Keepers.do_heard_pass_receive(wm, agent) == False:
            # print("i am ", wm.self()._unum,"no pass heard")
            # print("i am ", wm.self()._unum, "going to ", best_point)
            return GoToPoint(best_point, 0.2, 100).execute(agent)
        else:
            print("pass was heard ")
            # i am waiting for the pass.

            return agent.set_neck_action(NeckScanField())

        # if wm.self().pos().dist(best_point) < 1.5:
        #     print("NeckScanField")
        #     return NeckBodyToPoint(wm.ball().pos()).execute(agent)
        #     # agent.set_neck_action(NeckScanPlayers())
        # else:
        #     print("i am ", wm.self()._unum, "going to ", best_point)

        #     # agent.add_say_message(OnePlayerMessenger(wm.self().unum(),
        #     #                                     best_point))
        #     GoToPoint(best_point, 0.2, 100).execute(agent)
        #     return

        # # # # ObjectT lookObject = self._choose_look_object( 0.97 )

    # @staticmethod
    # def test_kick(wm, agent, t):
    #     """Test implementation for kick
    #     target
    #     speed
    #     speed threshold
    #     max step
    #     similar to the goalie kick
    #     """

    #     from lib.action.smart_kick import SmartKick

    #     action_candidates = BhvPassGen().generator(wm)

    #     print("action candidates ", action_candidates)

    #     if len(action_candidates) == 0:
    #         print("Holding the ball")
    #         agent.set_neck_action(NeckScanPlayers())
    #         return HoldBall().execute(agent)

    #     best_action: KickAction = max(action_candidates)
    #     target = best_action.target_ball_pos
    #     print("Target : ", target)
    #     log.debug_client().set_target(target)
    #     log.debug_client().add_message(
    #         best_action.type.value
    #         + "to "
    #         + best_action.target_ball_pos.__str__()
    #         + " "
    #         + str(best_action.start_ball_speed)
    #     )

    #     # print(" best action speed ", best_action.start_ball_speed)

    #     # SmartKick(
    #     #     target, best_action.start_ball_speed, best_action.start_ball_speed - 1, 3
    #     # ).execute(agent)
    #     agent.set_neck_action(NeckScanPlayers())

    #     return
