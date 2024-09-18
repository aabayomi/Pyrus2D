from pyrusgeom.geom_2d import *
from keepaway.lib.action.turn_to_ball import TurnToBall
from keepaway.lib.rcsc.server_param import ServerParam

from keepaway.utils.hfo_actions import *
from keepaway.utils.tools import Tools
from pyrusgeom.soccer_math import *
from pyrusgeom.vector_2d import Vector2D
from pyrusgeom.geom_2d import *
from keepaway.lib.debug.debug import log
from typing import TYPE_CHECKING

from keepaway.utils.hfo_actions import *
from keepaway.lib.action.intercept import Intercept

if TYPE_CHECKING:
    from keepaway.lib.player.world_model import WorldModel
    from keepaway.lib.player.object_player import PlayerObject

##TODO:
## 1. Check and implement MOVE behavior
## 2. Check and implement MARK_PLAYER behavior
## 3. Check and implement REORIENT
## 4. Check and implement INTERCEPT (hfo)

GOAL_POS_X = 0.9
GOAL_POS_Y = 0.0

# below - from hand_coded_defense_agent.cpp except LOW_KICK_DIST
HALF_FIELD_WIDTH = 68  # y coordinate -34 to 34 (-34 = bottom 34 = top)
HALF_FIELD_LENGTH = 52.5  # x coordinate 0 to 52.5 (0 = goalline 52.5 = center)
params = {
    "KICK_DIST": (1.504052352 * 1),
    "OPEN_AREA_HIGH_LIMIT_X": 0.747311440447,
    "TACKLE_DIST": (1.613456553 * 1),
    "LOW_KICK_DIST": ((5 * 5) / HALF_FIELD_LENGTH),
}


class OffenseAgent:
    """Offense agent."""

    @staticmethod
    def offense_with_ball(
        wm: "WorldModel", agent: "PlayerAgent", actions, last_action_time
    ):
        """
        This method implements the keeper with ball.


        Args:
            wm: WorldModel
            agent: PlayerAgent
            actions: list
            last_action_time: float
        """

        action = actions[wm.self().unum() - 1]
        OffenseAgent.interpret_offensive_action(wm, agent, action)

    @staticmethod
    def interpret_offensive_action(wm: "WorldModel", agent, action):
        """
        This method interprets the keeper action.
        Args:
            wm: WorldModel
            agent: PlayerAgent
            action: int
        """

        # if action == 0:
        #     # return HoldBall().execute(agent)
        #     return
        # else:
        #     k = wm.teammates_from_ball()
        #     if len(k) > 0:
        #         for tm in k:
        #             if tm.unum() == action:
        #                 temp_pos = tm.pos()
        #                 return agent.do_kick_to(tm, 1.5)
        # return


