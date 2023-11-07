from base import goalie_decision
from base.strategy_formation import StrategyFormation
from base.set_play.bhv_set_play import Bhv_SetPlay
from base.bhv_kick import BhvKick
from base.bhv_move import BhvMove
from lib.action.neck_scan_field import NeckScanField
from lib.action.neck_scan_players import NeckScanPlayers
from lib.action.neck_turn_to_ball import NeckTurnToBall

# from lib.action.neck_turn_to_ball_or_scan import NeckTurnToBallOrScan
from lib.action.scan_field import ScanField
from lib.debug.debug import log
from lib.messenger.ball_pos_vel_messenger import BallPosVelMessenger
from lib.messenger.player_pos_unum_messenger import PlayerPosUnumMessenger
from lib.rcsc.types import GameModeType, ViewWidth, UNUM_UNKNOWN
from base.sample_communication import SampleCommunication as comm

from lib.action.hold_ball import HoldBall

# from lib.action.keepaway_actions import HoldBall, GoToPoint
from lib.action.keepaway_actions import SmartKick, GoToPoint, NeckTurnToBallOrScan

from lib.action.turn_to_ball import TurnToBall

# from lib.action.go_to_point import GoToPoint
from lib.action.neck_body_to_point import NeckBodyToPoint
from lib.action.neck_body_to_ball import NeckBodyToBall
from lib.action.neck_turn_to_point import NeckTurnToPoint
from base.basic_tackle import BasicTackle
from lib.player_command.player_command import CommandType
from lib.rcsc.server_param import ServerParam

from base.generator_action import KickAction, ShootAction, KickActionType
from base.generator_dribble import BhvDribbleGen
from base.generator_pass import BhvPassGen
from lib.action.intercept import Intercept

from lib.messenger.pass_messenger import PassMessenger

from pyrusgeom.soccer_math import *
from pyrusgeom.rect_2d import Rect2D
from pyrusgeom.vector_2d import Vector2D
from pyrusgeom.geom_2d import *

from base.tools import Tools
import random
from lib.rcsc.types import ViewWidth
from lib.action.view_wide import ViewWide
from typing import TYPE_CHECKING

import math as Math

if TYPE_CHECKING:
    from lib.player.world_model import WorldModel
    from lib.player.player_agent import PlayerAgent

# TODO TACKLE GEN
# TODO GOAL KICK L/R
# TODO GOAL L/R
DEBUG = True


def get_decision(agent: "PlayerAgent"):
    wm: "WorldModel" = agent.world()

    st = StrategyFormation().i()
    st.update(wm)

    if wm.self().goalie():
        if goalie_decision.decision(agent):
            return True

    if wm.game_mode().type() != GameModeType.PlayOn:
        if Bhv_SetPlay().execute(agent):
            return True

    log.sw_log().team().add_text(
        f"is kickable? dist {wm.ball().dist_from_self()} "
        f"ka {wm.self().player_type().kickable_area()} "
        f"seen pos count {wm.ball().seen_pos_count()} "
        f"is? {wm.self()._kickable}"
    )
    if wm.self().is_kickable():
        ## TODO: check this
        return BhvKick().execute(agent)
    if BhvMove().execute(agent):
        return True
    log.os_log().warn("NO ACTION, ScanFIELD")
    return ScanField().execute(agent)


# working code - should


