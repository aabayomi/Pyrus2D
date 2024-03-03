import functools

from keepaway.lib.debug.debug import log
from keepaway.lib.debug.level import Level

# from pyrusgeom.soccer_math import *
from pyrusgeom.angle_deg import AngleDeg
from keepaway.lib.action.stop_ball import StopBall
from keepaway.lib.action.basic_actions import TurnToPoint
from keepaway.lib.player.soccer_action import BodyAction
from keepaway.lib.rcsc.game_time import GameTime
from keepaway.lib.rcsc.server_param import ServerParam
from pyrusgeom.rect_2d import Rect2D
from pyrusgeom.size_2d import Size2D
from pyrusgeom.line_2d import Line2D
from pyrusgeom.vector_2d import Vector2D
from pyrusgeom.segment_2d import Segment2D
from pyrusgeom.circle_2d import Circle2D


from keepaway.lib.player.soccer_action import NeckAction
from keepaway.lib.rcsc.server_param import ServerParam
from keepaway.lib.rcsc.types import GameModeType, ViewWidth
from keepaway.lib.player.world_model import WorldModel

from pyrusgeom.geom_2d import AngleDeg

# from keepaway.lib.action.neck_scan_field import NeckScanField
from keepaway.lib.action.neck_turn_to_ball import NeckTurnToBall
from keepaway.lib.debug.debug import log
from keepaway.lib.player.soccer_action import NeckAction

from keepaway.lib.player.soccer_action import *
from keepaway.lib.action.kick_table import KickTable, Sequence
from keepaway.lib.debug.level import Level
from pyrusgeom.soccer_math import bound
from keepaway.lib.action.neck_turn_to_relative import NeckTurnToRelative

import math as math

# from keepaway.lib.rcsc.server_param import ServerParam as SP
import pyrusgeom.soccer_math as smath
from pyrusgeom.geom_2d import *

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from keepaway.lib.player.world_model import WorldModel
    from keepaway.lib.player.player_agent import PlayerAgent

DEFAULT_SCORE = 100.0

from keepaway.lib.action.view_wide import ViewWide

def KeepPointCmp(item1, item2) -> bool:
    return item1.score_ < item2.score_


class KeepPoint:
    """
    \ brief construct with arguments
    \ param pos global position
    \ param krate kick rate at the position
    \ param score initial score
    """

    def __init__(self, pos=Vector2D.invalid(), kickrate=0.0, score=-10000000.0):
        self.pos_ = pos
        self.kick_rate_ = kickrate
        self.score_ = score

    """
      \ brief reset object value
    """

    def reset(self):
        self.pos_.invalidate()
        self.kick_rate_ = 0.0
        self.score_ = -10000000.0


