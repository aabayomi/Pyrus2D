"""
    Handcoded actions for HFO

"""




GOAL_POS_X = 0.9
GOAL_POS_Y = 0.0

# below - from hand_coded_defense_agent.cpp except LOW_KICK_DIST
HALF_FIELD_WIDTH = 68 # y coordinate -34 to 34 (-34 = bottom 34 = top)
HALF_FIELD_LENGTH = 52.5 # x coordinate 0 to 52.5 (0 = goalline 52.5 = center)
params = {'KICK_DIST':(1.504052352*1), 'OPEN_AREA_HIGH_LIMIT_X':0.747311440447,
          'TACKLE_DIST':(1.613456553*1), 'LOW_KICK_DIST':((5*5)/HALF_FIELD_LENGTH)}


## dist between to points ( TODO: reuseable )
def normalized_dist_between_points(x1, y1, x2, y2):
    return math.sqrt((x2 - x1)**2 + (HALF_FIELD_WIDTH/HALF_FIELD_LENGTH)*(y2 - y1)**2)

def is_tackleable(agent_pos_x, agent_pos_y, ball_dist, opp_pos_x, opp_pos_y):
  return (get_dist_normalized(agent_pos_x,
                              agent_pos_y,
                              opp_pos_x,
                              opp_pos_y) < params['TACKLE_DIST']) and (ball_dist <
                                                                       params['LOW_KICK_DIST'])

def ball_moving_toward_goal(ball_pos_x, ball_pos_y, old_ball_pos_x, old_ball_pos_y):
  return (get_dist_normalized(ball_pos_x, ball_pos_y,
                              GOAL_POS_X, GOAL_POS_Y) < min(params['KICK_DIST'],
                                                            get_dist_normalized(old_ball_pos_x,
                                                                                old_ball_pos_y,
                                                                                GOAL_POS_X,
                                                                                GOAL_POS_Y)))

def ball_nearer_to_goal(ball_pos_x, ball_pos_y, agent_pos_x, agent_pos_y):
  return get_dist_normalized(ball_pos_x, ball_pos_y,
                             GOAL_POS_X, GOAL_POS_Y) < min(params['KICK_DIST'],
                                                           get_dist_normalized(agent_pos_x,
                                                                               agent_pos_y,
                                                                               GOAL_POS_X,
                                                                               GOAL_POS_Y))



## sorted opppennets ( TODO: reuseable )

def get_sorted_opponents(state_vec, num_opponents, num_teammates, pos_x, pos_y):
  """
  Returns a list of tuple(unum, dist, opp_pos_x, opp_pos_y),
  sorted in increasing order of dist from the given position
  """
  unum_list = []
  for i in range(num_opponents):
    unum = state_vec[9+(i*3)+(6*num_teammates)+3]
    if unum > 0:
      opp_pos_x = state_vec[9+(i*3)+(6*num_teammates)+1]
      opp_pos_y = state_vec[9+(i*3)+(6*num_teammates)+2]
      dist = get_dist_normalized(pos_x, pos_y, opp_pos_x, opp_pos_y)
      unum_list.append(tuple([unum, dist, opp_pos_x, opp_pos_y]))
    # otherwise, unknown
  if len(unum_list) > 1:
    return sorted(unum_list, key=lambda x: x[1])
  return unum_list



def is_in_open_area(pos_x, ignored_pos_y):
  return pos_x >= params['OPEN_AREA_HIGH_LIMIT_X']

def add_num_times(action, main_dict, opt_dict=None):
  main_dict[action] += 1
  if opt_dict:
    opt_dict[action] += 1
  return action


