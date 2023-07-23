from base import goalie_decision
from base.strategy_formation import StrategyFormation
from base.set_play.bhv_set_play import Bhv_SetPlay
from base.bhv_kick import BhvKick
from base.bhv_move import BhvMove
from lib.action.neck_scan_field import NeckScanField
from lib.action.neck_scan_players import NeckScanPlayers
from lib.action.neck_turn_to_ball import NeckTurnToBall
from lib.action.neck_turn_to_ball_or_scan import NeckTurnToBallOrScan
from lib.action.scan_field import ScanField
from lib.debug.debug import log
from lib.messenger.ball_pos_vel_messenger import BallPosVelMessenger
from lib.messenger.player_pos_unum_messenger import PlayerPosUnumMessenger
from lib.rcsc.types import GameModeType, ViewWidth, UNUM_UNKNOWN
from lib.action.hold_ball import HoldBall
from lib.action.turn_to_ball import TurnToBall
from lib.action.go_to_point import GoToPoint
from lib.action.neck_body_to_point import NeckBodyToPoint
from lib.action.neck_body_to_ball import NeckBodyToBall
from base.basic_tackle import BasicTackle
from lib.player_command.player_command import CommandType
from lib.rcsc.server_param import ServerParam


from pyrusgeom.soccer_math import *
from pyrusgeom.rect_2d import Rect2D
from pyrusgeom.vector_2d import Vector2D
from pyrusgeom.geom_2d import *

from typing import TYPE_CHECKING

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
        return BhvKick().execute(agent)
    if BhvMove().execute(agent):
        return True
    log.os_log().warn("NO ACTION, ScanFIELD")
    return ScanField().execute(agent)


## TODO: 2021-07-20 17:10:00 keepaway modification


def keepaway_decision(agent: "PlayerAgent"):
    # pylint: disable=wildcard-import, method-hidden
    # pylint: enable=too-many-lines

    wm: "WorldModel" = agent.world()

    def _predict_player_pos(wm, agent, cycle, dash_power):
        """Predict the player position given a dash command."""
        ss = ServerParam.i()

        # p = self.world().self()
        dash_dir = agent._last_body_command[-1].dash_dir()
        dash_dir.normalize()
        angle = agent.body()
        power = dash_power * ss._player_decay() * cycle  ## pow
        p_vel = Vector2D.polar2vector(power, angle)
        p_pos = agent.pos() + p_vel
        return p_pos, p_vel

    def _predict_ball(wm, agent):
        """Predict the ball position and velocity given a kick command."""
        ss = ServerParam.i()

        ball_pos = wm.ball().pos()
        ball_vel = wm.ball().vel()

        if agent._last_body_command[-1] is CommandType.KICK:
            kick_power = agent._last_body_command[-1].kick_power()
            kick_dir = agent._last_body_command[-1].kick_dir()
            kick_dir.normalize()
            angle = ball_pos.th()
            power = kick_power * ss.ball_decay()
            ball_vel += Vector2D.polar2vector(power, angle)
            ball_pos += ball_vel

        return ball_pos, ball_vel

    def _keeper_support(wm, teammate):
        # fastest = wm.intercept_table().fastest_teammate()
        # int iCycles = WM->predictNrCyclesToObject( fastest, OBJECT_BALL )
        # VecPosition posPassFrom = WM->predictPosAfterNrCycles( OBJECT_BALL, iCycles )

        ## position to pass from the fastest teammate.
        # wm.intercept_table().predict_teammate(self)
        pos_pass_from = wm.intercept_table().fastest_teammate().pos()

        ## fix the position to pass from to be in the keep-away rectangle
        rect = wm._get_keepaway_rec("real")
        wm._get_open_for_pass_from_in_rectangle(rect, pos_pass_from, teammate)
        # ObjectT lookObject = self._choose_look_object( 0.97 )

        return NeckBodyToPoint(rect.center()).execute(agent)

    def _interpret_keeper_action(action):
        if action == 0:
            ## interpret HOLD action
            return HoldBall().execute(agent)
        elif action == 1:
            ## TODO:
            ## Normal Passing
            # ACT->putCommandInQueue( soc = directPass( tmPos, PASS_NORMAL ) )
            ## Or Fast Passing
            # ACT->putCommandInQueue( soc = directPass( tmPos, PASS_FAST ) );

            ## interpret PASS action
            return BhvKick().execute(agent)

    log.sw_log().team().add_text(
        f"is kickable? dist {wm.ball().dist_from_self()} "
        f"ka {wm.self().player_type().kickable_area()} "
        f"seen pos count {wm.ball().seen_pos_count()} "
        f"is? {wm.self()._kickable}"
    )

    ## Implementations of keeper with the ball
    action = None

    if wm.self().is_kickable():
        MAX_STATE_VARS = 100000000
        state = wm._retrieve_observation()
        print("state", state)
        if len(state) > 0:
            ## if we can calculate state vars
            ## Call startEpisode() on the first SMDP step.
            action = 0
            # if wm._get_last_action_time() == UNUM_UNKNOWN:
            #     action = self.start_episode(state)
            # elif (
            #     wm._get_last_action_time() == wm._get_current_cycle() - 1
            #     and wm._last_action > 0
            # ):
            #     ## if we were in the middle of a pass last cycle
            #     action = wm._last_action  ## then we follow through with it

            # ## Call step() on all but first SMDP step
            # else:
            #     action = self.step(wm._reward(), state)
            #     wm._set_last_action(action)
        else:
            ## if we don't have enough info to calculate state vars
            action = 1  ## hold ball
            # LogDraw.logText( "state", VecPosition( 35, 25 ),"clueless", 1, COLOR_RED )
            return _interpret_keeper_action(action)

    ## If fastest, intercept the ball.
    # fastest_teammate = wm.intercept_table().fastest_teammate()
    # if fastest_teammate is not None:
    #     if DEBUG:
    #         log.os_log().debug("I am fastest to ball; can get there in cycles")
    #         ## If we are the fastest to the ball, intercept it.
    #     return BasicTackle(0.8, 80).execute(agent)

    # log.os_log().debug("I am not fastest to ball")

    # return _keeper_support(wm, fastest_teammate)

    # return BhvKick().execute(agent)
    # if BhvMove().execute(agent):
    #     return True
    # log.os_log().warn("NO ACTION, ScanFIELD")
    # return ScanField().execute(agent)