class HoldBall(BodyAction):
    """
    \ brief accessible from global.
    """

    def __init__(
        self,
        do_turn=False,
        turn_target_point=Vector2D(0.0, 0.0),
        kick_target_point=Vector2D.invalid(),
    ):
        super().__init__()
        self._do_turn = do_turn
        self._turn_target_point = turn_target_point
        self._kick_target_point = kick_target_point

    """
      \ brief execute action
      \ param agent the agent itself
      \ return True if action is performed
    """

    def execute(self, agent: "PlayerAgent"):
        wm: "WorldModel" = agent.world()
        if not wm.self().is_kickable():
            log.sw_log().kick().add_text("not kickable")
            return False

        if not wm.ball().vel_valid():
            return StopBall().execute(agent)

        if self.keepReverse(agent):
            return True

        if self.turnToPoint(agent):
            return True

        if self.keepFront(agent):
            return True

        if self.avoidOpponent(agent):
            return True

        log.sw_log().kick().add_text("only stop ball")

        return StopBall().execute(agent)

    """
          \ brief kick the ball to avoid opponent
          \ param  agent itself
          \ return True if action is performed
    """

    def avoidOpponent(self, agent: "PlayerAgent"):
        wm: "WorldModel" = agent.world()
        point = self.searchKeepPoint(wm)
        if not point.is_valid():
            log.sw_log().kick().add_text("avoidOpponent() no candidate point")
            return False
        ball_move = point - wm.ball().pos()
        kick_accel = ball_move - wm.ball().vel()
        kick_accel_r = kick_accel.r()
        agent.do_kick(
            kick_accel_r / wm.self().kick_rate(), kick_accel.th() - wm.self().body()
        )
        return True

    """
      \ brief search the best keep point
      \ param wm  reference to the WorldModel instance
      \ return estimated best keep point. if no point, is returned.
     """

    def searchKeepPoint(self, wm: "WorldModel"):
        s_last_update_time = GameTime(0, 0)
        s_keep_points = []
        s_best_keep_point = KeepPoint()
        if s_last_update_time != wm.time():
            s_best_keep_point.reset()
            s_keep_points = self.createKeepPoints(wm, s_keep_points)
            self.evaluateKeepPoints(wm, s_keep_points)
            if s_keep_points:
                s_best_keep_point = max(
                    s_keep_points, key=functools.cmp_to_key(KeepPointCmp)
                )
        return s_best_keep_point.pos_

    """
      \ brief create candidate keep points
      \ param wm  reference to the WorldModel instance
      \ param keep_points reference to the variable container
     """

    def createKeepPoints(self, wm: "WorldModel", candidates):
        param = ServerParam.i()

        max_pitch_x = param.keepaway_length() - 0.2
        max_pitch_y = param.keepaway_length() - 0.2

        dir_divs = 20
        dir_step = 360.0 / dir_divs

        near_dist = (
            wm.self().player_type().player_size()
            + param.ball_size()
            + wm.self().player_type().kickable_margin() * 0.4
        )
        mid_dist = (
            wm.self().player_type().player_size()
            + param.ball_size()
            + wm.self().player_type().kickable_margin() * 0.6
        )
        far_dist = (
            wm.self().player_type().player_size()
            + param.ball_size()
            + wm.self().player_type().kickable_margin() * 0.8
        )

        # candidates = [] * dir_divs * 2

        my_next = wm.self().pos() + wm.self().vel()

        my_noise = wm.self().vel().r() * param.player_rand()
        current_dir_diff_rate = (
            wm.ball().angle_from_self() - wm.self().body()
        ).abs() / 180.0
        current_dist_rate = (
            wm.ball().dist_from_self()
            - wm.self().player_type().player_size()
            - param.ball_size()
        ) / wm.self().player_type().kickable_margin()
        current_pos_rate = 0.5 + 0.25 * (current_dir_diff_rate + current_dist_rate)
        current_speed_rate = 0.5 + 0.5 * (
            wm.ball().vel().r() / (param.ball_speed_max() * param.ball_decay())
        )

        angles = [-180 + a * dir_step for a in range(dir_divs)]
        for d in angles:
            angle = AngleDeg(d)
            dir_diff = (angle - wm.self().body()).abs()
            unit_pos = Vector2D.polar2vector(1.0, angle)

            # near side point
            near_pos = my_next + unit_pos.set_length_vector(near_dist)
            if near_pos.abs_x() < max_pitch_x and near_pos.abs_y() < max_pitch_y:
                ball_move = near_pos - wm.ball().pos()
                kick_accel = ball_move - wm.ball().vel()

                # can kick to the point by 1 step kick
                if kick_accel.r() < param.max_power() * wm.self().kick_rate():
                    near_krate = wm.self().player_type().kick_rate(near_dist, dir_diff)
                    # can stop the ball by 1 step kick
                    if (
                        ball_move.r() * param.ball_decay()
                        < param.max_power() * near_krate
                    ):
                        candidates.append(
                            KeepPoint(near_pos, near_krate, DEFAULT_SCORE)
                        )
            # middle point
            mid_pos = my_next + unit_pos.set_length_vector(mid_dist)
            if mid_pos.abs_x() < max_pitch_x and mid_pos.abs_y() < max_pitch_y:
                ball_move = mid_pos - wm.ball().pos()
                kick_accel = ball_move - wm.ball().vel()
                kick_power = kick_accel.r() / wm.self().kick_rate()

                # can kick to the point by 1 step kick
                if kick_power < param.max_power():
                    # check move noise
                    move_dist = ball_move.r()
                    ball_noise = move_dist * param.ball_rand()

                    max_kick_rand = (
                        wm.self().player_type().kick_rand()
                        * (kick_power / param.max_power())
                        * (current_pos_rate + current_speed_rate)
                    )
                    # move noise is small
                    if (
                        my_noise + ball_noise + max_kick_rand
                    ) * 0.95 < wm.self().player_type().kickable_area() - mid_dist - 0.1:
                        mid_krate = (
                            wm.self().player_type().kick_rate(mid_dist, dir_diff)
                        )
                        # can stop the ball by 1 step kick
                        if (
                            move_dist * param.ball_decay()
                            < param.max_power() * mid_krate
                        ):
                            candidates.append(
                                KeepPoint(mid_pos, mid_krate, DEFAULT_SCORE)
                            )

            # far side point
            far_pos = my_next + unit_pos.set_length_vector(far_dist)
            if far_pos.abs_x() < max_pitch_x and far_pos.abs_y() < max_pitch_y:
                ball_move = far_pos - wm.ball().pos()
                kick_accel = ball_move - wm.ball().vel()
                kick_power = kick_accel.r() / wm.self().kick_rate()

                # can kick to the point by 1 step kick
                if kick_power < param.max_power():
                    # check move noise
                    move_dist = ball_move.r()
                    ball_noise = move_dist * param.ball_rand()
                    max_kick_rand = (
                        wm.self().player_type().kick_rand()
                        * (kick_power / param.max_power())
                        * (current_pos_rate + current_speed_rate)
                    )
                    # move noise is small
                    if (
                        my_noise + ball_noise + max_kick_rand
                    ) * 0.95 < wm.self().player_type().kickable_area() - far_dist - 0.1:
                        far_krate = (
                            wm.self().player_type().kick_rate(far_dist, dir_diff)
                        )
                        # can stop the ball by 1 step kick
                        if move_dist * param.ball_decay():
                            candidates.append(
                                KeepPoint(far_pos, far_krate, DEFAULT_SCORE)
                            )
        return candidates

    """
      \ brief evaluate candidate keep points
      \ param wm  reference to the WorldModel instance
      \ param keep_points reference to the variable container
     """

    def evaluateKeepPoints(self, wm: "WorldModel", keep_points):
        for it in keep_points:
            it.score_ = self.evaluateKeepPoint(wm, it.pos_)
            if it.score_ < DEFAULT_SCORE:
                it.score_ += it.pos_.dist(wm.ball().pos())
            else:
                it.score_ += it.kick_rate_ * 1000.0

    """
      \ brief evaluate the keep point
      \ param wm  reference to the WorldModel instance
      \ param keep_point keep point value
    """

    def evaluateKeepPoint(self, wm: "WorldModel", keep_point: Vector2D):
        # penalty_area = Rect2D(
        #     Vector2D(
        #         ServerParam.i().their_penalty_area_line_x(),
        #         -ServerParam.i().penalty_area_half_width(),
        #     ),
        #     Size2D(
        #         ServerParam.i().penalty_area_length(),
        #         ServerParam.i().penalty_area_width(),
        #     ),
        # )
        ## TODO: hardcoded need to be changed
        penalty_area = Rect2D(
            Vector2D(-20 / 2, -20 / 2),
            Vector2D(20 / 2, 20 / 2),
        )

        consider_dist = (
            ServerParam.i().tackle_dist()
            + ServerParam.i().default_player_speed_max()
            + 1.0
        )
        param = ServerParam.i()
        score = DEFAULT_SCORE

        my_next = wm.self().pos() + wm.self().vel()
        if len(wm.opponents_from_ball()) == 0:
            return score
        for o in wm.opponents_from_ball():
            if o is None or o.player_type() is None:
                continue
            if o.dist_from_ball() > consider_dist:
                break
            if o.pos_count() > 10:
                continue
            if o.is_ghost():
                continue
            if o.is_tackling():
                continue

            player_type = o.player_type()
            opp_next = o.pos() + o.vel()
            control_area = (
                o.player_type().catchable_area()
                if (
                    o.goalie()
                    and penalty_area.contains(o.pos())
                    and penalty_area.contains(keep_point)
                )
                else o.player_type().kickable_area()
            )
            opp_dist = opp_next.dist(keep_point)

            if opp_dist < control_area * 0.5:
                score -= 100.0

            elif opp_dist < control_area + 0.1:
                score -= 50.0

            elif opp_dist < param.tackle_dist() - 0.2:
                score -= 25.0

            if o.body_count() == 0:
                opp_body = o.body()

            elif o.vel().r() > 0.2:  # o.velCount() <= 1 #and
                opp_body = o.vel().th()

            else:
                opp_body = (my_next - opp_next).th()

            #
            # check opponent body line
            #

            opp_line = Line2D(p=opp_next, a=opp_body)
            line_dist = opp_line.dist(keep_point)
            if line_dist < control_area:
                if line_dist < control_area * 0.8:
                    score -= 20.0
                else:
                    score -= 10.0

            player_2_pos = keep_point - opp_next
            player_2_pos.rotate(-opp_body)

            #
            # check tackle probability
            #
            tackle_dist = (
                param.tackle_dist()
                if (player_2_pos.x() > 0.0)
                else param.tackle_back_dist()
            )
            if tackle_dist > 1.0e-5:
                tackle_prob = pow(
                    player_2_pos.abs_x() / tackle_dist, param.tackle_exponent()
                ) + pow(
                    player_2_pos.abs_y() / param.tackle_width(), param.tackle_exponent()
                )
                if tackle_prob < 1.0 and 1.0 - tackle_prob > 0.7:  # success probability
                    score -= 30.0

            #
            # check kick or tackle possibility after dash
            #
            max_accel = (
                param.max_dash_power()
                * player_type.dash_power_rate()
                * player_type.effort_max()
            )

            if (
                player_2_pos.abs_y() < control_area
                and player_2_pos.x() > 0.0
                and (
                    player_2_pos.abs_x() < max_accel
                    or (player_2_pos - Vector2D(max_accel, 0.0)).r()
                    < control_area + 0.1
                )
            ):
                # next kickable
                score -= 20.0
            elif (
                player_2_pos.abs_y() < param.tackle_width() * 0.7
                and player_2_pos.x() > 0.0
                and player_2_pos.x() - max_accel < param.tackle_dist() - 0.25
            ):
                score -= 10.0

        ball_move_dist = (keep_point - wm.ball().pos()).r()
        if ball_move_dist > wm.self().player_type().kickable_area() * 1.6:
            next_ball_dist = my_next.dist(keep_point)
            threshold = wm.self().player_type().kickable_area() - 0.4
            rate = 1.0 - 0.5 * max(0.0, (next_ball_dist - threshold) / 0.4)
            score *= rate
        return score

    """
      \ brief if possible, to face target point
      \ param agent  agent itself
      \ return True if action is performed
    """

    def turnToPoint(self, agent: "PlayerAgent"):
        param = ServerParam.i()
        max_pitch_x = param.keepaway_length() / 2 - 0.2
        max_pitch_y = param.keepaway_width() / 2 - 0.2
        wm = agent.world()
        my_next = wm.self().pos() + wm.self().vel()
        ball_next = wm.ball().pos() + wm.ball().vel()

        if ball_next.abs_x() > max_pitch_x or ball_next.abs_y() > max_pitch_y:
            return False

        my_noise = wm.self().vel().r() * param.player_rand()
        ball_noise = wm.ball().vel().r() * param.ball_rand()

        next_ball_dist = my_next.dist(ball_next)

        if next_ball_dist > (
            wm.self().player_type().kickable_area() - my_noise - ball_noise - 0.15
        ):
            return False

        face_point = Vector2D(0.0, 0.0)
        face_point.x = param.pitch_half_length() - 5.0

        if self._do_turn:
            face_point = self._turn_target_point
        my_inertia = wm.self().inertia_final_point()
        target_angle = (face_point - my_inertia).th()

        if (wm.self().body() - target_angle).abs() < 5.0:
            return False

        score = self.evaluateKeepPoint(wm, ball_next)
        if score < DEFAULT_SCORE:
            return False

        TurnToPoint(face_point, 100).execute(agent)
        return True

    """
      \ brief keep the ball at body front
      \ param  agent itself
      \ return True if action is performed
    """

    def keepFront(self, agent: "PlayerAgent"):
        param = ServerParam.i()
        max_pitch_x = param.keepaway_length() / 2 - 0.2
        max_pitch_y = param.keepaway_width() / 2 - 0.2

        wm = agent.world()
        front_keep_dist = (
            wm.self().player_type().player_size() + param.ball_size() + 0.05
        )

        my_next = wm.self().pos() + wm.self().vel()

        front_pos = my_next + Vector2D.polar2vector(front_keep_dist, wm.self().body())

        if front_pos.abs_x() > max_pitch_x or front_pos.abs_y() > max_pitch_y:
            return False

        ball_move = front_pos - wm.ball().pos()
        kick_accel = ball_move - wm.ball().vel()
        kick_power = kick_accel.r() / wm.self().kick_rate()

        # can kick to the point by 1 step kick
        if kick_power > param.max_power():
            return False

        score = self.evaluateKeepPoint(wm, front_pos)

        if score < DEFAULT_SCORE:
            return False

        agent.do_kick(kick_power, kick_accel.th() - wm.self().body())
        return True

    """
      \ brief keep the ball at reverse point from the kick target point
      \ param  agent itself
    """

    def keepReverse(self, agent: "PlayerAgent"):
        if not self._kick_target_point.is_valid():
            return False

        param = ServerParam.i()
        # max_pitch_x = param.pitch_half_length() - 0.2
        # max_pitch_y = param.pitch_half_width() - 0.2
        max_pitch_x = param.keepaway_length() / 2 - 0.2
        max_pitch_y = param.keepaway_width() / 2 - 0.2
        wm = agent.world()

        my_inertia = wm.self().pos() + wm.self().vel()

        my_noise = wm.self().vel().r() * param.player_rand()
        current_dir_diff_rate = (
            wm.ball().angle_from_self() - wm.self().body()
        ).abs() / 180.0

        current_dist_rate = (
            wm.ball().dist_from_self()
            - wm.self().player_type().player_size()
            - param.ball_size()
        ) / wm.self().player_type().kickable_margin()

        current_pos_rate = 0.5 + 0.25 * (current_dir_diff_rate + current_dist_rate)
        current_speed_rate = 0.5 + 0.5 * (
            wm.ball().vel().r() / (param.ball_speed_max() * param.ball_decay())
        )

        keep_angle = (my_inertia - self._kick_target_point).th()
        dir_diff = (keep_angle - wm.self().body()).abs()
        min_dist = wm.self().player_type().player_size() + param.ball_size() + 0.2

        keep_dist = (
            wm.self().player_type().player_size()
            + wm.self().player_type().kickable_margin() * 0.7
            + param.ball_size()
        )

        while keep_dist > min_dist:
            keep_pos = my_inertia + Vector2D.polar2vector(keep_dist, keep_angle)

            keep_dist -= 0.05
            if keep_pos.abs_x() > max_pitch_x or keep_pos.abs_y() > max_pitch_y:
                continue

            ball_move = keep_pos - wm.ball().pos()
            kick_accel = ball_move - wm.ball().vel()
            kick_power = kick_accel.r() / wm.self().kick_rate()

            if kick_power > param.max_power():
                continue

            move_dist = ball_move.r()
            ball_noise = move_dist * param.ball_rand()
            max_kick_rand = (
                wm.self().player_type().kick_rand()
                * (kick_power / param.max_power())
                * (current_pos_rate + current_speed_rate)
            )

            if (
                my_noise + ball_noise + max_kick_rand
            ) > wm.self().player_type().kickable_area() - keep_dist - 0.1:
                continue

            new_krate = wm.self().player_type().kick_rate(keep_dist, dir_diff)
            if move_dist * param.ball_decay() > new_krate * param.max_power():
                continue

            score = self.evaluateKeepPoint(wm, keep_pos)
            if score >= DEFAULT_SCORE:
                agent.do_kick(kick_power, kick_accel.th() - wm.self().body())
                return True

            return False


