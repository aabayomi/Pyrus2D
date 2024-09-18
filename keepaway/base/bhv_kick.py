from keepaway.lib.action.hold_ball import HoldBall
from keepaway.lib.action.neck_scan_players import NeckScanPlayers
from keepaway.lib.action.smart_kick import SmartKick
from typing import List
from keepaway.base.generator_action import KickAction, ShootAction, KickActionType
from keepaway.base.generator_dribble import BhvDribbleGen
from keepaway.base.generator_pass import BhvPassGen
from keepaway.base.generator_shoot import BhvShhotGen
from keepaway.base.generator_clear import BhvClearGen
from keepaway.lib.rcsc.server_param import ServerParam
from pyrusgeom.line_2d import Line2D
from pyrusgeom.vector_2d import Vector2D
from keepaway.base.tools import Tools

from typing import TYPE_CHECKING

from keepaway.lib.debug.debug import log
from keepaway.lib.messenger.pass_messenger import PassMessenger

if TYPE_CHECKING:
    from keepaway.lib.player.world_model import WorldModel
    from keepaway.lib.player.player_agent import PlayerAgent


class BhvKick:
    def __init__(self):
        pass

    def execute(self, agent: "PlayerAgent"):
        wm: "WorldModel" = agent.world()
        shoot_candidate: ShootAction = BhvShhotGen().generator(wm)
        if shoot_candidate:
            log.debug_client().set_target(shoot_candidate.target_point)
            log.debug_client().add_message(
                "shoot"
                + "to "
                + shoot_candidate.target_point.__str__()
                + " "
                + str(shoot_candidate.first_ball_speed)
            )
            SmartKick(
                shoot_candidate.target_point,
                shoot_candidate.first_ball_speed,
                shoot_candidate.first_ball_speed - 1,
                3,
            ).execute(agent)
            agent.set_neck_action(NeckScanPlayers())
            return True
        else:
            action_candidates: List[KickAction] = []
            action_candidates += BhvPassGen().generator(wm)
            # action_candidates += BhvDribbleGen().generator(wm) # TODO

            if len(action_candidates) == 0:
                return self.no_candidate_action(agent)

            best_action: KickAction = max(action_candidates)  #

            target = best_action.target_ball_pos
            log.debug_client().set_target(target)
            log.debug_client().add_message(
                best_action.type.value
                + "to "
                + best_action.target_ball_pos.__str__()
                + " "
                + str(best_action.start_ball_speed)
            )
            SmartKick(
                target,
                best_action.start_ball_speed,
                best_action.start_ball_speed - 1,
                3,
            ).execute(agent)

            if best_action.type is KickActionType.Pass:
                agent.add_say_message(
                    PassMessenger(
                        best_action.target_unum,
                        best_action.target_ball_pos,
                        agent.effector().queued_next_ball_pos(),
                        agent.effector().queued_next_ball_vel(),
                    )
                )

            agent.set_neck_action(NeckScanPlayers())
            return True

    def no_candidate_action(self, agent: "PlayerAgent"):
        wm = agent.world()
        opp_min = wm.intercept_table().opponent_reach_cycle()
        if opp_min <= 3:
            action_candidates = BhvClearGen().generator(wm)
            if len(action_candidates) > 0:
                best_action: KickAction = max(action_candidates)
                target = best_action.target_ball_pos
                log.debug_client().set_target(target)
                log.debug_client().add_message(
                    best_action.type.value
                    + "to "
                    + best_action.target_ball_pos.__str__()
                    + " "
                    + str(best_action.start_ball_speed)
                )
                SmartKick(
                    target,
                    best_action.start_ball_speed,
                    best_action.start_ball_speed - 2.0,
                    2,
                ).execute(agent)

        agent.set_neck_action(NeckScanPlayers())
        return HoldBall().execute(agent)

    # def kick_to(self,agent: "PlayerAgent",tar_pos,speed):
    #     SP = ServerParam.i()
    #     wm = agent.world()

    #     ball_pos = wm.ball().pos()
    #     ball_vel = wm.ball().vel()
    #     travel_dist = tar_pos - ball_pos
    #     curr_pos = wm.self().pos()

    #     # set polar
    #     cal_travel_speed = Tools.get_kick_travel(travel_dist.r(), speed)
    #     vel_des = Vector2D.polar2vector(cal_travel_speed, travel_dist.dir())

    #     # vel_des = (tar_pos - curr_pos).normalized() * speed

    #     if (wm.predict_pos().dist(ball_pos + vel_des) < SP.ball_size() + SP.player_size() ):
    #         line_segment = Line2D(ball_pos,ball_pos + travel_dist)
    #         body_proj = line_segment.projection(curr_pos)
    #         dist =  ball_pos.dist(body_proj)
    #         if (travel_dist.r() < dist):
    #             dist -= SP.ball_size() + SP.player_size()
    #         else:
    #             dist += SP.ball_size() + SP.player_size()
    #             # Log.log(102, "kick results in collision, change velDes from (%f,%f)",
    #             #         velDes.getX(), velDes.getY());
    #             travel_dist.set_polar(dist, travel_dist.th())

    #     dDistOpp = std::numeric_limits<double>::max();
    #     objOpp = WM->getClosestInSetTo(OBJECT_SET_OPPONENTS,
    #                                      OBJECT_BALL, &dDistOpp);

    #     # // can never reach point
    #     if (travel_dist.r() > SP.ball_speed_max()):
    #         pow = SP.getMaxPower()
    #         speed = wm.self().kick_rate() * pow
    #         tmp = ball_vel.rotate(-travel_dist.th()).get_y()
    #         ang = travel_dist.th() - AngleDeg.asin_deg(tmp / speed)
    #         speedpred = (ball_vel + Vector2D.polar2vector(speed, ang)).r()
    #         # but ball acceleration in right direction is very high
    #         # player kick prop 0.85 - handcoded
    #         if (speedpred > 0.85 * SP.ball_accel_max()):
    #             # Log.log(102, "pos (%f,%f) too far, but can acc ball good to %f k=%f,%f",
    #             #         velDes.getX(), velDes.getY(), dSpeedPred, dSpeed, tmp);
    #             # // shoot nevertheless

    #             return accelerateBallToVelocity(vel_des)
    #         elif (wm.kick_power_rate() > 0.85 * SP.kick_power_rate()):
    #             # {
    #             # Log.log(102, "point too far, freeze ball"); // ball well-positioned
    #             # // freeze ball
    #             return freezeBall();
    #         else:
    #             # Log.log(102, "point too far, reposition ball (k_r = %f)",
    #             #         WM->getActualKickPowerRate() / (SS->getKickPowerRate()));
    #             # // else position ball better

    #             return kickBallCloseToBody(0);
    #     # // can reach point
    #     else :
    #         Vector2D accBallDes = vel_des - vel_ball
    #         dPower = wm.get_kick_power_speed(accBallDes.getMagnitude())

    #         # // with current ball speed
    #         if (dPower <= 1.05 * SS->getMaxPower() or (dDistOpp < 2.0 && dPower <= 1.30 *
    #                                             SP.getMaxPower())):                               // 1.05 since cannot get ball fully perfect
    #             # Log.log(102, "point good and can reach point %f", dPower);
    #             # // perform shooting action
    #             return accelerateBallToVelocity(velDes);
    #         else:
    #             # Log.log(102, "point good, but reposition ball since need %f", dPower);
    #             SoccerCommand soc = kickBallCloseToBody(0);
    #             VecPosition posPredBall;

    #             WM->predictBallInfoAfterCommand(soc, &posPredBall);
    #             dDistOpp = posPredBall.getDistanceTo(WM->getGlobalPosition(objOpp));
    #             # // position ball better
    #         return soc;
