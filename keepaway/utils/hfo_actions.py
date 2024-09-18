"""
    Handcoded actions for HFO

"""

from pyrusgeom.angle_deg import AngleDeg
from keepaway.lib.action.neck_turn_to_ball import NeckTurnToBall
from keepaway.lib.action.scan_field import ScanField
from keepaway.lib.action.hold_ball import HoldBall
from keepaway.lib.action.intercept import Intercept
from keepaway.lib.action.go_to_point import GoToPoint
from keepaway.lib.action.smart_kick import SmartKick
from keepaway.lib.rcsc.server_param import ServerParam


## dist between to points ( TODO: reuseable )
def normalized_dist_between_points(x1, y1, x2, y2):
    return math.sqrt(
        (x2 - x1) ** 2 + (HALF_FIELD_WIDTH / HALF_FIELD_LENGTH) * (y2 - y1) ** 2
    )


def is_tackleable(agent_pos_x, agent_pos_y, ball_dist, opp_pos_x, opp_pos_y):
    return (
        get_dist_normalized(agent_pos_x, agent_pos_y, opp_pos_x, opp_pos_y)
        < params["TACKLE_DIST"]
    ) and (ball_dist < params["LOW_KICK_DIST"])


def ball_moving_toward_goal(ball_pos_x, ball_pos_y, old_ball_pos_x, old_ball_pos_y):
    return get_dist_normalized(ball_pos_x, ball_pos_y, GOAL_POS_X, GOAL_POS_Y) < min(
        params["KICK_DIST"],
        get_dist_normalized(old_ball_pos_x, old_ball_pos_y, GOAL_POS_X, GOAL_POS_Y),
    )


def ball_nearer_to_goal(ball_pos_x, ball_pos_y, agent_pos_x, agent_pos_y):
    return get_dist_normalized(ball_pos_x, ball_pos_y, GOAL_POS_X, GOAL_POS_Y) < min(
        params["KICK_DIST"],
        get_dist_normalized(agent_pos_x, agent_pos_y, GOAL_POS_X, GOAL_POS_Y),
    )


## sorted opppennets ( TODO: reuseable )


def get_sorted_opponents(state_vec, num_opponents, num_teammates, pos_x, pos_y):
    """
    Returns a list of tuple(unum, dist, opp_pos_x, opp_pos_y),
    sorted in increasing order of dist from the given position
    """
    unum_list = []
    for i in range(num_opponents):
        unum = state_vec[9 + (i * 3) + (6 * num_teammates) + 3]
        if unum > 0:
            opp_pos_x = state_vec[9 + (i * 3) + (6 * num_teammates) + 1]
            opp_pos_y = state_vec[9 + (i * 3) + (6 * num_teammates) + 2]
            dist = get_dist_normalized(pos_x, pos_y, opp_pos_x, opp_pos_y)
            unum_list.append(tuple([unum, dist, opp_pos_x, opp_pos_y]))
        # otherwise, unknown
    if len(unum_list) > 1:
        return sorted(unum_list, key=lambda x: x[1])
    return unum_list


def is_in_open_area(pos_x, ignored_pos_y):
    return pos_x >= params["OPEN_AREA_HIGH_LIMIT_X"]


def add_num_times(action, main_dict, opt_dict=None):
    main_dict[action] += 1
    if opt_dict:
        opt_dict[action] += 1
    return action