class GoToPoint:
    _dir_thr: float

    def __init__(
        self,
        target,
        dist_thr,
        max_dash_power,
        dash_speed=-1.0,
        cycle=100,
        save_recovery=True,
        dir_thr=15.0,
    ):
        self._target = target
        self._dist_thr = dist_thr
        self._max_dash_power = max_dash_power
        self._dash_speed = dash_speed
        self._cycle = cycle
        self._save_recovery = save_recovery
        self._dir_thr = dir_thr
        self._back_mode = False

    def execute(self, agent):
        import pyrusgeom.soccer_math as smath

        if math.fabs(self._max_dash_power) < 0.1 or math.fabs(self._dash_speed) < 0.01:
            agent.do_turn(0)
            return True

        wm: "WorldModel" = agent.world()
        inertia_point: Vector2D = wm.self().inertia_point(self._cycle)
        target_rel: Vector2D = self._target - inertia_point

        target_dist = target_rel.r()
        if target_dist < self._dist_thr:
            agent.do_turn(0.0)
            return False

        self.check_collision(agent)

        if self.do_turn(agent):
            return True

        if self.do_dash(agent):
            return True

        agent.do_turn(0)
        return False

    def do_turn(self, agent):
        import pyrusgeom.soccer_math as smath

        SP = ServerParam

        wm: "WorldModel" = agent.world()

        inertia_pos: Vector2D = wm.self().inertia_point(self._cycle)
        target_rel: Vector2D = self._target - inertia_pos
        target_dist = target_rel.r()
        max_turn = (
            wm.self()
            .player_type()
            .effective_turn(SP.i().max_moment(), wm.self().vel().r())
        )
        turn_moment: AngleDeg = target_rel.th() - wm.self().body()
        if (
            turn_moment.abs() > max_turn
            and turn_moment.abs() > 90.0
            and target_dist < 2.0
            and wm.self().stamina_model().stamina()
            > SP.i().recover_dec_thr_value() + 500.0
        ):
            effective_power = SP.i().max_dash_power() * wm.self().dash_rate()
            effective_back_power = SP.i().min_dash_power() * wm.self().dash_rate()
            if math.fabs(effective_back_power) > math.fabs(effective_power) * 0.75:
                self._back_mode = True
                turn_moment += 180.0

        turn_thr = 180.0
        if self._dist_thr < target_dist:
            turn_thr = AngleDeg.asin_deg(self._dist_thr / target_dist)
        turn_thr = max(self._dir_thr, turn_thr)

        if turn_moment.abs() < turn_thr:
            return False
        return agent.do_turn(turn_moment)

    def do_dash(self, agent):
        import pyrusgeom.soccer_math as smath

        SP = ServerParam
        wm: "WorldModel" = agent.world()

        inertia_pos: Vector2D = wm.self().inertia_point(self._cycle)
        target_rel: Vector2D = self._target - inertia_pos

        accel_angle: AngleDeg = wm.self().body()
        if self._back_mode:
            accel_angle += 180.0

        target_rel.rotate(-accel_angle)
        first_speed = smath.calc_first_term_geom_series(
            target_rel.x(), wm.self().player_type().player_decay(), self._cycle
        )
        first_speed = smath.bound(
            -wm.self().player_type().player_speed_max(),
            first_speed,
            wm.self().player_type().player_speed_max(),
        )
        if self._dash_speed > 0.0:
            if first_speed > 0.0:
                first_speed = min(first_speed, self._dash_speed)
            else:
                first_speed = max(first_speed, -self._dash_speed)
        rel_vel = wm.self().vel()
        rel_vel.rotate(-accel_angle)
        required_accel = first_speed - rel_vel.x()
        if math.fabs(required_accel) < 0.05:
            return False
        dash_power = required_accel / wm.self().dash_rate()
        dash_power = min(dash_power, self._max_dash_power)
        if self._back_mode:
            dash_power = -dash_power
        dash_power = SP.i().normalize_dash_power(dash_power)
        # TODO check stamina check for save recovery
        return agent.do_dash(dash_power)

    def check_collision(self, agent):
        SP = ServerParam
        wm: "WorldModel" = agent.world()

        collision_dist = (
            wm.self().player_type().player_size() + SP.i().goal_post_radius() + 0.2
        )

        goal_post_l = Vector2D(
            -SP.i().keepaway_length() / 2 + SP.i().goal_post_radius(),
            -SP.i().keepaway_width() / 2 - SP.i().goal_post_radius(),
        )
        goal_post_r = Vector2D(
            -SP.i().keepaway_length() / 2 + SP.i().goal_post_radius(),
            +SP.i().keepaway_width() / 2 + SP.i().goal_post_radius(),
        )

        dist_post_l = wm.self().pos().dist2(goal_post_l)
        dist_post_r = wm.self().pos().dist2(goal_post_r)

        nearest_post = goal_post_l
        if dist_post_l > dist_post_r:
            nearest_post = goal_post_r

        dist_post = min(dist_post_l, dist_post_r)
        if dist_post > collision_dist + wm.self().player_type().real_speed_max() + 0.5:
            return

        post_circle = Circle2D(nearest_post, collision_dist)
        move_line = Segment2D(wm.self().pos(), self._target)
        if len(post_circle.intersection(move_line)) == 0:
            return

        post_angle: AngleDeg = AngleDeg((nearest_post - wm.self().pos()).th())
        new_target: Vector2D = nearest_post

        if post_angle.is_left_of(wm.self().body()):
            new_target += Vector2D.from_polar(collision_dist + 0.1, post_angle + 90.0)
        else:
            new_target += Vector2D.from_polar(collision_dist + 0.1, post_angle - 90.0)

        self._target = new_target


