from pyrusgeom.geom_2d import *
from keepaway.lib.rcsc.server_param import ServerParam
from pyrusgeom.vector_2d import Vector2D
from pyrusgeom.angle_deg import AngleDeg

from keepaway.lib.action.turn_to_ball import TurnToBall
from keepaway.lib.rcsc.server_param import ServerParam

from keepaway.utils.keepaway_actions import (
    SmartKick,
    GoToPoint,
    NeckBodyToPoint,
    NeckScanField,
    NeckScanPlayers,
    NeckTurnToBall,
    HoldBall,
)
from keepaway.utils.tools import Tools


from pyrusgeom.soccer_math import *
from pyrusgeom.vector_2d import Vector2D
from pyrusgeom.geom_2d import *
from keepaway.lib.debug.debug import log
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from keepaway.lib.player.world_model import WorldModel
    from keepaway.lib.player.object_player import PlayerObject


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
                return TurnToBall().execute(agent)
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
        action = actions[wm.self().unum() - 1]
        Keepers.interpret_keeper_action(wm, agent, action)

    @staticmethod
    def interpret_keeper_action(wm: "WorldModel", agent, action):
        if action == 0:
            return HoldBall().execute(agent)
        else:
            k = wm.teammates_from_ball()
            if len(k) > 0:
                for tm in k:
                    if tm.unum() == action:
                        temp_pos = tm.pos()
                        return agent.do_kick_to(tm, 1.5)
        return

    ## should be removed ** i dont know just yet
    @staticmethod
    def do_heard_pass_receive(wm: "WorldModel", agent):
        """
        check on pass .

        """
        if (
            wm.messenger_memory().pass_time() != wm.time()
            or len(wm.messenger_memory().pass_()) == 0
            or wm.messenger_memory().pass_()[0]._receiver != wm.self().unum()
        ):
            return False

        self_min = wm.intercept_table().self_reach_cycle()
        intercept_pos = wm.ball().inertia_point(self_min)
        heard_pos = wm.messenger_memory().pass_()[0]._pos
        log.sw_log().team().add_text(
            f"(sample player do heard pass) heard_pos={heard_pos}, intercept_pos={intercept_pos}"
        )

        if (
            not wm.kickable_teammate()
            and wm.ball().pos_count() <= 1
            and wm.ball().vel_count() <= 1
            and self_min < 20
        ):
            log.sw_log().team().add_text(
                f"(sample player do heard pass) intercepting!, self_min={self_min}"
            )
            log.debug_client().add_message("Comm:Receive:Intercept")
            GoToPoint(heard_pos, 1.0, ServerParam.i().max_dash_power()).execute(agent)
            return True
        else:
            log.sw_log().team().add_text(
                f"(sample player do heard pass) go to point!, cycle={self_min}"
            )
            log.debug_client().set_target(heard_pos)
            log.debug_client().add_message("Comm:Receive:GoTo")

            GoToPoint(heard_pos, 1.0, ServerParam.i().max_dash_power()).execute(agent)
            agent.set_neck_action(NeckTurnToBall())
            return True

    @staticmethod
    def keeper_support(wm, fastest, agent):
        """
        This method implements the keeper support.
        Keeper support.

        :param wm: WorldModel
        :param fastest: fastest player
        :param agent: PlayerAgent
        """
        from keepaway.lib.messenger.one_player_messenger import OnePlayerMessenger

        sp = ServerParam.i()
        first_ball_pos = wm.ball().pos()
        min_reach_cycle = Tools.estimate_min_reach_cycle(
            fastest._pos,
            1.0,
            first_ball_pos,
            first_ball_pos.th(),
        )
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
            wm, rect, pos_pass_from
        )

        if wm.self().pos().dist(best_point) < 1.5:
            return NeckBodyToPoint(wm.ball().pos()).execute(agent)
        else:
            return GoToPoint(best_point, 0.2, 100).execute(agent)
