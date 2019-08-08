"""
  \ file kick_table.py
  \ brief kick table class File to generate smart kick.
"""
import functools

# from typing import List, Any, Union
from lib.debug.level import Level
from lib.debug.logger import dlog
from lib.player.world_model import *
from lib.rcsc.player_type import *
from lib.rcsc.server_param import *
from lib.math.soccer_math import *
from lib.rcsc.game_time import *
from enum import Enum

"""
  \ enum Flag
  \ brief status bit flags
"""

"""
      \ brief compare operation function
      \ param item1 left hand side variable
      \ param item2 right hand side variable
      \ return compared result
"""


def TableCmp(item1, item2) -> bool:
    if item1.max_speed_ == item2.max_speed_:
        return item1.power_ < item2.power_

    return item1.max_speed_ > item2.max_speed_


def SequenceCmp(item1, item2) -> bool:
    return item1.score_ < item2.score_


class Flag(Enum):
    SAFETY = 0x0000
    NEXT_TACKLEABLE = 0x0001
    NEXT_KICKABLE = 0x0002
    TACKLEABLE = 0x0004
    KICKABLE = 0x0008
    SELF_COLLISION = 0x0010
    RELEASE_INTERFERE = 0x0020
    MAYBE_RELEASE_INTERFERE = 0x0040
    OUT_OF_PITCH = 0x0080
    KICK_MISS_POSSIBILITY = 0x0100


NEAR_SIDE_RATE = 0.3  # < kickable margin rate for the near side sub-target
MID_RATE = 0.5  # < kickable margin rate for the middle distance sub-target
FAR_SIDE_RATE = 0.7  # < kickable margin rate for the far side sub-target
MAX_DEPTH = 2
STATE_DIVS_NEAR = 8
STATE_DIVS_MID = 12
STATE_DIVS_FAR = 15
NUM_STATE = STATE_DIVS_NEAR + STATE_DIVS_MID + STATE_DIVS_FAR

DEST_DIR_DIVS: int = 72  # step: 5 degree

MAX_TABLE_SIZE: int = 128

"""
  \ class State
  \ brief class to represent a kick intermediate state
"""


class State:
    # < index of self point
    # < distance from self
    # < position relative to player's body
    # < kick rate
    # < status bit flag

    """
      \ brief construct an illegal state object
        OR
      \ brief construct a legal state object. flag is set to SAFETY.
      \ param index index number of self state
      \ param dist distance from self
      \ param pos global position
      \ param kick_rate kick rate at self state
     """

    def __init__(self, *args):
        if len(args) == 0:
            self.index_ = -1
            self.dist_ = 0.0
            self.kick_rate_ = 0.0
            self.flag_ = 0xFFFF
        else:
            self.index_ = args[0]
            self.dist_ = args[1]
            self.pos_ = args[2]
            self.kick_rate_ = args[3]
            self.flag_ = Flag.SAFETY


"""
  \ class Path
  \ brief used as a heuristic knowledge. path representation between two states
"""


class Path:
    # < index of origin state
    # < index of destination state
    # < reachable ball max speed
    # < kick power to generate max_speed_

    """
      \ brief construct a kick path object
      \ param origin index of origin state
      \ param destination index of destination state
     """

    def __init__(self, origin=0, destination=0):
        self.origin_ = origin
        self.dest_ = destination
        self.max_speed_ = 0.0
        self.power_ = 1000.0

    """
      \ class Sequence
      \ brief simulated kick sequence
     """


class Sequence:
    # < safety level flags. usually the combination of State flags
    # not < ball positions
    # < released ball speed
    # < estimated last kick power
    # < evaluated score of self sequence

    """
      \ brief construct an illegal sequence object
        OR
      \ brief copy constructor
      \ param arg another instance
     """

    def __init__(self, *args):
        if len(args) == 0:
            self.flag_ = 0x0000
            self.pos_list_ = []
            self.speed_ = 0.0
            self.power_ = 10000.0
            self.score_ = 0.0
        if len(args) == 1:
            self.flag_ = args[0].flag_
            self.pos_list_ = args[0].pos_list_
            self.speed_ = args[0].speed_
            self.power_ = args[0].power_
            self.score_ = args[0].score_


"""
 \ brief calculate the distance of near side sub-target
 \ param player_type calculated PlayerType
 \ return distance from the center of the player
"""