class ScanField(BodyAction):
    

    def __init__(self):
        pass

    def execute(self, agent: "PlayerAgent"):
        log.debug_client().add_message("ScanField/")
        wm = agent.world()
        # if not wm.self().pos_valid():
        #     agent.do_turn(60.0)
        #     agent.set_neck_action(NeckTurnToRelative(0))
        #     return True

        # if wm.ball().pos_valid():
        #     self.scan_all_field(agent)
        #     return True

        self.find_ball(agent)
        return True

    def find_ball(self, agent: "PlayerAgent"):

        wm = agent.world()
        # print(wm.ball().pos())
        # print("find ball/")

        if agent.effector().queued_next_view_width() is not ViewWidth.WIDE:
            agent.set_view_action(ViewWide())

        my_next = wm.self().pos() + wm.self().vel()
        face_angle = (
            (wm.ball().seen_pos() - my_next).th()
            if wm.ball().seen_pos().is_valid()
            else (my_next * -1).th()
        )

        search_flag = wm.ball().lost_count() // 3
        if search_flag % 2 == 1:
            face_angle += 180.0

        face_point = my_next + Vector2D(r=10, a=face_angle)
        NeckBodyToPoint(face_point).execute(agent)

    def scan_all_field(self, agent: "PlayerAgent"):
        wm = agent.world()
        # print(wm.ball().pos())
        # print("find ball/")

        if agent.effector().queued_next_view_width() is not ViewWidth.WIDE:
            agent.set_view_action(ViewWide())

        turn_moment = (
            wm.self().view_width().width()
            + agent.effector().queued_next_view_width().width()
        )
        turn_moment /= 2
        agent.do_turn(turn_moment)
        agent.set_neck_action(NeckTurnToRelative(wm.self().neck()))