def do_defense_action(state_vec, hfo_env,
                      num_opponents, num_teammates,
                      old_ball_pos_x, old_ball_pos_y,
                      num_times_overall, num_times_kickable,
                      misc_tracked):

    """Figures out and does the (hopefully) best defense action."""


    min_vec_size = 10 + (6*num_teammates) + (3*num_opponents)
    if (len(state_vec) < min_vec_size):
        raise LookupError("Feature vector length is {0:d} not {1:d}".format(len(state_vec),
                                                                        min_vec_size))
    agent_pos_x = state_vec[0]
    agent_pos_y = state_vec[1]
    ball_pos_x = state_vec[3]
    ball_pos_y = state_vec[4]

    # if get high_level working for invalid
    if (min(agent_pos_x,agent_pos_y,ball_pos_x,ball_pos_y) < -1):
        hfo_env.act(add_num_times(hfo.REORIENT,num_times_overall))
    return


    ball_toward_goal = ball_moving_toward_goal(ball_pos_x, ball_pos_y,
                                                old_ball_pos_x, old_ball_pos_y)

    ball_nearer_goal = ball_nearer_to_goal(ball_pos_x, ball_pos_y,
                                            agent_pos_x, agent_pos_y)

    ball_sorted_list = get_sorted_opponents(state_vec, num_opponents, num_teammates,
                                            pos_x=ball_pos_x, pos_y=ball_pos_y)
    if not ball_sorted_list: # unknown opponent positions/unums
        print("No known opponent locations (btg {0!r}; bng {1!r}; ".format(ball_toward_goal,
                                                                       ball_nearer_goal) +
          "ball xy {0:n}, {1:n}; ball old xy {2:n}, {3:n}; kickable {4:n})".format(ball_pos_x,
                                                                                   ball_pos_y,
                                                                                   old_ball_pos_x,
                                                                                   old_ball_pos_y,
                                                                                   state_vec[5]))
    if ((min(agent_pos_x,agent_pos_y,ball_pos_x,ball_pos_y) <= -1) or
        (max(agent_pos_x,agent_pos_y,ball_pos_x,ball_pos_y) >= 1)):
      # remove if get high-level working for invalid
      hfo_env.act(add_num_times(hfo.REORIENT,num_times_overall))
    elif ball_toward_goal:
      if ball_nearer_goal:
        hfo_env.act(add_num_times(hfo.REDUCE_ANGLE_TO_GOAL,num_times_overall))
      else:
        hfo_env.act(add_num_times(hfo.INTERCEPT,num_times_overall))
    else:
      hfo_env.act(add_num_times(hfo.MOVE,num_times_overall))
    return

    goal_sorted_list = get_sorted_opponents(state_vec, num_opponents, num_teammates,
                                            pos_x=GOAL_POS_X, pos_y=GOAL_POS_Y)

    if ball_toward_goal:
        if ball_sorted_list[0][1] < params['LOW_KICK_DIST']:
            ball_toward_goal = False
    elif goal_sorted_list[0][1] < get_dist_normalized(ball_pos_x,ball_pos_y,
                                                      GOAL_POS_X,GOAL_POS_Y):
            ball_toward_goal = False
    is_tackleable_opp = is_tackleable(agent_pos_x, agent_pos_y,
                                      ball_sorted_list[0][1],
                                    ball_sorted_list[0][2], ball_sorted_list[0][3])

    agent_to_ball_dist = get_dist_normalized(agent_pos_x, agent_pos_y,
                                             ball_pos_x, ball_pos_y)

    if state_vec[5] > 0: # kickable distance of player
        misc_tracked['max_kickable_dist'] = max(agent_to_ball_dist,misc_tracked['max_kickable_dist'])
        if is_tackleable_opp:
            hfo_env.act(add_num_times(hfo.MOVE,num_times_overall,num_times_kickable)) # will do tackle
        elif ball_nearer_goal:
            hfo_env.act(add_num_times(hfo.REDUCE_ANGLE_TO_GOAL,num_times_overall,num_times_kickable))
        elif ball_toward_goal:
            hfo_env.act(add_num_times(hfo.INTERCEPT,num_times_overall,num_times_kickable))
        else:
            hfo_env.act(add_num_times(hfo.GO_TO_BALL,num_times_overall,num_times_kickable))
        return

    if goal_sorted_list[0][0] != ball_sorted_list[0][0]:
        if is_in_open_area(ball_sorted_list[0][2],
                       ball_sorted_list[0][3]) and is_in_open_area(goal_sorted_list[0][2],
                                                                   goal_sorted_list[0][3]):
            if ball_sorted_list[0][1] < params['LOW_KICK_DIST']:
                hfo_env.act(add_num_times(hfo.MARK_PLAYER,num_times_overall),
                            goal_sorted_list[0][0])
            elif agent_to_ball_dist < ball_sorted_list[0][1]:
                if ball_nearer_goal:
                    hfo_env.act(add_num_times(hfo.REDUCE_ANGLE_TO_GOAL,num_times_overall))
                elif ball_toward_goal:
                    hfo_env.act(add_num_times(hfo.INTERCEPT,num_times_overall))
                else:
                    hfo_env.act(add_num_times(hfo.GO_TO_BALL,num_times_overall))
            else:
                hfo_env.act(add_num_times(hfo.REDUCE_ANGLE_TO_GOAL,num_times_overall))
    
        elif ball_sorted_list[0][1] >= params['KICK_DIST']:
            if agent_to_ball_dist < ball_sorted_list[0][1]:
                if ball_nearer_goal:
                    hfo_env.act(add_num_times(hfo.REDUCE_ANGLE_TO_GOAL,num_times_overall))
                elif ball_toward_goal:
                    hfo_env.act(add_num_times(hfo.INTERCEPT,num_times_overall))
                else:
                    hfo_env.act(add_num_times(hfo.GO_TO_BALL,num_times_overall))
            else:
                hfo_env.act(add_num_times(hfo.REDUCE_ANGLE_TO_GOAL,num_times_overall))
    
            elif is_tackleable_opp and (not is_in_open_area(ball_sorted_list[0][2],
                                                    ball_sorted_list[0][3])):
                hfo_env.act(add_num_times(hfo.MOVE,num_times_overall))
    
    
        elif ball_sorted_list[0][1] < (1*params['LOW_KICK_DIST']):
            hfo_env.act(add_num_times(hfo.MARK_PLAYER,num_times_overall),goal_sorted_list[0][0])
        else:
            hfo_env.act(add_num_times(hfo.REDUCE_ANGLE_TO_GOAL,num_times_overall))
        return

    if is_in_open_area(ball_sorted_list[0][2],ball_sorted_list[0][3]):
        if ball_sorted_list[0][1] < params['KICK_DIST']:
        hfo_env.act(add_num_times(hfo.REDUCE_ANGLE_TO_GOAL,num_times_overall))
        elif agent_to_ball_dist < params['KICK_DIST']:
        if ball_nearer_goal:
            hfo_env.act(add_num_times(hfo.REDUCE_ANGLE_TO_GOAL,num_times_overall))
        elif ball_toward_goal:
            hfo_env.act(add_num_times(hfo.INTERCEPT,num_times_overall))
        else:
            hfo_env.act(add_num_times(hfo.GO_TO_BALL,num_times_overall))
        elif is_tackleable_opp:
        hfo_env.act(add_num_times(hfo.MOVE,num_times_overall))
        else:
        hfo_env.act(add_num_times(hfo.REDUCE_ANGLE_TO_GOAL,num_times_overall))
    else:
        if ball_sorted_list[0][1] >= max(params['KICK_DIST'],agent_to_ball_dist):
        if ball_nearer_goal:
            hfo_env.act(add_num_times(hfo.REDUCE_ANGLE_TO_GOAL,num_times_overall))
        elif ball_toward_goal:
            hfo_env.act(add_num_times(hfo.INTERCEPT,num_times_overall))
        else:
            hfo_env.act(add_num_times(hfo.GO_TO_BALL,num_times_overall))
        elif ball_sorted_list[0][1] >= params['KICK_DIST']:
        hfo_env.act(add_num_times(hfo.REDUCE_ANGLE_TO_GOAL,num_times_overall))
        elif is_tackleable_opp:
        hfo_env.act(add_num_times(hfo.MOVE,num_times_overall))
        else:
        hfo_env.act(add_num_times(hfo.REDUCE_ANGLE_TO_GOAL,num_times_overall))
    return



def do_random_defense_action(state, hfo_env):
  if state[5] > 0: # kickable
    hfo_env.act(hfo.MOVE)
  else:
    if random.random() < 0.25:
      hfo_env.act(hfo.REDUCE_ANGLE_TO_GOAL)
    else:
      hfo_env.act(hfo.MOVE)
  return