def calc_near_dist(player_type: PlayerType):
    #       0.3 + 0.6*0.3 + 0.085 = 0.565
    # near: 0.3 + 0.7*0.3 + 0.085 = 0.595
    #       0.3 + 0.8*0.3 + 0.085 = 0.625
    return bound(player_type.player_size() + ServerParam.i().ball_size() + 0.1,
                 (player_type.player_size()
                  + (player_type.kickable_margin() * NEAR_SIDE_RATE)
                  + ServerParam.i().ball_size()),
                 player_type.kickable_area() - 0.2)


"""
  \ brief calculate the distance of middle distance sub-target
  \ param player_type calculated PlayerType
  \ return distance from the center of the player
"""


def calc_mid_dist(player_type: PlayerType):
    #      0.3 + 0.6*0.5 + 0.085 = 0.705
    # mid: 0.3 + 0.7*0.5 + 0.085 = 0.735
    #      0.3 + 0.8*0.5 + 0.085 = 0.765
    return bound(player_type.player_size() + ServerParam.i().ball_size() + 0.1,
                 (player_type.player_size()
                  + (player_type.kickable_margin() * MID_RATE)
                  + ServerParam.i().ball_size()),
                 player_type.kickable_area() - 0.2)


"""
  \ brief calculate the distance of far side sub-target
  \ param player_type calculated PlayerType
  \ return distance from the center of the player
"""


def calc_far_dist(player_type: PlayerType):
    #      0.3 + 0.6*0.7 + 0.085 = 0.865 (=0.985-0.12 . 0.785)
    # far: 0.3 + 0.7*0.7 + 0.085 = 0.875 (=1.085-0.21)
    #      0.3 + 0.8*0.7 + 0.085 = 0.945 (=1.185-0.24)

    #      0.3 + 0.6*0.68 + 0.085 = 0.793 (=0.985-0.192 . 0.760)
    # far: 0.3 + 0.7*0.68 + 0.085 = 0.861 (=1.085-0.224 . 0.860)
    #      0.3 + 0.8*0.68 + 0.085 = 0.929 (=1.185-0.256)

    #      0.3 + 0.6*0.675 + 0.085 = 0.79   (=0.985-0.195)
    # far: 0.3 + 0.7*0.675 + 0.085 = 0.8575 (=1.085-0.2275)
    #      0.3 + 0.8*0.675 + 0.085 = 0.925  (=1.185-0.26)

    return bound(player_type.player_size() + ServerParam.i().ball_size() + 0.1,
                 (player_type.player_size()
                  + (player_type.kickable_margin() * FAR_SIDE_RATE)
                  + ServerParam.i().ball_size()),
                 player_type.kickable_area() - 0.2)
    # player_type.kickable_area() - 0.22 )


"""
  \ brief calculate maximum velocity for the target angle by one step kick with krate and ball_vel
  \ param target_angle target angle of the next ball velocity
  \ param krate current kick rate
  \ param ball_vel current ball velocity
  \ return maximum velocity for the target angle
 """


def calc_max_velocity(target_angle: AngleDeg,
                      krate,
                      ball_vel: Vector2D):
    ball_speed_max2 = pow(ServerParam.i().ball_speed_max(), 2)
    max_accel = min(ServerParam.i().max_power() * krate,
                    ServerParam.i().ball_accel_max())

    desired_ray = Ray2D(Vector2D(0.0, 0.0), target_angle)
    next_reachable_circle = Circle2D(ball_vel, max_accel)

    num = next_reachable_circle.intersection(desired_ray)
    vel1 = num[1]
    vel2 = num[2]
    if num[0] == 0:
        return Vector2D(0.0, 0.0)

    if num[0] == 1:
        if vel1.r2() > ball_speed_max2:
            # next inertia ball point is within reachable circle.
            if next_reachable_circle.contains(Vector2D(0.0, 0.0)):
                # can adjust angle at least
                vel1.setLength(ServerParam.i().ball_speed_max())

            else:
                # failed
                vel1.assign(0.0, 0.0)

        return vel1

    #
    # num == 2
    #   ball reachable circle does not contain the current ball pos.

    length1 = vel1.r2()
    length2 = vel2.r2()

    if length1 < length2:
        vel1, vel2 = vel2, vel1
        length1, length2 = length2, length1

    if length1 > ball_speed_max2:
        if length2 > ball_speed_max2:
            # failed
            vel1.assign(0.0, 0.0)

        else:
            vel1.setLength(ServerParam.i().ball_speed_max())

    return vel1