class NeckScanField(NeckAction):
    DEBUG = True

    INVALID_ANGLE = -360.0

    _last_calc_time = GameTime(0, 0)
    _last_calc_view_width = ViewWidth.NORMAL
    _cached_target_angle = 0.0

    def __init__(self):
        super().__init__()

    def execute(self, agent: "PlayerAgent"):
        log.debug_client().add_message("NeckScanField/")
        wm = agent.world()
        ef = agent.effector()

        if (
            NeckScanField._last_calc_time == wm.time()
            and NeckScanField._last_calc_view_width != ef.queued_next_view_width()
        ):
            agent.do_turn_neck(
                NeckScanField._cached_target_angle
                - ef.queued_next_self_body()
                - wm.self().neck()
            )
            return True

        NeckScanField._last_calc_time = wm.time().copy()
        NeckScanField._last_calc_view_width = ef.queued_next_view_width()

        angle = self.calc_angle_for_wide_pitch_edge(agent)
        if angle != NeckScanField.INVALID_ANGLE:
            NeckScanField._cached_target_angle = angle
            agent.do_turn_neck(
                AngleDeg(NeckScanField._cached_target_angle)
                - ef.queued_next_self_body()
                - wm.self().neck()
            )
            return True

        existed_ghost = False
        for p in wm.all_players():
            if p.is_ghost() and p.dist_from_self() < 30:
                existed_ghost = True
                break

        if NeckScanField.DEBUG:
            log.sw_log().world().add_text(f"(NSF EXE) existed_ghost={existed_ghost}")
            log.sw_log().world().add_text(f"(NSF EXE) dir_counts={wm._dir_count}")

        if not existed_ghost:
            angle = NeckScanPlayers.get_best_angle(agent)
            if angle != NeckScanField.INVALID_ANGLE:
                NeckScanField._cached_target_angle = angle
                agent.do_turn_neck(
                    AngleDeg(NeckScanField._cached_target_angle)
                    - ef.queued_next_self_body()
                    - wm.self().neck()
                )
                return True

        gt = wm.game_mode().type()
        consider_patch = gt is GameModeType.PlayOn or (
            not gt.is_ind_free_kick()
            and not gt.is_back_pass()
            and wm.ball().dist_from_self()
            < wm.self().player_type().player_size() + 0.15
        )
        angle = self.calc_angle_default(agent, consider_patch)

        if consider_patch and (AngleDeg(angle) - wm.self().face()).abs() < 5:
            angle = self.calc_angle_default(agent, False)

        NeckScanField._cached_target_angle = angle
        agent.do_turn_neck(
            AngleDeg(NeckScanField._cached_target_angle)
            - ef.queued_next_self_body()
            - wm.self().neck()
        )

        return True

    def calc_angle_default(self, agent: "PlayerAgent", consider_patch: bool):
        SP = ServerParam.i()
        pitch_rect = Rect2D(
            Vector2D(-SP.pitch_half_length(), -SP.pitch_half_width()),
            Size2D(SP.pitch_length(), SP.pitch_width()),
        )

        expand_pitch_rect = Rect2D(
            Vector2D(-SP.pitch_half_length() - 3, -SP.pitch_half_width() - 3),
            Size2D(SP.pitch_length() + 6, SP.pitch_width() + 6),
        )

        goalie_rect = Rect2D(
            Vector2D(SP.pitch_half_length() - 3, -15.0), Size2D(10, 30)
        )

        wm = agent.world()
        ef = agent.effector()

        next_view_width = ef.queued_next_view_width().width()

        left_start = (
            ef.queued_next_self_body() + SP.min_neck_angle() - (next_view_width * 0.5)
        )
        scan_range = SP.max_neck_angle() - SP.min_neck_angle() + next_view_width
        shrinked_next_view_width = next_view_width - WorldModel.DIR_STEP * 1.5
        sol_angle = left_start + scan_range * 0.5
        if scan_range < shrinked_next_view_width:
            return sol_angle.degree()

        tmp_angle = left_start.copy()
        size_of_view_width = round(shrinked_next_view_width / WorldModel.DIR_STEP)
        dir_count: list[int] = []

        for _ in range(size_of_view_width):
            dir_count.append(wm.dir_count(tmp_angle))

            if NeckScanField.DEBUG:
                log.sw_log().world().add_text(f"(NSF CAD) dir_count={dir_count[-1]}")

            tmp_angle += WorldModel.DIR_STEP

        max_count_sum = 0
        add_dir = shrinked_next_view_width

        my_next = ef.queued_next_self_pos()

        while True:
            tmp_count_sum = sum(dir_count)
            angle = tmp_angle - shrinked_next_view_width * 0.5

            if tmp_count_sum > max_count_sum:
                update = True
                if consider_patch:
                    face_point = my_next + Vector2D(r=20, a=angle)
                    if not pitch_rect.contains(face_point) and not goalie_rect.contains(
                        face_point
                    ):
                        update = False

                    if update:
                        left_face_point = my_next + Vector2D(
                            r=20, a=angle - next_view_width * 0.5
                        )
                        if not expand_pitch_rect.contains(
                            left_face_point
                        ) and not goalie_rect.contains(left_face_point):
                            update = False

                    if update:
                        right_face_point = my_next + Vector2D(
                            r=20, a=angle + next_view_width * 0.5
                        )
                        if not expand_pitch_rect.contains(
                            right_face_point
                        ) and not goalie_rect.contains(right_face_point):
                            update = False

                if update:
                    sol_angle = angle
                    max_count_sum = tmp_count_sum
            dir_count = dir_count[1:]
            add_dir += WorldModel.DIR_STEP
            tmp_angle += WorldModel.DIR_STEP
            dir_count.append(wm.dir_count(tmp_angle))

            if add_dir > scan_range:
                break
        return sol_angle.degree()

    def calc_angle_for_wide_pitch_edge(self, agent: "PlayerAgent"):
        SP = ServerParam.i()
        wm = agent.world()
        ef = agent.effector()

        if ef.queued_next_view_width() is not ViewWidth.WIDE:
            return NeckScanField.INVALID_ANGLE

        gt = wm.game_mode().type()
        if (
            gt is not GameModeType.PlayOn
            and not gt.is_goal_kick()
            and wm.ball().dist_from_self() > 2
        ):
            return NeckScanField.INVALID_ANGLE

        next_self_pos = wm.self().pos() + wm.self().vel()
        pitch_x_thr = SP.pitch_half_length() - 15.0
        pitch_y_thr = (
            SP.pitch_half_length() - 10.0
        )  # TODO WIDTH MAYBE(it was on librcsc tho...)

        target_angle = NeckScanField.INVALID_ANGLE

        if next_self_pos.abs_y() > pitch_y_thr:
            target_pos = Vector2D(SP.pitch_half_length() - 7.0, 0.0)
            target_pos.set_x(
                min(target_pos.x(), target_pos.x() * 0.7 * next_self_pos.x() * 0.3)
            )

            if next_self_pos.abs_y() > pitch_y_thr:
                target_angle = (target_pos - next_self_pos).th().degree()

        if next_self_pos.abs_x() > pitch_x_thr:
            target_pos = Vector2D(SP.pitch_half_length() * 0.5, 0)

            if next_self_pos.abs_x() > pitch_x_thr:
                target_angle = (target_pos - next_self_pos).th().degree()

        return target_angle


