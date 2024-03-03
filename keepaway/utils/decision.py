from keepaway.lib.action.neck_turn_to_ball import NeckTurnToBall
from keepaway.lib.action.scan_field import ScanField
from keepaway.lib.action.hold_ball import HoldBall
from keepaway.utils.keepaway_actions import (
    SmartKick,
    GoToPoint,
    NeckTurnToBallOrScan,
    NeckBodyToPoint,
)

from keepaway.lib.action.intercept import Intercept


from pyrusgeom.soccer_math import *
from typing import TYPE_CHECKING
from keepaway.utils.keeepawy_utils import Takers, Keepers
import math as Math

if TYPE_CHECKING:
    from keepaway.lib.player.world_model import WorldModel
    from keepaway.lib.player.player_agent import PlayerAgent

# TODO TACKLE GEN
# TODO GOAL KICK L/R
# TODO GOAL L/R
DEBUG = True


def get_decision_keepaway(
    agent: "PlayerAgent",
    count_list,
    barrier,
    event_to_set,
    event_to_wait,
    obs,
    last_action_time,
    reward,
    terminated,
    full_world,
    adj_matrix,
):
    wm: "WorldModel" = agent.world()

    if wm.our_team_name() == "keepers":
        barrier.wait()
        if wm.get_confidence("ball") < 0.90:
            ScanField().execute(agent)

        # teammates_from_ball = wm.teammates_from_ball()
        # GoToPoint(ball_pos, 0.2, 100).execute(agent)
        # print("ball pos ", wm.ball().pos())

        closest_keeper_from_ball = wm.all_teammates_from_ball()
        if len(closest_keeper_from_ball) > 0:
            if wm.self().unum() == closest_keeper_from_ball[0].unum():
                GoToPoint(wm.ball().pos(), 0.2, 100).execute(agent)

        if wm.self().pos().dist(wm.ball().pos()) < 5.0:
            obs[wm.self().unum()] = wm._retrieve_observation()
            ##
            adj_matrix = wm.adjacency_matrix()
            # print("adj matrix ", adj_matrix)

            if wm.self().is_kickable():
                wm._available_actions[wm.self().unum()] = 2
                # count_list[wm.self().unum()] = 2
                with count_list.get_lock():
                    # print("action received  ", list(count_list))
                    pass
                # print("ball is kickable, ", wm.self().unum())
                Keepers.keeper_with_ball(wm, agent, count_list, last_action_time)
                # return
        else:
            # fastest = wm.get_teammate_nearest_to_ball(1)
            # print("i should be intercepting ")
            fastest = wm.intercept_table().fastest_teammate()
            # print("fastest player intercept table ", f)
            # print("fastest player ", fastest)
            ## TODO:: re-implement interception. this is not working properly.
            ## . check with
            if fastest is not None:
                # print("Get Open")
                Keepers.keeper_support(wm, fastest, agent)

        ## old implementation
        # if fastest is not None:
        #     # Intercept().execute(agent)
        #     if fastest.unum == wm.self()._unum:
        #         print("intercepting")
        #         # print("fastest player ", fastest._pos)
        #         Intercept().execute(agent)
        #     #         agent.set_neck_action(NeckTurnToBall())
        #     #         # print("fastest")
        #     #     # print("fastest player ", fastest._pos)
        #     keeper_support(wm, wm.self(), fastest, agent)

        ## Update State and Environment
        ## calculate reward .
        # with last_action_time.get_lock():
        #     last_action = last_action_time.value
        #     with reward.get_lock():
        #         reward.value = wm.reward(wm.get_current_cycle(), last_action)

    if wm.our_team_name() == "takers":
        # pass
        # barrier.wait()
        if wm.get_confidence("ball") < 0.90:
            ScanField().execute(agent)

        GoToPoint(wm.ball().pos(), 0.2, 100).execute(agent)

        # Maintain possession if you have the ball.
        if wm.self().is_kickable() and (len(wm.teammates_from_ball()) == 0):
            return HoldBall().execute(agent)

        closest_taker_from_ball = wm.teammates_from_ball()
        if wm.self() not in closest_taker_from_ball:
            Takers.mark_most_open_opponent(wm, agent)
            return NeckTurnToBall().execute(agent)

        d = closest_taker_from_ball.dist_to_ball()
        if d < 0.3:
            return NeckTurnToBall().execute(agent)
        return Intercept().execute(agent)