class ReduceAngleToGoal:

    def __init__(self):
        pass

    def execute(self, agent):

        wm = agent.world()
        SP = ServerParam.i()

        goal_pos1 = Vector2D(-SP.pitch_half_length(), SP.goal_width() / 2)
        goal_pos2 = Vector2D(-SP.pitch_half_length(), -SP.goal_width() / 2)

        ball = wm.ball()
        if not ball.pos_valid():
            return False

        ball_pos = ball.pos()
        near_ratio = 0.9

        teammates_between_ball_and_goal = []
        self_pos = wm.self().pos()
        goal_line_1 = Line2D(goal_pos1, ball_pos)
        goal_line_2 = Line2D(goal_pos2, ball_pos)
        max_angle_end_pt1 = goal_pos2
        max_angle_end_pt2 = goal_pos1

        # Filter out points not lying in the cone
        for teammate in wm.teammates_from_self():
            teammate_pos = teammate.pos()
            y1 = goal_line_1.get_y(teammate_pos.x)
            y2 = goal_line_2.get_y(teammate_pos.x)

            if teammate_pos.x >= ball_pos.x:
                continue

            if teammate_pos.y <= min(y1, y2) or teammate_pos.y >= max(y1, y2):
                continue

            # Push into the list if it passes both tests
            teammates_between_ball_and_goal.append(teammate)

        # Sort teammates by y position
        teammates_between_ball_and_goal.sort(key=lambda t: t.pos().y)
        max_angle = 0

        # Find max angle and choose endpoints
        for i in range(len(teammates_between_ball_and_goal) + 1):
            if i == 0:
                first_pos = goal_pos2
            else:
                first_pos = teammates_between_ball_and_goal[i - 1].pos()

            if i == len(teammates_between_ball_and_goal):
                second_pos = goal_pos1
            else:
                second_pos = teammates_between_ball_and_goal[i].pos()

            angle1 = math.atan2(ball_pos.y - first_pos.y, ball_pos.x - first_pos.x)
            angle2 = math.atan2(ball_pos.y - second_pos.y, ball_pos.x - second_pos.x)

            open_angle_value = abs(AngleDeg.normalize_angle(angle1 - angle2))

            if open_angle_value > max_angle:
                max_angle = open_angle_value
                max_angle_end_pt1 = first_pos
                max_angle_end_pt2 = second_pos

        # Calculate and go to the target point
        target_line_end1 = max_angle_end_pt1 * (1 - near_ratio) + ball_pos * near_ratio
        target_line_end2 = max_angle_end_pt2 * (1 - near_ratio) + ball_pos * near_ratio
        dist_to_end1 = target_line_end1.dist2(ball_pos)
        dist_to_end2 = target_line_end2.dist2(ball_pos)
        ratio = dist_to_end2 / (dist_to_end1 + dist_to_end2)
        target = target_line_end1 * ratio + target_line_end2 * (1 - ratio)

        if (
            GoToPoint(target, 0.25, ServerParam().max_dash_power()).execute(self)
            or wm.self().collides_with_post()
        ):
            return True
        return False


def intercept(agent):
    pass


def move(agent):
    pass


# enum action_t
# {
#   DASH,       // [Low-Level] Dash(power [0,100], direction [-180,180]) # Done
#   TURN,       // [Low-Level] Turn(direction [-180,180]) # Done
#   TACKLE,     // [Low-Level] Tackle(direction [-180,180])
#   KICK,       // [Low-Level] Kick(power [0,100], direction [-180,180]) # Done
#   KICK_TO,    // [Mid-Level] Kick_To(target_x [-1,1], target_y [-1,1], speed [0,3]) # Done
#   MOVE_TO,    // [Mid-Level] Move(target_x [-1,1], target_y [-1,1]) # Done
#   DRIBBLE_TO, // [Mid-Level] Dribble(target_x [-1,1], target_y [-1,1])
#   INTERCEPT,  // [Mid-Level] Intercept(): Intercept the ball
#   MOVE,       // [High-Level] Move(): Reposition player according to strategy
#   SHOOT,      // [High-Level] Shoot(): Shoot the ball
#   PASS,       // [High-Level] Pass(teammate_unum [0,11]): Pass to the most open teammate
#   DRIBBLE,    // [High-Level] Dribble(): Offensive dribble
#   CATCH,      // [High-Level] Catch(): Catch the ball (Goalie only!)
#   NOOP,       // Do nothing
#   QUIT,       // Special action to quit the game
#   REDUCE_ANGLE_TO_GOAL, // [High-Level] Reduce_Angle_To_Goal : Reduces the shooting angle
#   MARK_PLAYER, // [High-Level] Mark_Player(opponent_unum [0,11]) : Moves to the position in between the kicker and a given player
#   DEFEND_GOAL,
#   GO_TO_BALL,
#   REORIENT  // [High-Level] Handle lost position of self/ball, misc other situations; variant of doPreprocess called in DRIBBLE
# };