class NeckBodyToPoint(NeckAction):
    def __init__(self, point: Vector2D, angle_buf: Union[AngleDeg, float] = 5.0):
        super().__init__()
        self._point = point.copy()
        self._angle_buf = float(angle_buf)

    def execute(self, agent: "PlayerAgent"):
        log.debug_client().add_message("BodyToPoint/")
        SP = ServerParam.i()
        wm = agent.world()

        angle_buf = bound(0.0, self._angle_buf, 180.0)

        my_next = wm.self().pos() + wm.self().vel()
        target_rel_angle = (self._point - my_next).th() - wm.self().body()

        if (
            SP.min_neck_angle() + angle_buf
            < target_rel_angle.degree()
            < SP.max_neck_angle() - angle_buf
        ):
            agent.do_turn(0.0)
            agent.set_neck_action(NeckTurnToRelative(target_rel_angle))
            return True

        max_turn = (
            wm.self().player_type().effective_turn(SP.max_moment(), wm.self().vel().r())
        )
        if target_rel_angle.abs() < max_turn:
            agent.do_turn(target_rel_angle)
            agent.set_neck_action(NeckTurnToRelative(0.0))
            return True

        agent.do_turn(target_rel_angle)
        if target_rel_angle.degree() > 0.0:
            target_rel_angle -= max_turn
        else:
            target_rel_angle += max_turn

        agent.set_neck_action(NeckTurnToRelative(target_rel_angle))
        return True


