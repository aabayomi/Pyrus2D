from keepaway.base import goalie_decision
from keepaway.base.strategy_formation import StrategyFormation
from keepaway.base.set_play.bhv_set_play import Bhv_SetPlay
from keepaway.base.bhv_kick import BhvKick
from keepaway.base.bhv_move import BhvMove
from keepaway.lib.action.neck_scan_field import NeckScanField
from keepaway.lib.action.neck_scan_players import NeckScanPlayers
from keepaway.lib.action.neck_turn_to_ball import NeckTurnToBall
from keepaway.lib.action.scan_field import ScanField
from keepaway.lib.debug.debug import log
from keepaway.lib.action.hold_ball import HoldBall

from keepaway.utils.keepaway_actions import (
    SmartKick,
    GoToPoint,
    NeckTurnToBallOrScan,
    NeckBodyToPoint,
)

from keepaway.lib.action.turn_to_ball import TurnToBall
from keepaway.lib.action.neck_body_to_ball import NeckBodyToBall
from keepaway.lib.rcsc.server_param import ServerParam

from keepaway.base.generator_pass import BhvPassGen
from keepaway.lib.action.intercept import Intercept


from pyrusgeom.soccer_math import *
from pyrusgeom.rect_2d import Rect2D
from pyrusgeom.vector_2d import Vector2D
from pyrusgeom.line_2d import Line2D
from pyrusgeom.segment_2d import Segment2D
from pyrusgeom.geom_2d import *

from keepaway.base.tools import Tools
from typing import TYPE_CHECKING

import math as Math

