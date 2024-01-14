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

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from lib.player.world_model import WorldModel
    from lib.player.object_player import PlayerObject


class Tools:
    @staticmethod
    def predict_player_turn_cycle(
        ptype: PlayerType,
        player_body: AngleDeg,
        player_speed,
        target_dist,
        target_angle: AngleDeg,
        dist_thr,
        use_back_dash,
    ):
        sp = ServerParam.i()
        n_turn = 0
        angle_diff = (target_angle - player_body).abs()

        if (
            use_back_dash
            and target_dist < 5.0
            and angle_diff > 90.0
            and sp.min_dash_power() < -sp.max_dash_power() + 1.0
        ):
            angle_diff = abs(angle_diff - 180.0)

        turn_margin = 180.0
        if dist_thr < target_dist:
            turn_margin = max(15.0, AngleDeg.asin_deg(dist_thr / target_dist))

        speed = float(player_speed)
        while angle_diff > turn_margin:
            angle_diff -= ptype.effective_turn(sp.max_moment(), speed)
            speed *= ptype.player_decay()
            n_turn += 1

        return n_turn

    @staticmethod
    def predict_kick_count(
        wm: "WorldModel", kicker, first_ball_speed, ball_move_angle: AngleDeg
    ):
        if (
            wm.game_mode().type() != GameModeType.PlayOn
            and not wm.game_mode().is_penalty_kick_mode()
        ):
            return 1

        if kicker == wm.self().unum() and wm.self().is_kickable():
            max_vel = calc_max_velocity(
                ball_move_angle, wm.self().kick_rate(), wm.ball().vel()
            )
            if max_vel.r2() >= pow(first_ball_speed, 2):
                return 1
        if first_ball_speed > 2.5:
            return 3
        elif first_ball_speed > 1.5:
            return 2
        return 1

    @staticmethod
    def estimate_min_reach_cycle(
        player_pos: Vector2D,
        player_speed_max,
        target_first_point: Vector2D,
        target_move_angle: AngleDeg,
    ):
        target_to_player: Vector2D = (player_pos - target_first_point).rotated_vector(
            -target_move_angle
        )
        if target_to_player.x() < -1.0:
            return -1
        else:
            return max(1, int(target_to_player.abs_y() / player_speed_max))

    @staticmethod
    def get_nearest_teammate(
        wm: "WorldModel", position: Vector2D, players: list["PlayerObject"] = None
    ):
        if players is None:
            players = wm.teammates()
        best_player: "PlayerObject" = None
        min_dist2 = 1000
        for player in players:
            d2 = player.pos().dist2(position)
            if d2 < min_dist2:
                min_dist2 = d2
                best_player = player

        return best_player

    @staticmethod
    def estimate_virtual_dash_distance(player: "PlayerObject"):
        pos_count = min(10, player.pos_count(), player.seen_pos_count())
        max_speed = player.player_type().real_speed_max() * 0.8

        d = 0.0
        for i in range(pos_count):
            d += max_speed * math.exp(-(i**2) / 15)

        return d

    @staticmethod
    def get_end_speed_from_first_speed(end_speed, cycles, decay):
        SS = ServerParam.i()
        if decay < 0.0:
            decay = SS.ball_decay()
        return end_speed * math.pow(1.0 / SS.ball_decay(), cycles)

    @staticmethod
    def get_kick_travel(distance, target_speed):
        SS = ServerParam.i()
        if target_speed < 0.0001:
            return sm.calc_first_term_geom_series(distance, SS.ball_decay())
        steps = sm.calc_length_geom_series(
            target_speed, 1.0 / SS.ball_decay(), distance
        )

        sp = Tools.get_end_speed_from_first_speed(target_speed, steps, SS.ball_decay())
        # print("speed first : ", sp)
        return sp

    @staticmethod
    def predict_stamina_after_dash(dash_power, stamina):
        sta = stamina.stamina()
        eff = stamina.effort()
        rec = stamina.recovery()
        #  // double negative value when dashed backwards
        sta -= dash_power if dash_power > 0.0 else -2 * dash_power
        if sta < 0:
            sta = 0
        # // stamina below recovery threshold, lower recovery
        if (
            sta <= ServerParam.i().recover_dec_thr() * ServerParam.i().stamina_max()
            and rec > ServerParam.i().recover_min()
        ):
            rec -= ServerParam.i().recover_dec()
        # // stamina below effort decrease threshold, lower effort
        if (
            sta <= ServerParam.i().effort_dec_thr() * ServerParam.i().stamina_max()
            and eff > ServerParam.i().effort_min()
        ):
            eff -= ServerParam.i().effort_dec()
        # // stamina higher than effort incr threshold, raise effort and check maximum
        if (
            sta >= ServerParam.i().effort_inc_thr() * ServerParam.i().stamina_max()
            and eff < 1.0
        ):
            eff += ServerParam.i().effort_inc()
            if eff > 1.0:
                eff = 1.0
        # // increase stamina with (new) recovery value and check for maximum
        sta += rec * ServerParam.i().stamina_inc_max()
        if sta > ServerParam.i().stamina_max():
            sta = ServerParam.i().stamina_max()
        stamina.set_stamina(sta)
        stamina.set_effort(eff)
        stamina.set_recovery(rec)

    @staticmethod
    def predict_state_after_dash(p, dash_power, pos, vel, stamina, direction):
        """Predict the state of the object after dash."""

        SP = ServerParam.i()
        # get acceleration associated with actual power
        effort = stamina.effort() if stamina else p.effort_max()
        acc = dash_power * p.player_type().dash_power_rate() * effort

        # add it to the velocity; negative acceleration in backward direction
        if acc > 0:
            vel += Vector2D.polar2vector(acc, direction)
        else:
            vel += Vector2D.polar2vector(abs(acc), direction + 180)

        # check if velocity doesn't exceed maximum speed
        if vel.r() > SP.default_player_speed_max():
            vel.set_r(SP.player_speed_max())

        # add velocity to current global position and decrease velocity
        pos += vel
        vel *= p.player_type().player_decay()
        # print("pos: ", pos)
        # print("vel: ", vel)

        if stamina:
            stamina.simulate_dash(p.player_type(), dash_power)
            # Tools.predict_stamina_after_dash(dash_power, stamina)

    @staticmethod
    def predict_pos_after_n_cycles(p, cycles, dash_power):
        """Returns the position of player object after n cycles."""

        SP = ServerParam.i()
        # if p == BallObject:
        #     d = Geometry.get_sum_geom_series(
        #         vel.r(),
        #         SP.ball_decay(),
        #         cycles,
        #     )
        #     pos += Vector2D(d, vel.th(), POLAR)
        #     vel *= math.pow(SP.ball_decay(),cycles)

        # if p == ptype.player_type:
        update = True
        ptype = p.player_type()
        direction = p.body()
        # print("direction: ", direction)
        stamina = p.stamina_model()

        for i in range(cycles):
            Tools.predict_state_after_dash(
                p, dash_power, p.pos(), p.vel(), stamina, direction
            )
        if update:
            pos = p.pos()
            vel = p.vel()
        return pos

    @staticmethod
    def predict_ball_after_command(wm: "WorldModel", command, pos, vel):
        ball_pos = wm.ball().pos()
        ball_vel = wm.ball().vel()
        if command.type() == CommandType.KICK:
            kick_angle = command.kick_dir()
            power = command.kick_power()
            angle = AngleDeg.normalize_angle(kick_angle + wm.self().body().degree())
            ball_vel += Vector2D.polar2vector(
                wm.self().player_type().kick_power_rate() * power, angle
            )
            if ball_vel.r() > ServerParam.i().ball_speed_max():
                ball_vel.set_length(ServerParam.i().ball_speed_max())
            # print("ang: ", angle, "kick_rate: ", wm.self().player_type().kick_power_rate())
            # print("update for kick: ", power, angle)
        ball_pos += ball_vel
        ball_vel *= ServerParam.i().ball_decay()
        return ball_pos, ball_vel

    #### Keepaway Utility ####
    @staticmethod
    def get_in_set_in_cone(wm: "WorldModel", radius, pos_from, pos_to):
        """Returns the number of players in the given set in the cone from posFrom to posTo with the given radius."""
        conf_threshold = 0.88
        line_segments = Segment2D(pos_from, pos_to)
        count = 0
        for p in wm._all_players:
            if p.pos_valid():
                pos = p.pos()
                pos_on_line = line_segments.nearest_point(pos)
                ## projection not right yet . line.isInBetween(posOnLine, start, end)
                if (
                    (pos_on_line.dist(pos) < radius * pos_on_line.dist(pos_from))
                    and (line_segments.projection(pos_on_line))
                    and (pos_from.dist(pos) < pos_from.dist(pos_to))
                ):
                    count += 1
        return count
    
    @staticmethod
    def congestion(wm: "WorldModel", point, consider_me):
        """Returns the congestion at the given position."""
        congest = 0
        for p in wm._teammates:
            if p.pos_valid() and p.pos() != point:
                congest += 1 / p.pos().dist(point)

        for p in wm._opponents:
            if p.pos_valid():
                congest += 1 / p.pos().dist(point)
        return congest


    @staticmethod
    def least_congested_point_for_pass_in_rectangle(rect: Rect2D, pos_from):
        """Returns the least congested point for a pass in the given rectangle."""

        x_granularity = 5  # 5 samples by 5 samples
        y_granularity = 5
        x_buffer = 0.15  # 15% border on each side
        y_buffer = 0.15
        size = rect.size()
        length = size.length()
        width = size.width()
        x_mesh = length * (1 - 2 * x_buffer) / (x_granularity - 1)
        y_mesh = width * (1 - 2 * y_buffer) / (y_granularity - 1)

        start_x = rect.bottom_left().x() + x_buffer * length
        start_y = rect.top_left().y() + y_buffer * width

        x = start_x
        y = start_y

        best_congestion = 1000
        point = Vector2D(x, y)
        tmp = None

        for i in range(x_granularity):
            for j in range(y_granularity):
                point = Vector2D(x, y)
                # print("point", point)
                tmp = Tools.congestion(wm, point, True)
                if (
                    tmp < best_congestion
                    and Tools.get_in_set_in_cone(wm, 0.3, pos_from, point) == 0
                ):
                    best_congestion = tmp
                    best_point = point
                y += y_mesh
            x += x_mesh
            y = start_y

        if best_congestion == 1000:
            # take the point out of the rectangle -- meaning no point was valid.
            best_point = rect.center()
        return best_point
    


    # @staticmethod
    # def predict_pos_after_command(wm: "WorldModel", command):

    # @staticmethod
    # def predict_state_after_dash(
    #     dash_power,
    #     pos: Vector2D,
    #     vel: Vector2D,
    #     stamina,
    #     d_direction,
    #     p : "PlayerObject",
    # ):
    #     SS = ServerParam.i()

    #     d_effort = stamina.get_effort() if stamina else p.stamina_model().get_effort()
    #     d_acc = dash_power * SS.dash_power_rate() * d_effort

    #     # add it to the velocity; negative acceleration in backward direction
    #     if d_acc > 0:
    #         vel += Vector2D.polar2vector(d_acc, d_direction)
    #     else:
    #         vel += Vector2D.polar2vector(abs(d_acc), Vector2D.normalize_angle(d_direction + 180))

    #     # check if velocity doesn't exceed maximum speed
    #     if vel.r() > SS.default_player_speed_max():
    #         vel.set_length(SS.default_player_speed_max())

    #     # add velocity to current global position and decrease velocity
    #     pos += vel
    #     vel *= p.player_type().player_decay()

    #     # if stamina is provided, predict its value after dash
    # if stamina:
    #     predict_stamina_after_dash(d_actual_power, stamina)

    # @staticmethod
    # def predict_stamina_after_dash(dash_power):
    #     SS = ServerParam.i()
    #     sta = me.stamina_model()
    #     eff = sta.effort()
    #     rec = True

    #     # double negative value when dashed backwards
    #     sta -= dash_power if dash_power > 0.0 else -2 * dash_power
    #     if sta < 0:
    #         sta = 0

    #     # stamina below recovery threshold, lower recovery
    #     if sta <= SS.recover_dec_thr * SS.stamina_max and rec > SS.recover_min:
    #         rec -= SS.recover_dec

    #     # stamina below effort decrease threshold, lower effort
    #     if sta <= SS.effort_dec_thr * SS.stamina_max and eff > SS.effort_min:
    #         eff -= SS.effort_dec

    #     # stamina higher than effort increase threshold, raise effort and check maximum
    #     if sta >= SS.effort_inc_thr * SS.stamina_max and eff < 1.0:
    #         eff += SS.effort_inc
    #         if eff > 1.0:
    #             eff = 1.0

    #     # increase stamina with (new) recovery value and check for maximum
    #     sta += rec * SS.stamina_inc_max
    #     if sta > SS.stamina_max:
    #         sta = SS.stamina_max

    #     stamina.set_stamina(sta)
    #     stamina.set_effort(eff)
    #     stamina.set_recovery(rec)

    # @staticmethod
    # def estimate_position(
    #     player: "PlayerObject",
    #     cycles,
    #     dash_power,
    #     pos: Vector2D,
    #     vel: Vector2D,
    # ):

    #     vel = wm.self()._vel if vel is None else vel
    #     pos = wm.self()._pos if pos is None else pos

    #     d_direction = 0.0
    #     stamina = wm.self().stamina_model()

    #     if player:
    #         d_direction = player.body()
    #         stamina = player.stamina_model()
    #     elif wm.self().time() > wm.self().last_dash_time() + 2:
    #         d_direction = wm.self().body()

    #     for i in range(int(cycles)):
    #         predict_state_after_dash(
    #             dash_power, pos, vel, stamina, d_direction, obj
    #         )

    #     if pos not None:
    #         pos = pos + vel * cycles:
    #     if vel not None:
    #         vel = vel * player.player_type().player_decay() ** cycles

    #     return pos