class NeckTurnToBallOrScan(NeckAction):
    def __init__(self, count_thr: int = 5):
        super().__init__()
        self._count_thr = count_thr

    def execute(self, agent: "PlayerAgent"):
        log.debug_client().add_message("TurnToBallOrScan/")
        wm = agent.world()
        ef = agent.effector()
        SP = ServerParam.i()

        if wm.ball().pos_count() <= self._count_thr:
            return NeckScanField().execute(agent)

        ball_next = ef.queued_next_ball_pos()
        my_next = ef.queued_next_self_pos()
        # print("neck turn to ball or scan", wm.ball()._seen_pos)

        if (
            wm.ball().pos_count() <= 0
            and not wm.kickable_opponent()
            and not wm.kickable_teammate()
            and my_next.dist(ball_next) < SP.visible_distance() - 0.2
        ):
            return NeckScanField().execute(agent)

        my_next_body = ef.queued_next_self_body()
        next_view_width = ef.queued_next_view_width().width()

        if (
            (ball_next - my_next).th() - my_next_body
        ).abs() > SP.max_neck_angle() + next_view_width * 0.5 + 2:
            return NeckScanField().execute(agent)

        # print("here")
        return NeckTurnToBall().execute(agent)


class SmartKick(BodyAction):
    debug_print_DEBUG: bool = True  # debug_prints IN SMARTKICK

    def __init__(self, target_point: Vector2D, first_speed, first_speed_thr, max_step):
        super().__init__()
        # target point where the ball should move to
        self._target_point = target_point
        # desired ball first speed
        self._first_speed: float = first_speed
        # threshold value for the ball first speed
        self._first_speed_thr: float = first_speed_thr
        # maximum number of kick steps
        self._max_step: int = max_step
        # result kick sequence holder
        self._sequence = Sequence()

    def execute(self, agent: "PlayerAgent"):
        log.sw_log().kick().add_text("Body_SmartKick")
        log.os_log().debug(
            f"c{agent.world().time().cycle()}kick{self._target_point} {self._first_speed}"
        )
        log.sw_log().kick().add_text(
            f"c{agent.world().time().cycle()}kick{self._target_point} {self._first_speed}"
        )
        wm = agent.world()
        if not wm.self().is_kickable():
            if SmartKick.debug_print_DEBUG:
                log.os_log().info("----- NotKickable -----")
                log.sw_log().kick().add_text("not kickable")
            return False
        if not wm.ball().vel_valid():
            if SmartKick.debug_print_DEBUG:
                log.os_log().info("-- NonValidBall -> StopBall --")
                log.sw_log().kick().add_text("unknown ball vel")
            return StopBall().execute(agent)
        first_speed = min(self._first_speed, ServerParam.i().ball_speed_max())
        first_speed_thr = max(0.0, self._first_speed_thr)
        max_step = max(1, self._max_step)
        ans = KickTable.instance().simulate(
            wm,
            self._target_point,
            first_speed,
            first_speed_thr,
            max_step,
            self._sequence,
        )
        if ans[0] and SmartKick.debug_print_DEBUG:
            log.os_log().info(
                f"Smart kick : {ans[0]} seq -> speed : {ans[1].speed_} power : {ans[1].power_} score : {ans[1].score_} flag : {ans[1].flag_} next_pos : {ans[1].pos_list_[0]} {len(ans[1].pos_list_)} step {ans[1].pos_list_}"
            )
            log.sw_log().kick().add_text(
                f"Smart kick : {ans[0]} seq -> speed : {ans[1].speed_} power : {ans[1].power_} score : {ans[1].score_} flag : {ans[1].flag_} next_pos : {ans[1].pos_list_[0]} {len(ans[1].pos_list_)} step {ans[1].pos_list_}"
            )

        if ans[0]:
            self._sequence = ans[1]
            if self._sequence.speed_ >= first_speed_thr:  # double check
                vel = self._sequence.pos_list_[0] - wm.ball().pos()
                kick_accel = vel - wm.ball().vel()
                if SmartKick.debug_print_DEBUG:
                    log.os_log().debug(
                        f"Kick Vel : {vel}, Kick Power : {kick_accel.r() / wm.self().kick_rate()}, Kick Angle : {kick_accel.th() - wm.self().body()}"
                    )
                    log.sw_log().kick().add_text(
                        f"Kick Vel : {vel}, Kick Power : {kick_accel.r() / wm.self().kick_rate()}, Kick Angle : {kick_accel.th() - wm.self().body()}"
                    )

                agent.do_kick(
                    kick_accel.r() / wm.self().kick_rate(),
                    kick_accel.th() - wm.self().body(),
                )
                if SmartKick.debug_print_DEBUG:
                    log.os_log().debug(
                        f"----------------#### Player Number {wm.self().unum()} 'DO_KICK'ed in SmartKick at Time: {wm.time().cycle()} ####----------------"
                    )
                    log.sw_log().kick().add_text(
                        f"----------------#### Player Number {wm.self().unum()} 'DO_KICK'ed in SmartKick at Time: {wm.time().cycle()} ####----------------"
                    )
                return True

        # failed to search the kick sequence
        log.sw_log().kick().add_text("----->>>>>Hold Ball")
        HoldBall(False, self._target_point, self._target_point).execute(agent)
        return False

    def sequence(self):
        return self._sequence