def taker_decision(agent: "PlayerAgent"):
    wm: "WorldModel" = agent.world()

    def _get_in_set_in_cone(wm, radius, pos_from, pos_to):
        """Returns the number of players in the given set in the cone from posFrom to posTo with the given radius."""
        count = 0
        for p in wm._opponents:
            if p.pos_valid():
                if (
                    pos_from.dist(pos_to) - p.pos().dist(pos_to) < radius
                ):  ## TODO: check this
                    count += 1
        return count

    def _get_marking_position(wm, pos, dDist):
        """Returns the marking position."""

        ball_pos = wm.ball().pos()
        ball_angle = (ball_pos - pos._pos).dir()
        return pos._pos + Vector2D.polar2vector(dDist, ball_angle)

    def mark_opponent(wm, p, dDist, obj):  # TODO: check this.
        """Mark the given opponent."""

        # wm: "WorldModel" = agent.world()
        pos_mark = _get_marking_position(wm, p, dDist)
        pos_agent = p.pos()
        pos_ball = wm.ball().pos()

        if obj == "ball":
            if pos_mark.dist(pos_agent) < 1.5:
                return TurnToBall().execute(agent)
            else:
                return GoToPoint(pos_mark, 0.2, 100).execute(agent)
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
            # Log.log(513, "mark: turn body to ang %f", angOpp);
            target = pos_agent + Vector2D(1.0, ang_opp, POLAR)
            return NeckBodyToPoint(target).execute(agent)
            # return self.turn_body_to_point(pos_agent + Vector2D(1.0, ang_opp, POLAR))

        print("mark: move to marking position", pos_mark)
        # Log.log(513, "move to marking position");
        return GoToPoint(pos_mark, 0.2, 100).execute(agent)
        # return self.move_to_pos(pos_mark, 25, 3.0, False)

    def mark_most_open_opponent(wm, keepers):
        """Mark the most open opponent."""

        if len(keepers) == 0:
            return
        else:
            pos_from = keepers[0].pos()

            min_player = None
            min = 1000
            for p in wm._opponents:
                if p.pos_valid():
                    point = p.pos()
                    if point.abs_y() == 37:
                        continue
                    num = _get_in_set_in_cone(wm, 0.3, pos_from, point)
                    if num < min:
                        min = num
                        min_player = p

            return mark_opponent(wm, min_player, 4.0, "ball")

    # If we don't know where the ball is, search for it. PS->getBallConfThr() = 0.90
    if wm._get_confidence("ball") < 0.90:
        log.os_log().warn("NO ACTION, ScanFIELD")
        return ScanField().execute(agent)

    # Maintain possession if you have the ball. not totally sure will debug later
    if wm.self().is_kickable() and (len(wm.self()._teammates_from_ball) == 0):
        return HoldBall().execute(agent)

    # If not first or second closest, then mark open opponent.
    closest_taker_from_ball = wm._teammates_from_ball
    if agent not in closest_taker_from_ball[0:2]:
        # find the closest keeper to the ball
        closest_keeper_from_ball = wm._opponents_from_ball
        # print("closest keeper from ball", closest_keeper_from_ball)
        # mark the keeper with the ball.
        mark_most_open_opponent(wm, closest_keeper_from_ball)  ## should be a behavior
        return NeckTurnToBall().execute(agent)

    ## If teammate has it, don't mess with it.
    d = closest_taker_from_ball.dist_to_ball()

    # if (SoccerTypes::isTeammate( closest ) && closest != WM->getAgentObjectType() & dDist < SS->getMaximalKickDist()):
    if d < 0.3:
        NeckTurnToBall().execute(agent)
        # TurnToAngle().execute(self)
        return NeckBodyToBall().execute(agent)
    else:
        # Otherwise try to intercept the ball
        # ACT->putCommandInQueue( soc = intercept( false ) ) ## TODO check if this is the right intercept
        # ACT->putCommandInQueue( turnNeckToObject( OBJECT_BALL, soc ) );
        NeckTurnToBall().execute(agent)
        if BhvMove().execute(agent):
            return True

    # if wm.game_mode().type() != GameModeType.PlayOn:
    if BhvMove().execute(agent):
        return True
    log.os_log().warn("NO ACTION, ScanFIELD")
    return ScanField().execute(agent)