if TYPE_CHECKING:
    from keepaway.lib.player.world_model import WorldModel
    from keepaway.lib.player.player_agent import PlayerAgent

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
):
    wm: "WorldModel" = agent.world()

    # void GetOpen::run() {
    #   int status = WM->isTmControllBall();
    #   while (running() && status == WM->isTmControllBall()) {
    #     SoccerCommand soc;
    #     ObjectT fastest = WM->getFastestInSetTo(OBJECT_SET_TEAMMATES, OBJECT_BALL);
    #     int iCycles = WM->predictNrCyclesToObject(fastest, OBJECT_BALL);
    #     VecPosition posPassFrom = WM->predictPosAfterNrCycles(OBJECT_BALL, iCycles);
    #     posPassFrom = refineTarget(posPassFrom, WM->getBallPos());
    #     ACT->putCommandInQueue(soc = player->getOpenForPassFromInRectangle(WM->getKeepawayRect(), posPassFrom));
    #     ACT->putCommandInQueue(player->turnNeckToObject(OBJECT_BALL, soc));
    #     Log.log(101, "GetOpen::run action");
    #     Action(this)();
    #     if (WM->isBallKickable()) break;
    #   }

    #     bool WorldModel::isTmControllBall() {
    #   ObjectT K0 = getClosestInSetTo(OBJECT_SET_TEAMMATES, OBJECT_BALL);
    #   VecPosition B = getBallPos();
    #   double WK0_dist_to_B = getGlobalPosition(K0).getDistanceTo(B);
    #   bool tmControllBall = WK0_dist_to_B < getMaximalKickDist(K0);
    #   return tmControllBall || isBallKickable();
    # }

    def get_marking_position(wm, pos, dDist):
        """Returns the marking position."""
        ball_pos = wm.ball().pos()
        ball_angle = (ball_pos - pos._pos).dir()
        return pos._pos + Vector2D.polar2vector(dDist, ball_angle)

    def mark_opponent(wm, p, dDist, obj):  # TODO: check this.
        """Mark the given opponent."""

        pos_mark = get_marking_position(wm, p, dDist)
        pos_agent = p.pos()
        pos_ball = wm.ball().pos()
        if obj == "ball":
            if pos_mark.dist(pos_agent) < 1.5:
                TurnToBall().execute(agent)
            else:
                GoToPoint(pos_mark, 0.2, 100).execute(agent)
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

                return NeckBodyToPoint(target).execute(agent)

        return GoToPoint(pos_mark, 0.2, 100).execute(agent)

    def mark_most_open_opponent(wm):
        """Mark the most open opponent."""
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
        """
        check on pass .

        """
        # print(" checking on pass ")
        # print("pass ball changed .. ", len(wm.messenger_memory().balls()))
        # print("pass time ", wm.messenger_memory().pass_time())
        # print("world model time ", wm.time())
        # print("length of pass ", wm.messenger_memory().pass_())
        # if len(wm.messenger_memory().pass_()) > 0:
        #     print("pass receiver ", wm.messenger_memory().pass_()[0]._receiver)
        # print("memory players ", wm.messenger_memory().players())

        if (
            wm.messenger_memory().pass_time() != wm.time()
            or len(wm.messenger_memory().pass_()) == 0
            or wm.messenger_memory().pass_()[0]._receiver != wm.self().unum()
        ):
            # print("False")
            return False

        self_min = wm.intercept_table().self_reach_cycle()
        intercept_pos = wm.ball().inertia_point(self_min)
        heard_pos = wm.messenger_memory().pass_()[0]._pos

        # print("heard pos ", heard_pos)

        log.sw_log().team().add_text(
            f"(sample player do heard pass) heard_pos={heard_pos}, intercept_pos={intercept_pos}"
        )

        if (
            not wm.kickable_teammate()
            and wm.ball().pos_count() <= 1
            and wm.ball().vel_count() <= 1
            and self_min < 20
        ):
            print(
                "sample player do heard pass) intercepting!", "i am ", wm.self().unum()
            )

            log.sw_log().team().add_text(
                f"(sample player do heard pass) intercepting!, self_min={self_min}"
            )
            log.debug_client().add_message("Comm:Receive:Intercept")
            Intercept().execute(agent)
            agent.set_neck_action(NeckTurnToBall())

        else:
            print(
                "(sample player do heard pass) go to point!,  cycle ",
                self_min,
                " i am ",
                wm.self().unum(),
            )

            log.sw_log().team().add_text(
                f"(sample player do heard pass) go to point!, cycle={self_min}"
            )
            log.debug_client().set_target(heard_pos)
            log.debug_client().add_message("Comm:Receive:GoTo")

            GoToPoint(heard_pos, 1.0, ServerParam.i().max_dash_power()).execute(agent)
            agent.set_neck_action(NeckTurnToBall())

    def get_in_set_in_cone(wm, radius, pos_from, pos_to):
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

    def congestion(wm, point, consider_me):
        """Returns the congestion at the given position."""
        congest = 0
        for p in wm._teammates:
            if p.pos_valid() and p.pos() != point:
                congest += 1 / p.pos().dist(point)

        for p in wm._opponents:
            if p.pos_valid():
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

        start_x = rect.bottom_left().x() + x_buffer * length
        start_y = rect.top_left().y() + y_buffer * width

        x = start_x
        y = start_y

        # print("X and Y ", x, y)

        best_congestion = 1000
        point = Vector2D(x, y)
        tmp = None

        for i in range(x_granularity):
            for j in range(y_granularity):
                point = Vector2D(x, y)
                # print("point", point)
                tmp = congestion(wm, point, True)
                if (
                    tmp < best_congestion
                    and get_in_set_in_cone(wm, 0.3, pos_from, point) == 0
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

    def get_open(wm, best_point):
        if wm.self().pos().dist(best_point) < 1.5:
            NeckBodyToPoint(best_point).execute(agent)
        else:
            GoToPoint(best_point, 0.2, 100).execute(agent)

    def keeper_support(wm, fastest, agent):
        """Keeper support."""
        from keepaway.lib.messenger.one_player_messenger import OnePlayerMessenger

        sp = ServerParam.i()
        first_ball_pos = wm.ball().pos()
        min_reach_cycle = Tools.estimate_min_reach_cycle(
            fastest._pos,
            1.0,
            first_ball_pos,
            first_ball_pos.th(),
        )
        # print("min_reach_cycle ", min_reach_cycle)
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

        rect = wm.keepaway_rect()
        best_point = least_congested_point_for_pass_in_rectangle(rect, pos_pass_from)

        if do_heard_pass_receive(wm, agent) == False:
            # print("i am ", wm.self()._unum,"no pass heard")
            # print("i am ", wm.self()._unum, "going to ", best_point)
            GoToPoint(best_point, 0.2, 100).execute(agent)
            return
        else:
            print("pass was heard ")
            # i am waiting for the pass.
            agent.set_neck_action(NeckScanField())
            return

        # if wm.self().pos().dist(best_point) < 1.5:
        #     print("NeckScanField")
        #     return NeckBodyToPoint(wm.ball().pos()).execute(agent)
        #     # agent.set_neck_action(NeckScanPlayers())
        # else:
        #     print("i am ", wm.self()._unum, "going to ", best_point)

        #     # agent.add_say_message(OnePlayerMessenger(wm.self().unum(),
        #     #                                     best_point))
        #     GoToPoint(best_point, 0.2, 100).execute(agent)
        #     return

        # # # # ObjectT lookObject = self._choose_look_object( 0.97 )

    def search_ball(wm, agent):
        return ScanField().execute(agent)

    def hold(wm, agent):
        """ """
        from keepaway.lib.action.neck_scan_players import NeckScanPlayers

        agent.set_neck_action(NeckScanPlayers())
        HoldBall().execute(agent)
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
            search_ball(wm, agent)
            return
        # move(wm, agent)
        return

    def test_kick(wm, agent, t):
        """Test implementation for kick
        target
        speed
        speed threshold
        max step
        similar to the goalie kick
        """

        from keepaway.lib.action.smart_kick import SmartKick

        action_candidates = BhvPassGen().generator(wm)

        print("action candidates ", action_candidates)

        if len(action_candidates) == 0:
            print("Holding the ball")
            agent.set_neck_action(NeckScanPlayers())
            return HoldBall().execute(agent)

        best_action: KickAction = max(action_candidates)
        target = best_action.target_ball_pos
        print("Target : ", target)
        log.debug_client().set_target(target)
        log.debug_client().add_message(
            best_action.type.value
            + "to "
            + best_action.target_ball_pos.__str__()
            + " "
            + str(best_action.start_ball_speed)
        )

        # print(" best action speed ", best_action.start_ball_speed)

        # SmartKick(
        #     target, best_action.start_ball_speed, best_action.start_ball_speed - 1, 3
        # ).execute(agent)
        agent.set_neck_action(NeckScanPlayers())

        return

    def interpret_keeper_action(wm, agent, action):
        print("interpret actions , ", action)

        if action == 0:
            print("Holding Ball ")
            hold(wm, agent)
        else:
            print("Passing ")
            k = wm.teammates_from_ball()
            if len(k) > 0:
                for tm in k:
                    if tm.unum() == action:
                        temp_pos = tm.pos()
                        # print("passing to player ", tm.unum(), "at pos ", temp_pos)
                        print(
                            "i am ",
                            wm.self().unum(),
                            "at pos ",
                            wm.self().pos(),
                            "passing to player ",
                            tm.unum(),
                            "at pos ",
                            temp_pos,
                        )
                        # ball_to_player.rotate(-wm.ball().vel().th())
                        agent.do_kick_to(tm, 1.5)
                        # agent.do_kick_2(tm, 1.5)
                        ## test pass logic
                        # agent.test_pass(tm, 1.5)
                        # test_kick(wm,agent,temp_pos)
                        agent.set_neck_action(NeckScanPlayers())
                        # agent.do_kick(temp_pos, 0.8)
            # k = wm.messenger_memory().players()
            # if len(k) > 0:
            #     for tm in k:
            #         print("player num ", tm.unum_)
            #         if tm.unum_ == action:
            #             temp_pos = tm.pos_
            #             print("i am ",wm.self().unum(), "passing to player ", tm.unum_, "at pos ", temp_pos)
            #             agent.do_kick_to(tm, 2.0)
            #             agent.set_neck_action(NeckScanPlayers())

            else:
                print("no teammates")
                pass
        return

    def keeper_with_ball_2(
        wm: "WorldModel", agent: "PlayerAgent", actions, last_action_time
    ):
        # print("keeper with ball")
        # action = actions[wm.self().unum()]
        action = actions[wm.self().unum() - 1]
        # print(
        #     "agent ",
        #     wm.self().unum(),
        #     " action ",
        #     actions,
        #     "my act ",
        #     actions[wm.self().unum() - 1],
        # )
        interpret_keeper_action(wm, agent, action)

    if wm.our_team_name() == "keepers":
        barrier.wait()
        if wm.get_confidence("ball") < 0.90:
            search_ball(wm, agent)

        # teammates_from_ball = wm.teammates_from_ball()
        ball_pos = wm.ball().pos()
        # GoToPoint(ball_pos, 0.2, 100).execute(agent)

        closest_keeper_from_ball = wm.all_teammates_from_ball()
        if len(closest_keeper_from_ball) > 0:
            if wm.self().unum() == closest_keeper_from_ball[0].unum():
                GoToPoint(ball_pos, 0.2, 100).execute(agent)

        if wm.self().pos().dist(ball_pos) < 5.0:
            obs[wm.self().unum()] = wm._retrieve_observation()
            if wm.self().is_kickable():
                wm._available_actions[wm.self().unum()] = 2
                # count_list[wm.self().unum()] = 2
                with count_list.get_lock():
                    # print("action received  ", list(count_list))
                    pass
                # print("ball is kickable, ", wm.self().unum())
                keeper_with_ball_2(wm, agent, count_list, last_action_time)
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
                keeper_support(wm, fastest, agent)

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
            search_ball(wm, agent)

        ball_pos = wm.ball().pos()
        GoToPoint(ball_pos, 0.2, 100).execute(agent)

        # Maintain possession if you have the ball.
        if wm.self().is_kickable() and (len(wm.teammates_from_ball()) == 0):
            return HoldBall().execute(agent)

        closest_taker_from_ball = wm.teammates_from_ball()
        if wm.self() not in closest_taker_from_ball:
            mark_most_open_opponent(wm)
            return NeckTurnToBall().execute(agent)

        d = closest_taker_from_ball.dist_to_ball()
        if d < 0.3:
            NeckTurnToBall().execute(agent)
            NeckBodyToBall().execute(agent)
            return
        return Intercept().execute(agent)
