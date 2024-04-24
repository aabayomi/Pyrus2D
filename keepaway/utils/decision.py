"""
Keepaway decision making module.

"""

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
from keepaway.utils.keepaway_utils import Takers, Keepers
import math as Math

if TYPE_CHECKING:
    from keepaway.lib.player.world_model import WorldModel
    from keepaway.lib.player.player_agent import PlayerAgent
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

        closest_keeper_from_ball = wm.all_teammates_from_ball()
        if len(closest_keeper_from_ball) > 0:
            if wm.self().unum() == closest_keeper_from_ball[0].unum():
                GoToPoint(wm.ball().pos(), 0.2, 100).execute(agent)

        if wm.self().pos().dist(wm.ball().pos()) < 5.0:
            with count_list.get_lock():
                obs[wm.self().unum()] = wm._retrieve_observation()

            if wm.self().is_kickable():
                # wm._available_actions[wm.self().unum()] = 2
                with count_list.get_lock():
                    pass

                Keepers.keeper_with_ball(wm, agent, count_list, last_action_time)
        else:
            fastest = wm.intercept_table().fastest_teammate()
            if fastest is not None:
                Keepers.keeper_support(wm, fastest, agent)

    if wm.our_team_name() == "takers":
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