def get_decision_keepaway(agent: "PlayerAgent", count_list, barrier, event_to_set, event_to_wait,obs,last_action_time,reward,terminated,full_world):
    wm: "WorldModel" = agent.world()

    # def get_open_for_pass(wm):
    #     fastest = wm.get_teammate_nearest_to_ball(5)
    #     if fastest is not None:
    #         if fastest.unum == wm.self()._unum:
    #             print("fastest player ", fastest._pos)
    #             Intercept().execute(agent)


    def get_marking_position(wm, pos, dDist):
        """Returns the marking position."""
        # print("get marking position")
        ball_pos = wm.ball().pos()
        ball_angle = (ball_pos - pos._pos).dir()
        return pos._pos + Vector2D.polar2vector(dDist, ball_angle)

    def mark_opponent(wm, p, dDist, obj):  # TODO: check this.
        """Mark the given opponent."""

        pos_mark = get_marking_position(wm, p, dDist)
        pos_agent = p.pos()
        pos_ball = wm.ball().pos()

        # print("mark position", pos_mark)
        # print("mark position", pos_ball)

        if obj == "ball":
            if pos_mark.dist(pos_agent) < 1.5:
                TurnToBall().execute(agent)
            else:
                GoToPoint(pos_mark, 0.2, 100).execute(agent)
                # return self.move_to_pos(pos_mark, 30.0, 3.0, False)

            if pos_agent.dist(pos_mark) < 2.0:
                ang_opp = (p.pos() - pos_agent).th()
                ang_ball = (pos_ball - pos_agent).th()
                normalized_ang_opp = AngleDeg.normalize_angle(ang_opp + 180)

                if ang_ball.is_within(ang_opp, normalized_ang_opp):
                    ang_opp += 80
                else:
                    ang_opp -= 80

                ang_opp = AngleDeg.normalize_angle(ang_opp)
                target = pos_agent + Vector2D(1.0, ang_opp, POLAR)
                NeckBodyToPoint(target).execute(agent)
                return

        # print("mark: move to marking position", pos_mark)
        GoToPoint(pos_mark, 0.2, 100).execute(agent)
        return

    def mark_most_open_opponent(wm):
        """Mark the most open opponent."""
        
        # print("mark most open opponent")

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
                num = get_in_set_in_cone(wm, 0.3, pos_from, point)
                if num < min:
                    min = num
                    min_player = p

        return mark_opponent(wm, min_player, 4.0, "ball")

    def do_heard_pass_receive(wm, agent):
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
            f"(sample palyer do heard pass) heard_pos={heard_pos}, intercept_pos={intercept_pos}"
        )

        if (
            not wm.kickable_teammate()
            and wm.ball().pos_count() <= 1
            and wm.ball().vel_count() <= 1
            and self_min < 20
        ):
            log.sw_log().team().add_text(
                f"(sample palyer do heard pass) intercepting!, self_min={self_min}"
            )
            log.debug_client().add_message("Comm:Receive:Intercept")
            Intercept().execute(agent)
            agent.set_neck_action(NeckTurnToBall())
        else:
            log.sw_log().team().add_text(
                f"(sample palyer do heard pass) go to point!, cycle={self_min}"
            )
            log.debug_client().set_target(heard_pos)
            log.debug_client().add_message("Comm:Receive:GoTo")

            GoToPoint(heard_pos, 0.5, ServerParam.i().max_dash_power()).execute(agent)
            agent.set_neck_action(NeckTurnToBall())

    def get_in_set_in_cone(wm, radius, pos_from, pos_to):
        """Returns the number of players in the given set in the cone from posFrom to posTo with the given radius."""
        count = 0
        for p in wm._opponents:
            if p.pos_valid():
                if (
                    pos_from.dist(pos_to) - p.pos().dist(pos_to) < radius
                ):  ## TODO: check this
                    count += 1
        # print("count get in set in cone", count)
        return count

    def congestion(wm, point, consider_me):
        ## Keepaway congestion method

        """Returns the congestion at the given position."""
        congest = 0
        if consider_me and point != wm.self().pos():
            congest += 1 / wm.self().pos().dist(point)

        for p in wm._teammates:
            if p.pos_valid() and p.pos() != point:
                congest += 1 / p.pos().dist(point)

        for p in wm._opponents:
            if p.pos_valid() and p.pos() != point:
                congest += 1 / p.pos().dist(point)

        return congest

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

        start_x = rect.bottom_right().x() + x_buffer * length
        start_y = rect.top_left().y() + y_buffer * width

        x = start_x
        y = start_y

        # print("X and Y ", x, y)
        best_congestion = 1000
        point = Vector2D(x, y)
        tmp = None

        for i in range(x_granularity):
            for j in range(y_granularity):
                tmp = congestion(wm, point, True)
                # print("tmp", tmp)   
                if (
                    tmp < best_congestion
                    and get_in_set_in_cone(wm, 0.3, pos_from, point) == 0
                ):
                    best_congestion = tmp
                    best_point = point
                y += y_mesh
            x += x_mesh
            y = start_y

        # print(" After X and Y ", x, y)
        if best_congestion == 1000:
            # take the point out of the rectangle -- meaning no point was valid.
            best_point = rect.center()
        return best_point

    def get_open_for_pass_from_in_rectangle(
        wm, rect: Rect2D, pos_from: Vector2D, fastest
    ):
        best_point = least_congested_point_for_pass_in_rectangle(rect, pos_from)
        if fastest.pos().dist(best_point) < 1.5:
            NeckBodyToPoint(wm.ball().pos()).execute(agent)
        else:
            # print("best point", best_point)
            # print("go to point")
            # agent.do_move(0.0, 0.0)
            # move(wm, agent) 
            GoToPoint(best_point, 0.2, 100).execute(agent)
        return

    def keeper_support(wm, current_player, fastest):
        ##. find the min reach cycle of the fastest teammate to the ball

        sp = ServerParam.i()
        # first_ball_pos = current_player.ball().pos()
        first_ball_pos = wm.ball().pos()

        # print("first ball pos", first_ball_pos)

        # print("current player ", current_player)
        # print("fastest player ", fastest)


        # # TODO: fix player type
        p = fastest
        # ptype = p.player_type()
        min_reach_cycle = Tools.estimate_min_reach_cycle(
            fastest._pos,
            1.0,
            first_ball_pos,
            first_ball_pos.th(),
        )
        # print("min reach cycle", min_reach_cycle)

        ## find dist of ball
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

        # print("pos pass from", pos_pass_from)

        # fix the position to pass from to be in the keep-away rectangle
        # rect = agent.get_keepaway_rec("real")
        # print("old rect", rect)

        rect = wm.keepaway_rect()
        # print("rect", rect)
        # get_open_for_pass_from_in_rectangle(wm, rect, pos_pass_from, p)
        # GoToPoint(ball_pos, 2, 100).execute(agent)

        # # # ObjectT lookObject = self._choose_look_object( 0.97 )
        NeckBodyToPoint(rect.center()).execute(agent)  ##
        return

    def move(wm, agent):
        target = wm.ball().pos()
        GoToPoint(target, 0.2, 100).execute(agent)
        return

    def random_point_in_rect(rect):
        x = random.uniform(rect.left(), rect.left() + 20)
        y = random.uniform(rect.top(), rect.top() + 20)
        return Vector2D(x, y)

    def search_ball(wm, agent):
        return ScanField().execute(agent)

    def hold(wm, agent):
        HoldBall().execute(agent)
        return

    def pass_ball(wm, agent):
        pass_speed = 0.8  ## in player settings

        agent.do_kick_to(2, 18, Vector2D(5, 0))
        return

    def keeper(wm: "WorldModel", agent: "PlayerAgent"):
        # if wm.self()._is_new_episode() == True:
        #     wm.self().end_episode(wm._reward())  #
        #     wm.set_new_episode()
        #     self.world().set_last_action(-1)  #
        #     time_start_episode = self.world().time()  #
        if DEBUG:
            log.sw_log().world().add_text(f"ball pos = {wm.ball().pos()}")

        if wm.get_confidence("ball") < 0.90:
            if ScanField().execute(agent):
                ball_pos = wm.ball().pos()
                # print("ball pos", ball_pos)
                # GoToPoint(ball_pos, 0.2, 100).execute(agent)
                move(wm,agent)
                return
        return

    def interpret_keeper_action(wm, agent, action):
        if action == 0:
            hold(wm, agent)
        elif action == 1:
            # BhvKick().execute(agent)
            # my teammates are
            k = wm.teammates_from_ball()
            # print("k", k)
            if len(k) > 0:
                temp_pos = k[0].pos()
                # print("pass ball", temp_pos)
                agent.do_kick_to(50, 18, temp_pos)
        return

    def handcoded():
        obs = wm._retrieve_observation()
        return 0

    def learned_policy():
        obs = wm._retrieve_observation()

        if len(obs) > 0:
            if wm._get_last_action_time() is None:
                # action = wm.self().start_episode(state)
                # print("ball", wm.ball().pos())
                action = 0
            elif (
                wm._get_last_action_time() == wm._get_current_cycle() - 1
            ) and wm._last_action > 0:
                action = wm._last_action
                # pass_ball(wm, agent)
                # print("continue action")
            else:
                # action = self.step(wm._reward(), state)
                wm._set_last_action(action)
                # print("in step")
        else:
            action = 0
        # print("action", action)
        return action

    def keeper_with_ball(wm: "WorldModel", agent: "PlayerAgent", policy):
        if policy == "random":
            action = random.randint(0, 1)
            # print("random action", action)
        elif policy == "always-hold":
            action = 0
        elif policy == "handcoded":
            action = handcoded()
        else:
            action = learned_policy()
        return interpret_keeper_action(wm, agent, action)
    

    def keeper_with_ball_2(wm: "WorldModel", agent: "PlayerAgent", actions, last_action_time):
        # print("keeper with ball")
        # action = actions[wm.self().unum()]
        action = random.randint(0, 1)
        interpret_keeper_action(wm, agent, action)
        ## Update last action time for action keeper
        # if last_action_time[wm.self().unum()] == 0:
        #     last_action_time[wm.self().unum()] = wm._get_last_action_time()
        # with last_action_time.get_lock():
        #     if last_action_time.value == 0:
        #         last_action_time = wm._get_last_action_time()

        # print("last action time", last_action_time)
        pass

    if wm.our_team_name() == "keepers":
        ## barrier for synchronizing game cycle for all keepers
        barrier.wait()
        ## get observation .. 
        keeper(wm, agent)
        obs[wm.self().unum()] = wm._retrieve_observation()
        
        if wm.self().is_kickable():
            wm._available_actions[wm.self().unum()] = 2
            count_list[wm.self().unum()] = 2
            keeper_with_ball_2(wm, agent, wm._available_actions, last_action_time)

        fastest = wm.get_teammate_nearest_to_ball(5)
        if fastest is not None:
            if fastest.unum == wm.self()._unum:
                print("fastest player ", fastest._pos)
                Intercept().execute(agent)
        #         agent.set_neck_action(NeckTurnToBall())
        #         # print("fastest")
        #     # print("fastest player ", fastest._pos)
            # keeper_support(wm,wm.self(), fastest)

        ## Update State and Environment
        ## calculate reward .
        with last_action_time.get_lock():
            last_action = last_action_time.value
            with reward.get_lock():
                reward.value = wm.reward(wm.get_current_cycle(),last_action)
        
        # with terminated.get_lock():
        #     terminated.value = True
        # print("full world value ", full_world._terminated)
        # print("terminated value ", terminated.value)
           

    if wm.our_team_name() == "takers":
        if wm.get_confidence("ball") < 0.90:
            search_ball(wm, agent)
            return
        # Maintain possession if you have the ball.
        if wm.self().is_kickable() and (len(wm.teammates_from_ball()) == 0):
            # print(" taker hold ball")
            return HoldBall().execute(agent)
        closest_taker_from_ball = wm.teammates_from_ball()
        if wm.self() not in closest_taker_from_ball:
            mark_most_open_opponent(wm)  ## should be a behavior
            NeckTurnToBall().execute(agent)
            return
        d = closest_taker_from_ball.dist_to_ball()
        if d < 0.3:
            NeckTurnToBall().execute(agent)
            NeckBodyToBall().execute(agent)
            return
        Intercept().execute(agent)
        return 