class NeckScanPlayers(NeckAction):
    DEBUG = True

    INVALID_ANGLE = -360.0

    _last_calc_time = GameTime(0, 0)
    _last_calc_view_width = ViewWidth.NORMAL
    _cached_target_angle = 0.0
    _last_calc_min_neck_angle = 0.0
    _last_calc_max_neck_angle = 0.0

    def __init__(
        self,
        min_neck_angle: float = INVALID_ANGLE,
        max_neck_angle: float = INVALID_ANGLE,
    ):
        super().__init__()

        self._min_neck_angle = min_neck_angle
        self._max_neck_angle = max_neck_angle

    def execute(self, agent: "PlayerAgent"):
        log.debug_client().add_message("ScanPlayers/")
        wm = agent.world()
        ef = agent.effector()

        if NeckScanPlayers.DEBUG:
            log.sw_log().world().add_text(
                f"(NSP exe) last={NeckScanPlayers._last_calc_time}|wm-time={wm.time()}"
            )

        if (
            NeckScanPlayers._last_calc_time != wm.time()
            or NeckScanPlayers._last_calc_view_width != ef.queued_next_view_width()
            or abs(NeckScanPlayers._last_calc_min_neck_angle - self._min_neck_angle)
            > 1.0e-3
            or abs(NeckScanPlayers._last_calc_max_neck_angle - self._max_neck_angle)
            > 1.0e-3
        ):
            NeckScanPlayers._last_calc_time = wm.time().copy()
            NeckScanPlayers._last_calc_view_width = ef.queued_next_view_width()
            NeckScanPlayers._last_calc_min_neck_angle = self._min_neck_angle
            NeckScanPlayers._last_calc_max_neck_angle = self._max_neck_angle

            NeckScanPlayers._cached_target_angle = NeckScanPlayers.get_best_angle(
                agent, self._min_neck_angle, self._max_neck_angle
            )

        if NeckScanPlayers._cached_target_angle == NeckScanPlayers.INVALID_ANGLE:
            return NeckScanField().execute(agent)

        target_angle = AngleDeg(NeckScanPlayers._cached_target_angle)
        agent.do_turn_neck(
            target_angle
            - ef.queued_next_self_body().degree()
            - wm.self().neck().degree()
        )
        return True

    @staticmethod
    def get_best_angle(
        agent: "PlayerAgent",
        min_neck_angle: float = INVALID_ANGLE,
        max_neck_angle: float = INVALID_ANGLE,
    ):
        wm = agent.world()

        if len(wm.all_players()) < 22:
            if NeckScanPlayers.DEBUG:
                log.sw_log().world().add_text(
                    f"(NSP GBA) all players are less than 22, n={len(wm.all_players())}"
                )
            return NeckScanPlayers.INVALID_ANGLE

        SP = ServerParam.i()
        ef = agent.effector()

        next_self_pos = ef.queued_next_self_pos()
        next_self_body = ef.queued_next_self_body()
        view_width = ef.queued_next_view_width().width()
        view_half_width = view_width / 2

        neck_min = (
            SP.min_neck_angle()
            if min_neck_angle == NeckScanPlayers.INVALID_ANGLE
            else bound(SP.min_neck_angle(), min_neck_angle, SP.max_neck_angle())
        )
        neck_max = (
            SP.max_neck_angle()
            if max_neck_angle == NeckScanPlayers.INVALID_ANGLE
            else bound(SP.min_neck_angle(), max_neck_angle, SP.max_neck_angle())
        )
        neck_step = max(1, (neck_max - neck_min) / 36)

        best_dir = NeckScanPlayers.INVALID_ANGLE
        best_score = 0.0

        dirs = [neck_min + d * neck_step for d in range(36)]
        for dir in dirs:
            left_angle = next_self_body + (dir - (view_half_width - 0.01))
            right_angle = next_self_body + (dir + (view_half_width - 0.01))

            score = NeckScanPlayers.calculate_score(
                wm, next_self_pos, left_angle, right_angle
            )  # TODO IMP FUNC

            if NeckScanPlayers.DEBUG:
                log.sw_log().world().add_text(
                    f"body={next_self_body}|dir={dir}|score={score}"
                )

            if score > best_score:
                best_dir = dir
                best_score = score

        if best_dir == NeckScanPlayers.INVALID_ANGLE or abs(best_score) < 1.0e-5:
            return NeckScanPlayers.INVALID_ANGLE

        angle = next_self_body + best_dir
        return angle.degree()

    @staticmethod
    def calculate_score(
        wm: WorldModel,
        next_self_pos: Vector2D,
        left_angle: AngleDeg,
        right_angle: AngleDeg,
    ):
        score = 0.0
        view_buffer = 90.0

        it = wm.intercept_table()
        our_min = min(it.self_reach_cycle(), it.teammate_reach_cycle())
        opp_min = it.opponent_reach_cycle()

        our_ball = our_min <= opp_min

        reduced_left_angle = left_angle + 5.0
        reduced_right_angle = right_angle - 5.0

        for p in wm.all_players():
            if p.is_self():
                continue

            pos = p.pos() + p.vel()
            angle = (pos - next_self_pos).th()

            if not angle.is_right_of(reduced_left_angle) or not angle.is_left_of(
                reduced_right_angle
            ):
                continue

            if p.ghost_count() >= 5:
                continue

            pos_count = p.seen_pos_count()
            if p.is_ghost() and p.ghost_count() % 2 == 1:
                pos_count = min(2, pos_count)

            pos_count += 1

            if our_ball:
                if p.side() == wm.our_side() and (
                    p.pos().x() > wm.ball().pos().x() - 10 or p.pos().x() > 30
                ):
                    pos_count *= 2

            keepaway.base_val = pos_count**2
            rate = exp(-(p.dist_from_self() ** 2) / (2 * (20**2)))

            score += keepaway.base_val * rate
            buf = min((angle - left_angle).abs(), (angle - right_angle).abs())

            if buf < view_buffer:
                view_buffer = buf

        rate = 1 + view_buffer / 90
        score *= rate
        return score