class DefenseAgent:
    """Defense agent."""

    @staticmethod
    def defense_with_ball(
        wm: "WorldModel", agent: "PlayerAgent", actions, last_action_time
    ):
        """
        This method implements the defense player behaviors.


        Args:
            wm: WorldModel
            agent: PlayerAgent
            actions: list
            last_action_time: float
        """

        action = actions[wm.self().unum() - 1]
        DefenseAgent.interpret_defensive_action(wm, agent, action)

    @staticmethod
    def interpret_defensive_action(wm: "WorldModel", agent, action):
        """
        This method interprets the keeper action.
        Args:
            wm: WorldModel
            agent: PlayerAgent
            action: int
        """

        if action == 0:
            do_random_defense_action(wm, agent, obs)
            return
        elif action == 1:
            do_defense_action(
                obs,
                wm,
                agent,
                old_ball_pos_x=old_ball_pos_x,
                old_ball_pos_y=old_ball_pos_y,
                num_times_overall=num_times_overall,
                num_times_kickable=num_times_kickable,
                misc_tracked=misc_tracked,
            )
            return

    @staticmethod
    def do_random_defense_action(
        wm: "WorldModel", agent: "PlayerAgent", obs: "Observation"
    ):
        """
        This method implements the defense player behaviors.
        Args:
            wm: WorldModel
            agent: PlayerAgent
        """
        # If ball is kickable

        if obs[5] > 0:
            GoToPoint(wm.ball().pos(), 0.2, 100).execute(agent)
        else:
            if random.random() < 0.25:
                ReduceAngleToGoal().execute(agent)
            else:
                GoToPoint(wm.ball().pos(), 0.2, 100).execute(agent)
        return

    @staticmethod
    def add_num_times(action, main_dict, opt_dict=None):
        """
        This method adds the number of times an action is executed.
        Args:
            action: int
            main_dict: dict
            opt_dict: dict
        """
        pass
        # main_dict[action] += 1
        # if opt_dict:
        #     pass
        return

    @staticmethod
    def do_defense_action(
        obs,
        wm: "WorldModel",
        agent: "PlayerAgent",
        old_ball_pos_x,
        old_ball_pos_y,
        num_times_overall,
        num_times_kickable,
        misc_tracked,
    ):
        """Figures out and does the (hopefully) best defense action."""

        num_opponents = wm.num_opponents()
        num_teammates = wm.num_teammates()

        min_vec_size = 10 + (6 * num_teammates) + (3 * num_opponents)
        if len(obs) < min_vec_size:
            raise LookupError(
                "Feature vector length is {0:d} not {1:d}".format(
                    len(obs), min_vec_size
                )
            )
        agent_pos_x = obs[0]
        agent_pos_y = obs[1]
        ball_pos_x = obs[3]
        ball_pos_y = obs[4]

        # if get high_level working for invalid
        if min(agent_pos_x, agent_pos_y, ball_pos_x, ball_pos_y) < -1:
            NeckTurnToBall().execute(agent)
        return

        ball_toward_goal = ball_moving_toward_goal(
            ball_pos_x, ball_pos_y, old_ball_pos_x, old_ball_pos_y
        )

        ball_nearer_goal = ball_nearer_to_goal(
            ball_pos_x, ball_pos_y, agent_pos_x, agent_pos_y
        )

        ball_sorted_list = get_sorted_opponents(
            obs, num_opponents, num_teammates, pos_x=ball_pos_x, pos_y=ball_pos_y
        )
        if not ball_sorted_list:  # unknown opponent positions/unums
            print(
                "No known opponent locations (btg {0!r}; bng {1!r}; ".format(
                    ball_toward_goal, ball_nearer_goal
                )
                + "ball xy {0:n}, {1:n}; ball old xy {2:n}, {3:n}; kickable {4:n})".format(
                    ball_pos_x, ball_pos_y, old_ball_pos_x, old_ball_pos_y, obs[5]
                )
            )
            if (min(agent_pos_x, agent_pos_y, ball_pos_x, ball_pos_y) <= -1) or (
                max(agent_pos_x, agent_pos_y, ball_pos_x, ball_pos_y) >= 1
            ):
                NeckTurnToBall().execute(agent)
            elif ball_toward_goal:
                if ball_nearer_goal:
                    add_num_times(
                        hfo.REDUCE_ANGLE_TO_GOAL, num_times_overall, num_times_kickable
                    )
                    ReduceAngleToGoal().execute(agent)
                else:
                    # update_time_overall()
                    add_num_times(hfo.INTERCEPT, num_times_overall, num_times_kickable)
                    Intercept().execute(agent)
            else:
                #   update_time_overall()
                GoToPoint(wm.ball().pos(), 0.2, 100).execute(agent)
            return

        goal_sorted_list = get_sorted_opponents(
            obs, num_opponents, num_teammates, pos_x=GOAL_POS_X, pos_y=GOAL_POS_Y
        )

        if ball_toward_goal:
            if ball_sorted_list[0][1] < params["LOW_KICK_DIST"]:
                ball_toward_goal = False
        elif goal_sorted_list[0][1] < get_dist_normalized(
            ball_pos_x, ball_pos_y, GOAL_POS_X, GOAL_POS_Y
        ):
            ball_toward_goal = False

        is_tackleable_opp = is_tackleable(
            agent_pos_x,
            agent_pos_y,
            ball_sorted_list[0][1],
            ball_sorted_list[0][2],
            ball_sorted_list[0][3],
        )

        agent_to_ball_dist = get_dist_normalized(
            agent_pos_x, agent_pos_y, ball_pos_x, ball_pos_y
        )

        if obs[5] > 0:  # kickable distance of player
            misc_tracked["max_kickable_dist"] = max(
                agent_to_ball_dist, misc_tracked["max_kickable_dist"]
            )
            if is_tackleable_opp:
                # hfo_env.act(add_num_times(hfo.MOVE,num_times_overall,num_times_kickable)) # will do tackle
                add_num_times(hfo.MOVE, num_times_overall, num_times_kickable)
                GoToPoint(wm.ball().pos(), 0.2, 100).execute(agent)
            elif ball_nearer_goal:
                # hfo_env.act(add_num_times(hfo.REDUCE_ANGLE_TO_GOAL,num_times_overall,num_times_kickable))
                add_num_times(
                    hfo.REDUCE_ANGLE_TO_GOAL, num_times_overall, num_times_kickable
                )
                ReduceAngleToGoal().execute(agent)
            elif ball_toward_goal:
                # hfo_env.act(add_num_times(hfo.INTERCEPT,num_times_overall,num_times_kickable))
                add_num_times(hfo.INTERCEPT, num_times_overall, num_times_kickable)
                Intercept().execute(agent)
            else:
                # hfo_env.act(add_num_times(hfo.GO_TO_BALL,num_times_overall,num_times_kickable))
                add_num_times(hfo.GO_TO_BALL, num_times_overall, num_times_kickable)
                GoToPoint(wm.ball().pos(), 0.2, 100).execute(agent)
            return

        if goal_sorted_list[0][0] != ball_sorted_list[0][0]:
            if is_in_open_area(
                ball_sorted_list[0][2], ball_sorted_list[0][3]
            ) and is_in_open_area(goal_sorted_list[0][2], goal_sorted_list[0][3]):
                if ball_sorted_list[0][1] < params["LOW_KICK_DIST"]:
                    # hfo_env.act(add_num_times(hfo.MARK_PLAYER,num_times_overall),
                    #             goal_sorted_list[0][0])

                    mark_player(agent, goal_sorted_list[0][0])
                elif agent_to_ball_dist < ball_sorted_list[0][1]:
                    if ball_nearer_goal:
                        # hfo_env.act(add_num_times(hfo.REDUCE_ANGLE_TO_GOAL,num_times_overall))
                        # reduce_angle_to_goal(agent)
                        add_num_times(hfo.REDUCE_ANGLE_TO_GOAL, num_times_overall)
                        ReduceAngleToGoal().execute(agent)
                    elif ball_toward_goal:
                        # hfo_env.act(add_num_times(hfo.INTERCEPT,num_times_overall))
                        add_num_times(hfo.INTERCEPT, num_times_overall)
                        Intercept().execute(agent)
                    else:
                        # hfo_env.act(add_num_times(hfo.GO_TO_BALL,num_times_overall))

                        add_num_times(hfo.GO_TO_BALL, num_times_overall)
                        GoToPoint(wm.ball().pos(), 0.2, 100).execute(agent)
                else:
                    # hfo_env.act(add_num_times(hfo.REDUCE_ANGLE_TO_GOAL,num_times_overall))
                    add_num_times(hfo.REDUCE_ANGLE_TO_GOAL, num_times_overall)
                    reduce_angle_to_goal(agent)

            elif ball_sorted_list[0][1] >= params["KICK_DIST"]:
                if agent_to_ball_dist < ball_sorted_list[0][1]:
                    if ball_nearer_goal:
                        # hfo_env.act(add_num_times(hfo.REDUCE_ANGLE_TO_GOAL,num_times_overall))
                        add_num_times(hfo.REDUCE_ANGLE_TO_GOAL, num_times_overall)
                        ReduceAngleToGoal().execute(agent)
                    elif ball_toward_goal:
                        # hfo_env.act(add_num_times(hfo.INTERCEPT,num_times_overall))
                        add_num_times(hfo.INTERCEPT, num_times_overall)
                        Intercept().execute(agent)
                    else:
                        # hfo_env.act(add_num_times(hfo.GO_TO_BALL,num_times_overall))
                        add_num_times(hfo.GO_TO_BALL, num_times_overall)
                        GoToPoint(wm.ball().pos(), 0.2, 100).execute(agent)
                else:
                    # hfo_env.act(add_num_times(hfo.REDUCE_ANGLE_TO_GOAL,num_times_overall))
                    add_num_times(hfo.REDUCE_ANGLE_TO_GOAL, num_times_overall)
                    ReduceAngleToGoal().execute(agent)

            elif is_tackleable_opp and (
                not is_in_open_area(ball_sorted_list[0][2], ball_sorted_list[0][3])
            ):
                # hfo_env.act(add_num_times(hfo.MOVE,num_times_overall))
                add_num_times(hfo.MOVE, num_times_overall)
                GoToPoint(wm.ball().pos(), 0.2, 100).execute(agent)

            elif ball_sorted_list[0][1] < (1 * params["LOW_KICK_DIST"]):
                # hfo_env.act(add_num_times(hfo.MARK_PLAYER,num_times_overall),goal_sorted_list[0][0])
                add_num_times(hfo.MARK_PLAYER, num_times_overall)
                mark_player(agent, goal_sorted_list[0][0])
            else:
                # hfo_env.act(add_num_times(hfo.REDUCE_ANGLE_TO_GOAL,num_times_overall))
                add_num_times(hfo.REDUCE_ANGLE_TO_GOAL, num_times_overall)
                ReduceAngleToGoal().execute(agent)
            return

        if is_in_open_area(ball_sorted_list[0][2], ball_sorted_list[0][3]):
            if ball_sorted_list[0][1] < params["KICK_DIST"]:
                # hfo_env.act(add_num_times(hfo.REDUCE_ANGLE_TO_GOAL,num_times_overall))
                add_num_times(hfo.REDUCE_ANGLE_TO_GOAL, num_times_overall)
                ReduceAngleToGoal().execute(agent)
            elif agent_to_ball_dist < params["KICK_DIST"]:
                if ball_nearer_goal:
                    # hfo_env.act(add_num_times(hfo.REDUCE_ANGLE_TO_GOAL,num_times_overall))
                    add_num_times(hfo.REDUCE_ANGLE_TO_GOAL, num_times_overall)
                    ReduceAngleToGoal().execute(agent)
                elif ball_toward_goal:
                    # hfo_env.act(add_num_times(hfo.INTERCEPT,num_times_overall))
                    add_num_times(hfo.INTERCEPT, num_times_overall)
                    Intercept().execute(agent)
                else:
                    # hfo_env.act(add_num_times(hfo.GO_TO_BALL,num_times_overall))
                    add_num_times(hfo.GO_TO_BALL, num_times_overall)
                    GoToPoint(wm.ball().pos(), 0.2, 100).execute(agent)
            elif is_tackleable_opp:
                # hfo_env.act(add_num_times(hfo.MOVE,num_times_overall))
                add_num_times(hfo.MOVE, num_times_overall)
                GoToPoint(wm.ball().pos(), 0.2, 100).execute(agent)
            else:
                # hfo_env.act(add_num_times(hfo.REDUCE_ANGLE_TO_GOAL,num_times_overall))
                add_num_times(hfo.REDUCE_ANGLE_TO_GOAL, num_times_overall)
                ReduceAngleToGoal().execute(agent)
        else:
            if ball_sorted_list[0][1] >= max(params["KICK_DIST"], agent_to_ball_dist):
                if ball_nearer_goal:
                    # hfo_env.act(add_num_times(hfo.REDUCE_ANGLE_TO_GOAL,num_times_overall))
                    add_num_times("REDUCE_ANGLE_TO_GOAL", num_times_overall)
                    ReduceAngleToGoal().execute(agent)
                elif ball_toward_goal:
                    # hfo_env.act(add_num_times(hfo.INTERCEPT,num_times_overall))
                    add_num_times("INTERCEPT", num_times_overall)
                    Intercept().execute(agent)
                else:
                    # hfo_env.act(add_num_times(hfo.GO_TO_BALL,num_times_overall))
                    # go_to_ball(agent)
                    add_num_times("GO_TO_BALL", num_times_overall)
                    GoToPoint(wm.ball().pos(), 0.2, 100).execute(agent)
            elif ball_sorted_list[0][1] >= params["KICK_DIST"]:
                # hfo_env.act(add_num_times(hfo.REDUCE_ANGLE_TO_GOAL,num_times_overall))
                add_num_times("REDUCE_ANGLE_TO_GOAL", num_times_overall)
                ReduceAngleToGoal().execute(agent)
            elif is_tackleable_opp:
                # hfo_env.act(add_num_times(hfo.MOVE,num_times_overall))
                add_num_times("MOVE", num_times_overall)
                GoToPoint(wm.ball().pos(), 0.2, 100).execute(agent)
            else:
                # hfo_env.act(add_num_times(hfo.REDUCE_ANGLE_TO_GOAL,num_times_overall))
                add_num_times("REDUCE_ANGLE_TO_GOAL", num_times_overall)
                ReduceAngleToGoal().execute(agent)
        return