class _KickTable:

    def __init__(self):
        self._player_size = 0.0
        self._kickable_margin = 0.0
        self._ball_size = 0.0
        self._state_cache = []
        for i in range(MAX_DEPTH):
            self._state_cache.append([])
            for j in range(NUM_STATE):
                self._state_cache[i].append(0.0)
        # not  static state list
        self._state_list = list[State]
        self._tables = list[Path]

        for i in range(DEST_DIR_DIVS):
            self._tables.append([])

        self._current_state = State()

        self._state_cache = list[State]

        self._candidates = list[Sequence]

    """
    \ brief create heuristic table
    \ return result of table creation
    """

    def createTables(self):
        player_type = PlayerType()  # default type

        if (math.fabs(self._player_size - player_type.player_size()) < EPS
                and math.fabs(self._kickable_margin - player_type.kickable_margin()) < EPS
                and math.fabs(self._ball_size - ServerParam.i().ball_size()) < EPS):
            return False

        self._player_size = player_type.player_size()
        self._kickable_margin = player_type.kickable_margin()
        self._ball_size = ServerParam.i().ball_size()

        self.createStateList(player_type)

        angle_step = 360.0 / DEST_DIR_DIVS

        angle = -180.0

        for i in range(DEST_DIR_DIVS):
            angle += angle_step
            self.createTable(angle, self._tables[i])

        return True

    """
      \ brief create static state list
    """

    def createStateList(self, player_type: PlayerType):
        near_dist = calc_near_dist(player_type)
        mid_dist = calc_mid_dist(player_type)
        far_dist = calc_far_dist(player_type)

        near_angle_step = 360.0 / STATE_DIVS_NEAR
        mid_angle_step = 360.0 / STATE_DIVS_MID
        far_angle_step = 360.0 / STATE_DIVS_FAR

        index = 0
        self._state_list.clear()

        for near in range(STATE_DIVS_NEAR):
            angle = AngleDeg(-180.0 + (near_angle_step * near))
            pos = Vector2D.polar2vector(near_dist, angle)
            krate = player_type.kick_rate(near_dist, angle.degree())
            self._state_list.append(State(index, near_dist, pos, krate))
            index += 1

        for mid in range(STATE_DIVS_MID):
            angle = AngleDeg(-180.0 + (mid_angle_step * mid))
            pos = Vector2D.polar2vector(mid_dist, angle)
            krate = player_type.kick_rate(mid_dist, angle.degree())
            self._state_list.append(State(index, mid_dist, pos, krate))
            index += 1

        for far in range(STATE_DIVS_FAR):
            angle = AngleDeg(-180.0 + (far_angle_step * far))
            pos = Vector2D.polar2vector(far_dist, angle)
            krate = player_type.kick_rate(far_dist, angle.degree())
            self._state_list.append(State(index, far_dist, pos, krate))
            index += 1

    """
      \ brief create table for angle
      \ param angle target angle relative to body angle
      \ param table reference to the container variable
     """

    def createTable(self, angle: AngleDeg, table):

        max_combination = NUM_STATE * NUM_STATE
        max_state = len(self._state_list)

        table.clear()
        table.reserve(max_combination)
        for origin in range(max_state):
            for dest in range(max_state):
                vel = self._state_list[dest].pos_ - self._state_list[origin].pos_
                max_vel = calc_max_velocity(angle,
                                            self._state_list[dest].kick_rate_,
                                            vel)
                accel = max_vel - vel
                path = Path(origin, dest)

                path.max_speed_ = max_vel.r()
                path.power_ = accel.r() / self._state_list[dest].kick_rate_
                table.push_back(path)

        table.sort(key=functools.cmp_to_key(TableCmp))

        if len(table) > MAX_TABLE_SIZE:
            table.erase(table.begin() + MAX_TABLE_SIZE,
                        table.end())

    """
      \ brief update internal state
      \ param world  reference to the WorldModel
     """

    def updateState(self, world: WorldModel):

        if KickTable.S_UPDATE_TIME == world.time():
            return

        KickTable.S_UPDATE_TIME = world.time()

        self.createStateCache(world)

    """
      \ brief implementation of the state update
      \ param world  reference to the WorldModel
     """

    def createStateCache(self, world: WorldModel):

        param = ServerParam.i()
        pitch = Rect2D(Vector2D(- param.pitch_half_length(), - param.pitch_half_width()), Size2D(param.pitch_length(),
                                                                                                 param.pitch_width()))
        self_type = world.self().player_type()
        near_dist = calc_near_dist(self_type)
        mid_dist = calc_mid_dist(self_type)
        far_dist = calc_far_dist(self_type)

        rpos = world.ball().rpos()
        rpos.rotate(- world.self().body())

        dist = rpos.r()
        angle = rpos.th()

        if math.fabs(dist - near_dist) < math.fabs(dist - far_dist):
            dir_div = STATE_DIVS_NEAR
        else:
            dir_div = STATE_DIVS_FAR

        self._current_state.index_ = (rint(dir_div * rint(angle.degree() + 180.0) / 360.0))  # TODO : STATIC CAST
        if self._current_state.index_ >= dir_div:
            self._current_state.index_ = 0

        # self._current_state.pos_ = world.ball().rpos()
        self._current_state.pos_ = world.ball().pos()
        self._current_state.kick_rate_ = world.self().kick_rate()

        self.checkInterfereAt(world, 0, self._current_state)

        #
        # create future state
        #

        self_pos = world.self().pos()
        self_vel = world.self().vel()

        for i in range(MAX_DEPTH):
            self._state_cache[i].clear()

            self_pos += self_vel
            self_vel *= self_type.playerDecay()

            index = 0
            for near in range(STATE_DIVS_NEAR):
                pos = self._state_list[index].pos_
                krate = self_type.kickRate(near_dist, pos.th().degree())

                pos.rotate(world.self().body())
                pos.setLength(near_dist)
                pos += self_pos

                self._state_cache[i].push_back(State(index, near_dist, pos, krate))
                self.checkInterfereAt(world, i + 1, self._state_cache[i].back())
                if not pitch.contains(pos):
                    self._state_cache[i].back().flag_ |= Flag.OUT_OF_PITCH

                index += 1

            for mid in range(STATE_DIVS_MID):
                pos = self._state_list[index].pos_
                krate = self_type.kickRate(mid_dist, pos.th().degree())

                pos.rotate(world.self().body())
                pos.setLength(mid_dist)
                pos += self_pos

                self._state_cache[i].push_back(State(index, mid_dist, pos, krate))
                self.checkInterfereAt(world, i + 1, self._state_cache[i].back())
                if not pitch.contains(pos):
                    self._state_cache[i].back().flag_ |= Flag.OUT_OF_PITCH

                index += 1

            for far in range(STATE_DIVS_FAR):
                pos = self._state_list[index].pos_
                krate = self_type.kickRate(far_dist, pos.th().degree())

                pos.rotate(world.self().body())
                pos.setLength(far_dist)
                pos += self_pos

                self._state_cache[i].push_back(State(index, far_dist, pos, krate))
                self.checkInterfereAt(world, i + 1, self._state_cache[i].back())
                if not pitch.contains(pos):
                    self._state_cache[i].back().flag_ |= Flag.OUT_OF_PITCH

                index += 1

    """
      \ brief update collision flag of state caches for the target_point and first_speed
      \ param world  reference to the WorldModel
      \ param target_point kick target point
      \ param first_speed required first speed
     """

    def checkCollisionAfterRelease(self, world: WorldModel, target_point: Vector2D, first_speed):

        self_type = world.self().player_type()

        collide_dist2 = pow(self_type.player_size() + ServerParam.i().ball_size(), 2)

        self_pos = world.self().pos()
        self_vel = world.self().vel()

        # check the release kick from current state

        self_pos += self_vel
        self_vel *= self_type.player_decay()

        release_pos = (target_point - self._current_state.pos_)
        release_pos.setLength(first_speed)

        if self_pos.dist2(release_pos) < collide_dist2:

            self._current_state.flag_ |= Flag.SELF_COLLISION

        else:

            self._current_state.flag_ &= ~Flag.SELF_COLLISION

        # check the release kick from future state

        for i in range(MAX_DEPTH):
            self_pos += self_vel
            self_vel *= self_type.playerDecay()

            for it in self._state_cache[i]:
                release_pos = (target_point - it.pos_)
                release_pos.setLength(first_speed)

                if self_pos.dist2(release_pos) < collide_dist2:

                    it.flag_ |= Flag.SELF_COLLISION
                else:
                    it.flag_ &= ~Flag.SELF_COLLISION

    """
      \ brief update interfere level at state
      \ param world  reference to the WorldModel
      \ param cycle the cycle delay for state
      \ param state reference to the State variable to be updated
    """

    @staticmethod
    def checkInterfereAt(world: WorldModel,
                         cycle,  # not needed
                         state: State):
        cycle += 0  # TODO : Check need
        penalty_area = Rect2D(Vector2D(ServerParam.i().their_penalty_area_line_x(),
                                       - ServerParam.i().penalty_area_half_width()),
                              Size2D(ServerParam.i().penalty_area_length(),
                                     ServerParam.i().penalty_area_width()))
        flag = 0x0000
        OFB = world.opponents_from_ball()

        for o in OFB:
            if o.pos_count() >= 8:
                continue
            if o.is_ghost():
                continue
            if o.dist_from_ball() > 10.0:
                break

            opp_next = o.pos() + o.vel()
            opp_dist = opp_next.dist(state.pos_)

            if o.is_tackling():
                if opp_dist < (o.playerTypePtr().player_size()
                               + ServerParam.i().ball_size()):
                    flag |= Flag.KICKABLE
                    break

                continue

            control_area = o.player_type.catch_able_area() if (
                    o.goalie() and penalty_area.contains(o.pos()) and penalty_area.contains(state.pos_
                                                                                            )) else o.player_type().kick_able_area()

            #
            # check kick possibility
            #
            if not o.isGhost() and o.posCount() <= 2 and opp_dist < control_area + 0.15:
                flag |= Flag.KICKABLE
                break

            opp_body = o.body() if o.bodyCount() <= 1 else (state.pos_ - opp_next).th()
            player_2_pos = Vector2D(state.pos_ - opp_next)
            player_2_pos.rotate(- opp_body)
            #
            # check tackle possibility
            #
            tackle_dist = ServerParam.i().tackle_dist() if player_2_pos.x() > 0.0 else ServerParam.i().tackle_back_dist()
            if tackle_dist > EPSILON:
                tackle_prob = (pow(player_2_pos.absX() / tackle_dist,
                                   ServerParam.i().tackle_exponent()) + pow(
                    player_2_pos.absY() / ServerParam.i().tackle_width(),
                    ServerParam.i().tackle_exponent()))
                if tackle_prob < 1.0 and 1.0 - tackle_prob > 0.7:  # success probability
                    flag |= Flag.TACKLABLE

                    # check kick or tackle possibility after dash

            player_type = o.player_type()
            max_accel = (ServerParam.i().max_dash_power()
                         * player_type.dash_power_rate()
                         * player_type.effort_max())

            if player_2_pos.absY() < control_area and (
                    player_2_pos.absX() < max_accel or (player_2_pos + Vector2D(max_accel, 0.0)).r() < control_area or (
                    player_2_pos - Vector2D(max_accel, 0.0)).r() < control_area):
                flag |= Flag.NEXT_KICKABLE
            elif (player_2_pos.absY() < ServerParam.i().tackle_width() * 0.7
                  and player_2_pos.x() > 0.0
                  and player_2_pos.x() - max_accel < ServerParam.i().tackle_dist() - 0.3):
                flag |= Flag.NEXT_TACKLABLE

        state.flag_ = flag

    """
      \ brief update interfere level after release kick for all states
      \ param world  reference to the WorldModel
      \ param target_point kick target point
      \ param first_speed required first speed
      \ brief update interfere level after release kick for each state
      \ param world  reference to the WorldModel
      \ param target_point kick target point
      \ param first_speed required first speed
      \ param cycle the cycle delay for state
      \ param state reference to the State variable to be updated
    """

    def checkInterfereAfterRelease(self, *args):  # , **kwargs):):
        if len(args) == 3:
            world: WorldModel = args[0]
            target_point: Vector2D = args[1]
            first_speed: float = args[2]
            self.checkInterfereAfterRelease(world, target_point, first_speed, 1, self._current_state)

            for i in range(MAX_DEPTH):
                for state in self._state_cache[i]:
                    state.flag_ &= ~Flag.RELEASE_INTERFERE
                    state.flag_ &= ~Flag.MAYBE_RELEASE_INTERFERE

                    self.checkInterfereAfterRelease(world, target_point, first_speed, i + 2, state)
        elif len(args) == 5:
            world: WorldModel = args[0]
            target_point: Vector2D = args[1]
            first_speed: float = args[2]
            cycle: int = args[3],
            state: State = args[4]

            penalty_area = Rect2D(Vector2D(ServerParam.i().their_penalty_area_line_x(),
                                           - ServerParam.i().penalty_area_half_width()),
                                  Size2D(ServerParam.i().penalty_area_length(),
                                         ServerParam.i().penalty_area_width()))

            ball_pos = target_point - state.pos_
            ball_pos.setLength(first_speed)
            ball_pos += state.pos_

            OFB = world.opponents_from_ball()

            for o in OFB:
                if o.pos_count() >= 8:
                    continue
                if o.is_ghost():
                    continue
                if o.dist_from_ball() > 10.0:
                    break
                opp_pos = o.inertia_point(cycle)
                if not opp_pos.is_valid():
                    opp_pos = o.pos() + o.vel()

                if o.isTackling():
                    if opp_pos.dist(ball_pos) < (o.player_type().player_size() + ServerParam.i().ball_size()):
                        state.flag_ |= Flag.RELEASE_INTERFERE
                    continue
                control_area = o.player_type.catch_able_area() if (
                        o.goalie() and penalty_area.contains(o.pos()) and penalty_area.contains(
                    state.pos_)) else o.player_type().kick_able_area()

                control_area += 0.1
                control_area2 = pow(control_area, 2)

                if ball_pos.dist2(opp_pos) < control_area2:
                    if cycle <= 1:
                        state.flag_ |= Flag.RELEASE_INTERFERE

                    else:
                        state.flag_ |= Flag.RELEASE_INTERFERE
                else:  # if  cycle <= 1 :
                    opp_body = o.body() if o.body_count() <= 1 else (ball_pos - opp_pos).th()
                    player_2_pos = ball_pos - opp_pos
                    player_2_pos.rotate(- opp_body)

                    tackle_dist = ServerParam.i().tackle_dist() if player_2_pos.x > 0.0 else ServerParam.i().tackle_back_dist()
                    if tackle_dist > EPSILON:
                        tackle_prob = (pow(player_2_pos.absX() / tackle_dist,
                                           ServerParam.i().tackle_exponent()) + pow(
                            player_2_pos.absY() / ServerParam.i().tackle_width(),
                            ServerParam.i().tackle_exponent()))
                        if tackle_prob < 1.0 and 1.0 - tackle_prob > 0.8:  # success probability
                            state.flag_ |= Flag.MAYBE_RELEASE_INTERFERE
                    player_type = o.player_type()
                    max_accel = (ServerParam.i().max_dash_power()
                                 * player_type.dash_power_rate()
                                 * player_type.effort_max()) * 0.8
                    if (player_2_pos.absY() < control_area - 0.1
                            and (player_2_pos.absX() < max_accel
                                 or (player_2_pos + Vector2D(max_accel, 0.0)).r() < control_area - 0.25
                                 or (player_2_pos - Vector2D(max_accel, 0.0)).r() < control_area - 0.25)):
                        state.flag_ |= Flag.MAYBE_RELEASE_INTERFERE

                    elif (player_2_pos.absY() < ServerParam.i().tackle_width() * 0.7
                          and player_2_pos.x - max_accel < ServerParam.i().tackle_dist() - 0.5):
                        state.flag_ |= Flag.MAYBE_RELEASE_INTERFERE

    """
      \ brief simulate one step kick
      \ param world  reference to the WorldModel
      \ param target_point kick target point
      \ param first_speed required first speed
     """

    #
    # def simulateOneStep(self, world: WorldModel,
    #                     target_point:‌
    #
    #
    # Vector2D,
    # first_speed ):

    """
      \ brief simulate two step kicks
      \ param world  reference to the WorldModel
      \ param target_point kick target point
      \ param first_speed required first speed
     """

    # def simulateTwoStep(self, world‌
    #
    # :‌WorldModel,
    #   target_point:‌Vector2D,
    #                 first_speed ):

    """
      \ brief simulate three step kicks
      \ param world  reference to the WorldModel
      \ param target_point kick target point
      \ param first_speed required first speed
     """

    #
    # def simulateThreeStep(self, world: WorldModel,
    #                       target_point: Vector2D,
    #                       first_speed):

    """
      \ brief evaluate candidate kick sequences
      \ param first_speed required first speed
      \ param allowable_speed required first speed threshold
     """

    def evaluate(self, first_speed, allowable_speed):
        power_thr1 = ServerParam.i().max_power() * 0.94
        power_thr2 = ServerParam.i().max_power() * 0.9
        for it in self._candidates:
            n_kick = len(it.pos_list_)

            it.score_ = 1000.0

            if it.speed_ < first_speed:
                if n_kick > 1 or it.speed_ < allowable_speed:
                    it.score_ = -10000.0
                    it.score_ -= (first_speed - it.speed_) * 100000.0

                else:
                    it.score_ -= 50.0

            if it.flag_ & Flag.TACKLABLE:
                it.score_ -= 500.0

            if it.flag_ & Flag.NEXT_TACKLABLE:
                it.score_ -= 300.0

            if it.flag_ & Flag.NEXT_KICKABLE:
                it.score_ -= 600.0

            if it.flag_ & Flag.MAYBE_RELEASE_INTERFERE:
                if n_kick == 1:
                    it.score_ -= 250.0

                else:
                    it.score_ -= 200.0

            if n_kick == 3:
                it.score_ -= 200.0

            elif n_kick == 2:
                it.score_ -= 50.0

            if n_kick > 1:
                if it.power_ > power_thr1:
                    it.score_ -= 75.0

                elif it.power_ > power_thr2:
                    it.score_ -= 25.0

            it.score_ -= it.power_ * 0.5

            if it.flag_ & Flag.KICK_MISS_POSSIBILITY:
                it.score_ -= 30.0

    """
    \ brief simulate kick sequence
    \ param world  reference to the WorldModel
    \ param target_point kick target point
    \ param first_speed required first speed
    \ param allowable_speed required first speed threshold
    \ param max_step maximum size of kick sequence
    \ param sequence reference to the result variable
    \ return if successful kick is found, True, False is returned but kick sequence is generated anyway.
    """

    def simulate(self, world, target_point: Vector2D, first_speed, allowable_speed, max_step, sequence: Sequence):

        if self._state_list.empty():
            return False

        target_speed = bound(0.0,
                             first_speed,
                             ServerParam.i().ball_speed_max())
        speed_thr = bound(0.0,
                          allowable_speed,
                          target_speed)

        self._candidates.clear()

        self.updateState(world)

        self.checkCollisionAfterRelease(world,
                                        target_point,
                                        target_speed)
        self.checkInterfereAfterRelease(world,
                                        target_point,
                                        target_speed)

        if (max_step >= 1
                and self.simulateOneStep(world,
                                         target_point,
                                         target_speed)):
            dlog.add_text(Level.KICK, "simulate() found 1 step")
        if (max_step >= 2
                and self.simulateTwoStep(world,
                                         target_point,
                                         target_speed)):
            dlog.add_text(Level.KICK, "simulate() found 2 step")
        if (max_step >= 3
                and self.simulateThreeStep(world,
                                           target_point,
                                           target_speed)):
            dlog.add_text(Level.KICK, "simulate() found 3 step")

        self.evaluate(target_speed, speed_thr)

        if self._candidates.empty():
            return False
        # sequence = self._candidates[0]
        sequence = max(self._candidates, key=functools.cmp_to_key(SequenceCmp))

        """
            dlog.addText( Logger.KICK,
                          __FILE__": simulate() result next_pos=(%.2f %.2f)  flag=%x n_kick=%d speed=%.2f power=%.2f score=%.2f",
                          sequence.pos_list_.front().x,
                          sequence.pos_list_.front().y,
                          sequence.flag_,
                          (int)sequence.pos_list_.size(),
                          sequence.speed_,
                          sequence.power_,
                          sequence.score_ )
        """
        return sequence.speed_ >= target_speed - EPS

    """
    \ brief get the candidate kick sequences
    \ return  reference to the container of Sequence
    """

    def candidates(self):
        return self.candidates


"""
  \ brief singleton interface
  \ return reference to the singleton instance
 """


class KickTable:
    S_UPDATE_TIME = GameTime(-1, 0)

    _instance: _KickTable = _KickTable()

    @staticmethod
    def instance() -> _KickTable:
        return KickTable._instance
