from typing import Union
import logging
import time

from keepaway.lib.action.kick_table import KickTable

# from keepaway.base.decision import get_decision
from keepaway.lib.debug.debug import log
from keepaway.lib.debug.level import Level
from keepaway.lib.debug.color import Color
from pyrusgeom.angle_deg import AngleDeg
from pyrusgeom.line_2d import Line2D
from keepaway.lib.player.action_effector import ActionEffector
from keepaway.lib.player.sensor.body_sensor import SenseBodyParser
from keepaway.lib.player.sensor.see_state import SeeState
from keepaway.lib.player.sensor.visual_sensor import SeeParser
from keepaway.lib.player.soccer_action import ViewAction, NeckAction, FocusPointAction
# from keepaway.lib.player.soccer_agent import SoccerAgent
from keepaway.utils.soccer_agent import SoccerAgent
from keepaway.lib.player.world_model import WorldModel
from keepaway.base.tools import Tools

# from keepaway.lib.coach.gloabl_world_model import GlobalWorldModel
from keepaway.lib.network.udp_socket import IPAddress
from pyrusgeom.soccer_math import min_max

from keepaway.lib.player_command.player_command import (
    PlayerInitCommand,
    PlayerByeCommand,
    PlayerCheckBallCommand,
)

from keepaway.lib.player_command.player_command_support import (
    PlayerDoneCommand
)

from keepaway.lib.player_command.player_command_body import (
    PlayerKickCommand
)


from keepaway.lib.player_command.player_command_sender import PlayerSendCommands
from keepaway.lib.rcsc.game_mode import GameMode
from keepaway.lib.rcsc.game_time import GameTime
from keepaway.lib.rcsc.server_param import ServerParam
from keepaway.lib.rcsc.types import UNUM_UNKNOWN, GameModeType, SideID, ViewWidth
from keepaway.lib.messenger.messenger import Messenger
# from keepaway.config import team_config
from keepaway.config import team_config
from keepaway.lib.debug.timer import ProfileTimer as pt
from keepaway.lib.parser.parser_message_fullstate_world import FullStateWorldMessageParser


DEBUG = True


def get_time_msec():
    return int(time.time() * 1000)


from pyrusgeom.angle_deg import AngleDeg
from pyrusgeom.vector_2d import Vector2D


class PlayerAgent(SoccerAgent):
    def __init__(
        self,
        shared_values,
        barrier,
        lock,
        event,
        world,
        terminated,
        reward,
        team_name=team_config.TEAM_NAME,
    ):
        self._goalie: bool = False
        super(PlayerAgent, self).__init__()
        self._think_received = False
        self._current_time: GameTime = GameTime()
        self._last_decision_time: GameTime = GameTime()

        self._sense_body_parser: SenseBodyParser = SenseBodyParser()
        self._see_parser: SeeParser = SeeParser()
        self._full_state_parser: FullStateWorldMessageParser = (
            FullStateWorldMessageParser()
        )

        self._see_state: SeeState = SeeState()

        # self._team_name = team_config.TEAM_NAME
        self._team_name = team_name
        # print("team name is ", self._team_name)

        self._game_mode: GameMode = GameMode()
        self._server_cycle_stopped: bool = True

        self._sense_receive_time_stamp: Union[int, None] = None

        self._neck_action: Union[NeckAction, None] = None
        self._view_action: Union[ViewAction, None] = None
        self._focus_point_action: Union[FocusPointAction, None] = None

        # self._real_world = WorldModel("real")
        self._real_world = None
        # self._full_world = WorldModel("full")
        self._full_world = world
        self._last_body_command = []
        self._is_synch_mode = True
        self._effector = ActionEffector(self)
        self._communication = None

        self._shared_values = shared_values
        self._barrier = barrier
        self._lock = lock
        self._event = event

        self._terminated = terminated
        self._terminal_time = GameTime(0, 0)
        self._reward = reward

    def send_init_command(self):
        # TODO check reconnection

        # com = PlayerInitCommand(
        #     team_config.TEAM_NAME, team_config.PLAYER_VERSION, self._goalie
        # )
        com = PlayerInitCommand(self._team_name, 18, self._goalie)
        # TODO set team name from keepaway.config

        # self._full_world._team_name = team_config.TEAM_NAME
        self._full_world._team_name = self._team_name

        # print(com.str())
        if self._client.send_message(com.str()) <= 0:
            log.os_log().error("ERROR failed to connect to server")
            self._client.set_server_alive(False)
            return False
        return True

    # def do_teamname(self):
    #     command = CoachTeamnameCommand()
    #     self._last_body_command.append(command)
    #     return True

    def check_ball(self):
        command = PlayerCheckBallCommand()
        # print(command.str())
        self._client.send_message(command.str())

    def send_bye_command(self):
        if self._client.is_server_alive() is True:  # TODO FALSE?
            com = PlayerByeCommand()
            self._client.send_message(com.str())
            self._client.set_server_alive(False)

    def parse_sense_body_message(self, message: str):
        self._sense_receive_time_stamp = get_time_msec()
        self.update_current_time(PlayerAgent.parse_cycle_info(message), True)
        self._sense_body_parser.parse(message, self._current_time)
        self._see_state.update_by_sense_body(
            self._current_time, self._sense_body_parser.view_width()
        )
        if DEBUG:
            log.os_log().debug(
                f"##################{self._current_time}#################"
            )
            log.sw_log().sensor().add_text("===Received Sense Message===\n" + message)
            log.os_log().debug("===Received Sense Message===\n" + message)
            log.sw_log().sensor().add_text(str(self._sense_body_parser))
            log.os_log().debug(str(self._sense_body_parser))

    def parse_see_message(self, message: str):
        self.update_current_time(PlayerAgent.parse_cycle_info(message), False)
        # log.debug_client().add_message(f'rec see in {self.world().time().cycle()}\n')
        self._see_parser.parse(message, self._team_name, self._current_time)
        self._see_state.update_by_see(
            self._current_time, self.real_world().self().view_width()
        )

        if DEBUG:
            log.sw_log().sensor().add_text(
                "===Received See Message Sensor===\n" + message
            )
            log.os_log().debug(f'{"=" * 30}See Message Sensor{"=" * 30}\n' + message)
            log.sw_log().sensor().add_text(
                "===Received See Message Visual Sensor===\n" + str(self._see_parser)
            )
            log.os_log().debug(
                f'{"=" * 30}Visual Sensor{"=" * 30}\n' + str(self._see_parser)
            )

    def parse_full_state_message(self, message: str):
        self.update_current_time(PlayerAgent.parse_cycle_info(message), False)
        self._full_state_parser.parse(message)
        log.os_log().debug("===Received Full State Message Sensor===\n" + message)
        log.os_log().debug(
            f'{"=" * 30}Full State Message Sensor{"=" * 30}\n'
            + str(self._full_state_parser.dic())
        )

    def hear_parser(self, message: str):
        self.update_current_time(PlayerAgent.parse_cycle_info(message), False)
        _, cycle, sender = tuple(message.split(" ")[:3])
        cycle = int(cycle)

        if sender[0].isnumeric() or sender[0] == "-":  # PLAYER MESSAGE.
            self.hear_player_parser(message)
            pass
        elif sender == "referee":
            # print("referee message", message)

            # with self._terminated.get_lock():
            #     self._terminated.value = True
            # self.full_world()._terminated = True
            self.hear_referee_parser(message)
            # pass
        elif sender == "coach":
            # print("coach message", message)

    def init_dlog(self, message):
        log.setup(self.world().team_name_l(), "coach", self._current_time)

    def hear_player_parser(self, message: str):
        log.debug_client().add_message(f"rcv msg:#{message}#")
        log.sw_log().communication().add_text(f"rcv msg:#{message}#")
        if message.find('"') == -1:
            log.sw_log().communication().add_text("parser error A")
            return
        data = message.strip("()").split(" ")
        if len(data) < 6:
            # log.os_log().error(f"(hear player parser) message format is not matched! msg={message}")
            log.sw_log().communication().add_text("parser error B")
            return
        if data[3] == "opp":
            log.sw_log().communication().add_text("parser error C")
            return
        player_message = message.split('"')[1]
        if not data[4].isdigit():
            log.sw_log().communication().add_text("parser error D")
            return
        sender = int(data[4])
        log.sw_log().communication().add_text(f"sender is {sender}")
        Messenger.decode_all(
            self.real_world()._messenger_memory,
            player_message,
            sender,
            self._current_time,
        )

    def hear_referee_parser(self, message: str):
        mode = message.split(" ")[-1].strip(")")
        keepaway_mode = message.split(" ")[-2:]
        if keepaway_mode[-1].strip(")\x00") == "play_on":
            # print("mode is ", keepaway_mode[-1].strip(")"))
            pass
        else:
            ## Set new episode
            # self._full_world().set_new_episode()
            # print("end of episode")
            with self._terminated.get_lock():
                self.full_world()._terminated = True
                self._terminated.value = True
                self._reward.value = (
                    self._current_time.cycle() - self._terminal_time.cycle()
                )

        time.sleep(1)
        self._barrier.wait()

        # self._terminated.value = True

        with self._terminated.get_lock():
            self.full_world().start_new_episode()
            self._terminated.value = False
            self.full_world()._terminated = False
            self._terminal_time = self._current_time.copy()
            self._reward.value = 0

        if not self._game_mode.update(mode, self._current_time):
            return

        # TODO: Fix this. game mode changes
        # TODO CARDS AND OTHER STUFF

        self.update_server_status()

        if self._game_mode.type() is GameModeType.TimeOver:
            self.send_bye_command()
            return
        self.real_world().update_game_mode(self._game_mode, self._current_time)
        if self.full_world_exists():
            self.full_world().update_game_mode(self._game_mode, self._current_time)

    def update_server_status(self):
        if self._server_cycle_stopped:
            self._server_cycle_stopped = False

        if self._game_mode.is_server_cycle_stopped_mode():
            self._server_cycle_stopped = True

    @staticmethod
    def parse_cycle_info(msg: str) -> int:
        cycle = int(msg.split(" ")[1].removesuffix(")\x00"))
        return cycle

    def update_current_time(self, new_time: int, by_sense_body: bool):
        old_time: GameTime = self._current_time.copy()
        if new_time < old_time.cycle():
            log.os_log().warn(
                f"player({self.world().self_unum()}):" f"received an old message!!"
            )
            return

        if self._server_cycle_stopped:
            if new_time == self._current_time.cycle():
                if by_sense_body:
                    self._current_time.assign(
                        self._current_time.cycle(),
                        self._current_time.stopped_cycle() + 1,
                    )
                    log.sw_log().any().add_text(
                        f"Cycle: {self._current_time.cycle()}-"
                        f"{self._current_time.stopped_cycle()} " + "-" * 20
                    )
                    if (
                        self._last_decision_time != old_time
                        and old_time.stopped_cycle() != 0
                    ):
                        log.sw_log().system().add_text(
                            f"(update current time) missed last action(1)"
                        )
            else:
                self._current_time.assign(new_time, 0)
                if new_time - 1 != old_time.cycle():
                    log.os_log().warn(
                        f"player({self.world().self_unum()}):"
                        f"last server time was wrong maybe"
                    )
        else:
            self._current_time.assign(new_time, 0)
            if old_time.cycle() != new_time:
                log.sw_log().any().add_text(f"Cycle {new_time}-0 " + "-" * 20)

                if new_time - 1 != old_time.cycle():
                    log.os_log().warn(
                        f"player({self.world().self_unum()}):"
                        f"last server time was wrong maybe"
                    )

                if (
                    self._last_decision_time.stopped_cycle() == 0
                    and self._last_decision_time.cycle() != new_time - 1
                ):
                    log.sw_log().system().add_text(
                        f"(update current time) missed last action(2)"
                    )

    def think_received(self):
        return self._think_received

    # def do_change_mode(self, mode: GameModeType):
    #     self._last_body_command.append(PlayerChangeModeCommand(mode))

    def is_decision_time(self, timeout_count: int, waited_msec):
        msec_from_sense = -1
        if self._sense_receive_time_stamp:
            msec_from_sense = get_time_msec() - self._sense_receive_time_stamp
        SP = ServerParam.i()

        if SP.synch_mode():
            return False

        if msec_from_sense < 0:
            return False

        if self._last_decision_time == self._current_time:
            return False

        if self.world().self().unum() == UNUM_UNKNOWN:
            return False

        if self.world().see_time() == self._current_time:
            return True

        wait_thr: int = team_config.WAIT_TIME_THR_SYNCH_VIEW

        if (
            self._last_decision_time == self.world().sense_body_time()
            and timeout_count <= 2
        ):
            return False

        if SP.synch_see_offset() > wait_thr and msec_from_sense >= 0:
            return True

        if self._see_state.cycles_till_next_see() > 0:
            return True

        if msec_from_sense >= wait_thr * SP.slow_down_factor():
            return True
        return False

    def do_neck_action(self):
        log.debug_client().add_message("NECK/")
        if self._neck_action:
            self._neck_action.execute(self)
            self._neck_action = None

    def do_view_action(self):
        if self._view_action:
            self._view_action.execute(self)
            self._view_action = None

    def do_change_focus_action(self):
        if self._focus_point_action:
            self._focus_point_action.execute(self)
            self._focus_point_action = None

    def communicate_impl(self):
        if self._communication is not None:
            self._communication.execute(self)

    def init_impl(self, goalie: bool):
        self._goalie = goalie

    def handle_start(self):
        if self._client is None:
            return False

        if team_config.PLAYER_VERSION < 18:
            log.os_log().warn(
                "PYRUS2D keepaway.base code does not support player version less than 18."
            )
            self._client.set_server_alive(False)
            return False

        # TODO check for config.host not empty

        if not self._client.connect_to(
            IPAddress(team_config.HOST, team_config.PLAYER_PORT)
        ):
            log.os_log().error("ERROR failed to connect to server")
            self._client.set_server_alive(False)
            return False

        if not self.send_init_command():
            return False
        return True

    def handle_exit(self):
        if self._client.is_server_alive():
            self.send_bye_command()
        log.os_log().info(
            f"player( {self._real_world.self_unum()} ): finished"
        )  # TODO : Not working

    def see_state(self):
        return self._see_state

    # def run(self):
    #     last_time_rec = time.time()
    #     waited_msec: int = 0
    #     timeout_count: int = 0
    #     while self._client.is_server_alive():
    #         length, message, server_address = self._client.recv_message()
    #         if len(message) == 0:
    #             waited_msec += team_config.SOCKET_INTERVAL
    #             timeout_count += 1
    #             if time.time() - last_time_rec > 3:
    #                 self._client.set_server_alive(False)
    #                 break
    #         else:
    #             self.parse_message(message.decode())
    #             last_time_rec = time.time()
    #             waited_msec = 0
    #             timeout_count = 0

    #         if ServerParam.i().synch_mode():
    #             if self.think_received():
    #                 self.action()
    #                 self.debug_players()
    #                 self._think_received = False
    #         else:
    #             if self.is_decision_time(timeout_count, waited_msec) or (
    #                 self._last_decision_time != self._current_time
    #                 and self.world().see_time() == self._current_time
    #             ):
    #                 # print(self._team_name)
    #                 self.action()
    #         self.flush_logs()
    #         if len(message) > 0:
    #             print(pt.get())
    #     self.send_bye_command()

    ## new implementation. This method

    def run(self):
        last_time_rec = time.time()
        waited_msec: int = 0
        timeout_count: int = 0
        while self._client.is_server_alive():
            # with self._lock:
            command = PlayerCheckBallCommand()
            # self._client.send_message(command.str())

            length, message, server_address = self._client.recv_message()
            if len(message) == 0:
                waited_msec += team_config.SOCKET_INTERVAL
                timeout_count += 1
                if time.time() - last_time_rec > 3:
                    self._client.set_server_alive(False)
                    break
            else:
                # print(message.decode())
                self.parse_message(message.decode())
                last_time_rec = time.time()
                waited_msec = 0
                timeout_count = 0

            if ServerParam.i().synch_mode():
                if self.think_received():
                    self.action()
                    self.debug_players()
                    self._think_received = False
            else:
                if self.is_decision_time(timeout_count, waited_msec) or (
                    self._last_decision_time != self._current_time
                    and self.world().see_time() == self._current_time
                ):
                    # self._lock.wait()
                    self.action()
                    # self._lock.acquire()
                    # # with self._lock:
                    #     #     print(self._team_name)
                    # self._shared_values[
                    #         self.world().self_unum()
                    #     ] = self._current_time
                    # current_values = list(self._shared_values)
                    # print(current_values)
                    # self._lock.release()
                    # self._event.set()  # Signal that the numbers are ready to print
                    # self.action()
                    # self._event.wait()
                    # print(current_values)
                    # self._event.clear()  # Clear the event for the next iteration

            self.flush_logs()
            if len(message) > 0:
                print(pt.get())
        self.send_bye_command()

    def debug_players(self):
        for p in (
            self.world()._teammates
            + self.world()._opponents
            + self.world()._unknown_players
        ):
            if p.pos_valid():
                log.sw_log().world().add_circle(
                    1, center=p.pos(), color=Color(string="blue")
                )
        if self.world().ball().pos_valid():
            log.sw_log().world().add_circle(
                center=self.world().ball().pos(),
                r=0.5,
                color=Color(string="blue"),
                fill=True,
            )

        if self.full_world_exists():
            for p in (
                self.full_world()._teammates
                + self.full_world()._opponents
                + self.full_world()._unknown_players
            ):
                if p.pos_valid():
                    log.sw_log().world().add_circle(
                        1, center=p.pos(), color=Color(string="red")
                    )
            if self.world().ball().pos_valid():
                log.sw_log().world().add_circle(
                    center=self.world().ball().pos(),
                    r=0.5,
                    color=Color(string="red"),
                    fill=True,
                )

    def change_player_type_parser(self, msg: str):
        data = msg.strip("\x00").strip(")(").split(" ")
        if len(data) != 3:
            return

        u = int(data[1])
        t = int(data[2])

        self.real_world().set_our_player_type(u, t)
        if self.full_world_exists():
            self.full_world().set_our_player_type(u, t)

    def parse_message(self, message: str):
        # print("parse message is called", message)
        if message.startswith("(sense_body"):
            self.parse_sense_body_message(message)
        elif message.startswith("(see"):
            self.parse_see_message(message)
        elif message.startswith("(init"):
            self.parse_init(message)
        elif message.startswith("(server_param"):
            ServerParam.i().parse(message)
        elif message.startswith("(fullstate"):
            self.parse_full_state_message(message)
        elif message.startswith("(hear"):
            # pass
            self.hear_parser(message)
        elif message.startswith("(change_player_type"):
            self.change_player_type_parser(message)
        elif message.startswith("(player_type"):
            self._real_world.parse(message)
            self._full_world.parse(message)
        elif message.startswith("(think"):
            self._think_received = True
        elif message.find("(ok") != -1:
            # print(message)
            pass
            # self._client.send_message(TrainerDoneCommand().str())
        else:
            log.os_log().error(f"Pyrus can not parse this message: {message}")

    def do_check_ball(self):
        self._client.send_message(PlayerCheckBallCommand().str())

    def do_dash(self, power, angle=0):
        if self.world().self().is_frozen():
            log.os_log().error(
                f"(do dash) player({self._real_world.self_unum()} is frozen!"
            )
            return False
        self._last_body_command.append(self._effector.set_dash(power, float(angle)))
        return True

    def do_turn(self, angle):
        if self.world().self().is_frozen():
            log.os_log().error(
                f"(do turn) player({self._real_world.self_unum()} is frozen!"
            )
            return False
        self._last_body_command.append(self._effector.set_turn(float(angle)))
        return True

    def do_move(self, x, y):
        if self.world().self().is_frozen():
            log.os_log().error(
                f"(do move) player({self._real_world.self_unum()} is frozen!"
            )
            return False
        self._last_body_command.append(self._effector.set_move(x, y))
        return True

    def do_kick(self, power: float, rel_dir: AngleDeg):
        if self.world().self().is_frozen():
            log.os_log().error(
                f"(do kick) player({self._real_world.self_unum()} is frozen!"
            )
            return False
        self._last_body_command.append(self._effector.set_kick(power, rel_dir))
        return True

    ### all things below are new implementation

    # This method is not used in the code. It

    # def predict_command_to_intercept_ball(self, obj_type, soc):
    #     soc
    #     VecPosition pos, vel, posPred, posBall(0, 0), posBallTmp, velBall, posAgent;
    #     AngDeg angBody, angNeck;

    #     min_cycles_ball = 100
    #     first_ball = 100
    #     ##TODO: mamximal kick dist should be in server settings

    #     maximal_kick_dist = (
    #         self.world().self().player_type().kickable_margin()
    #         + self.world().self().player_type().player_size()
    #         + ServerParam.i().ball_size()
    #     )

    #     min_old_intercept = 100
    #     distance_of_intercept = 10.0
    #     old_Intercept = UnknownIntValue;
    #     Time timeLastIntercepted(-1, 0);
    #     static VecPosition posOldIntercept;

    # def do_intercept(self,is_goalie):
    #     soc = self.intercept_close_goalie() if is_goalie else self.intercept_close()
    #     soc2 = None
    #     if soc.command_type() != CMD_ILLEGAL and is_goalie:
    #         print("Log: intercept in two cycles")
    #         return soc
    #     print(f"Log: start intercept, obj {self.world().self().object_type()}")
    #     soc2 = self.world().predict_command_to_intercept_ball(
    #         self.world().self().object_type(), soc
    #     )
    #     if soc2.is_illegal():
    #         print("Log: soc2 illegal")
    #         return self.move_to_pos(self.world().ball().pos(), 30.0)
    #     return soc2

    def accel_ball_vel(self, vel: Vector2D):
        # print("accel ball vel is called")

        SP = ServerParam.i()
        ang = self.world().self().body()
        ball_vel = self.world().ball().vel()
        acc_des = vel - ball_vel
        # pow = None
        # actual_angle = None
        # // if acceleration can be reached, create shooting vector
        if acc_des.r() < SP.ball_accel_max():
            power = self.world().get_kick_power_speed(acc_des.r())
            diff_angle = acc_des.dir() - ang
            actual_angle = AngleDeg.normalize_angle(diff_angle.degree())
            if power <= SP.max_power():
                self._last_body_command.append(
                    self._effector.set_kick(power, actual_angle)
                )
                return
        # // else determine vector that is in direction 'velDes' (magnitude is lower)
        power = SP.max_power()
        speed = self.world().self().player_type().kick_power_rate() * power
        tmp = ball_vel.rotate(-vel.th()).get_y()
        # print("ball rotated velocity is : ", tmp)
        actual_angle = vel.th() - AngleDeg.asin_deg(tmp / speed)
        # print("first calculated actual angle is : ", actual_angle)
        actual_angle = AngleDeg.normalize_angle((actual_angle - ang).degree())
        # print("second calculated actual angle is : ", actual_angle)
        # print("power is ", power, "actual angle is ", actual_angle)
        self._last_body_command.append(self._effector.set_kick(power, actual_angle))
        return

    def freeze_ball(self):
        # print("freeze ball is called")
        SP = ServerParam.i()
        maximal_kick_dist = (
            self.world().self().player_type().kickable_margin()
            + self.world().self().player_type().player_size()
            + SP.ball_size()
        )
        pred_pos = Tools.predict_pos_after_n_cycles(self.world().self(), 1, 0)
        # pred_pos = WM->predictAgentPos(1, 0)
        d_power = self.world().get_kick_power_speed(self.world().ball().vel().r())

        if d_power > SP.max_power():
            # Log.log(552, "%d: freeze ball has to much power", WM->getCurrentCycle());
            d_power = SP.max_power()
        d_angle = self.world().ball().pos().th() + 180 - self.world().self().body()
        d_angle = AngleDeg.normalize_angle(d_angle.degree())
        # self._last_body_command.append(self._effector.set_kick(d_power, d_angle))
        # VecPosition posBall, velBall;
        # WM->predictBallInfoAfterCommand(soc, &posBall, &velBall)
        ## check pass commands todo
        # command = self._last_body_command[-1]
        command = PlayerKickCommand(d_power, d_angle)
        agent_pred_pos, agent_pred_vel = Tools.predict_ball_after_command(
            self.world(), command, self.world().ball().pos(), self.world().ball().vel()
        )

        ## check this --
        if self.world().ball().pos().dist(agent_pred_pos) < 0.8 * maximal_kick_dist:
            return self._last_body_command.append(
                self._effector.set_kick(d_power * 0.5, d_angle)
            )
        # Log.log(102, "freeze ball will end up oustide -> accelerate");
        ball_pos = self.world().ball().pos()
        # // kick ball to position inside to compensate when agent is moving
        posTo = pred_pos + Vector2D.polar2vector(
            min(0.7 * maximal_kick_dist, ball_pos.dist(pred_pos) - 0.1),
            (ball_pos - pred_pos).th(),
        )

        vel_des = posTo - ball_pos
        # accelerateBallToVelocity(velDes)
        return self.accel_ball_vel(vel_des)

    def kick_ball_close_to_body(self, angle, dKickRatio):
        # print("kick_ball_close_to_body - ")
        SP = ServerParam.i()
        ang = self.world().self().body()
        pred_pos = Tools.predict_pos_after_n_cycles(self.world().self(), 1, 0)
        dist = SP.player_size() + SP.ball_size() + SP.kickable_margin() * dKickRatio
        ang_global = ang + angle
        ang_global.normal()
        pos_des_ball = pred_pos + Vector2D.polar2vector(dist, ang_global)
        if (
            abs(pos_des_ball.get_y()) > SP.pitch_width() / 2.0
            or abs(pos_des_ball.get_x()) > SP.pitch_length() / 2.0
        ):
            lineBody = Line2D(self.world().self().pos(), ang_global)
            # Line::makeLineFromPositionAndAngle(posAgent, angGlobal)
            # Line lineSide(0, 0, 0)
            lineSide = None
            if abs(pos_des_ball.get_y()) > SP.pitch_width() / 2.0:
                lineSide = Line2D(
                    Vector2D(0, (pos_des_ball.get_x()) * SP.pitch_length() / 2.0),
                    90,
                )
            else:
                lineSide = Line2D(
                    Vector2D(0, -(pos_des_ball.get_x()) * SP.pitch_length() / 2.0),
                    90,
                )
            posIntersect = lineSide.getIntersection(lineBody)
            pos_des_ball = self.world().self().pos() + Vector2D.polar2vector(
                posIntersect.dist(self.world().self().pos()) - 0.2, ang_global
            )

        vecDesired = pos_des_ball - self.world().ball().pos()
        vecShoot = vecDesired - self.world().ball().vel()
        d_power = self.world().get_kick_power_speed(vecShoot.r())
        ang_actual = vecShoot.dir() - ang
        ang_actual.normal()
        if d_power > SP.max_power() and self.world().ball().vel().r() > 0.1:
            # Log.log(500, "kickBallCloseToBody: cannot compensate ball speed, freeze");
            # Log.log(102, "kickBallCloseToBody: cannot compensate ball speed, freeze");
            # print("power is line 756 ", d_power)
            # print("kickBallCloseToBody: cannot compensate ball speed, freeze")
            return self.freeze_ball()
        elif d_power > SP.max_power():
            ## removed this for now.
            if self.world().game_mode().type() is not GameModeType.PlayOn:
                # if (WM->isDeadBallUs()):
                if (self.world().ball().pos().th()).normalize_angle() > 25:
                    # Log.log(102, "dead ball situation, turn to ball");
                    # turnBodyToObject(OBJECT_BALL)
                    # print("print game type code ")
                    return
                else:
                    d_power = 100
        else:
            # Log.log(102, "(kick %f %f), vecDesired (%f,%f) %f posDes(%f,%f)",
            #         dPower, angActual, vecDesired.getX(), vecDesired.getY(), ang,
            #         posDesBall.getX(), posDesBall.getY());
            # return
            # SoccerCommand(CMD_KICK, dPower, angActual)
            # print("power is line 774 ", d_power)
            command = self._effector.set_kick(d_power, ang_actual)

            return self._last_body_command.append(
                self._effector.set_kick(d_power, ang_actual)
            )
            # return command

    ## TODO: pass message
    ## speed has to be precomupted.

    def update_receiver(self):
        receivers = []
        log.sw_log().pass_().add_text("===update receivers".format())
        for p in self.world().teammates():
            if p is None:
                log.sw_log().pass_().add_text("-----<<< TM is none")
                continue
            if p.unum() <= 0:
                log.sw_log().pass_().add_text(f"-----<<< TM unum is {p.unum()}")
                continue
            if p.unum() == self.world().self().unum():
                log.sw_log().pass_().add_text(f"-----<<< TM unum is {p.unum()} (self)")
                continue
            if p.pos_count() > 10:
                log.sw_log().pass_().add_text(
                    f"-----<<< TM unum pos count {p.pos_count()}"
                )
                continue
            if p.is_tackling():
                log.sw_log().pass_().add_text(f"-----<<< TM is tackling")
                continue
            log.sw_log().pass_().add_text(f"--->>>>> TM {p.unum()} is added")
            receivers.append(p)
        receivers = sorted(receivers, key=lambda p: p.pos().x(), reverse=True)
        return receivers

    def update_opponents(self):
        receivers = []
        log.sw_log().pass_().add_text("===update receivers".format())
        for p in self.world().opponents():
            if p is None:
                log.sw_log().pass_().add_text("-----<<< TM is none")
                continue
            if p.unum() <= 0:
                log.sw_log().pass_().add_text(f"-----<<< TM unum is {p.unum()}")
                continue

            if p.pos_count() > 10:
                log.sw_log().pass_().add_text(
                    f"-----<<< TM unum pos count {p.pos_count()}"
                )
                continue
            if p.is_tackling():
                log.sw_log().pass_().add_text(f"-----<<< TM is tackling")
                continue
            log.sw_log().pass_().add_text(f"--->>>>> TM {p.unum()} is added")
            receivers.append(p)
        receivers = sorted(receivers, key=lambda p: p.pos().x(), reverse=True)
        return receivers

    def predict_receiver_reach_step(
        self, receiver, pos: Vector2D, use_penalty, pass_type
    ):
        ptype = receiver.player_type()

        target_dist = receiver.inertia_point(1).dist(pos)
        n_turn = (
            1
            if receiver.body_count() > 0
            else Tools.predict_player_turn_cycle(
                ptype,
                receiver.body(),
                receiver.vel().r(),
                target_dist,
                (pos - receiver.inertia_point(1)).th(),
                ptype.kickable_area(),
                False,
            )
        )
        dash_dist = target_dist

        # if use_penalty:
        #     dash_dist += receiver.penalty_distance_;

        if pass_type == "L":
            dash_dist *= 1.05

            dash_angle = (pos - receiver.pos()).th()

            if (
                dash_angle.abs() > 90.0
                or receiver.body_count() > 1
                or (dash_angle - receiver.body()).abs() > 30.0
            ):
                n_turn += 1

        n_dash = ptype.cycles_to_reach_distance(dash_dist)

        n_step = n_turn + n_dash if n_turn == 0 else n_turn + n_dash + 1
        return n_step

    def accel_ball_vel_to(
        self,
        receiver,
        receive_point: Vector2D,
        min_step,
        max_step,
        min_first_ball_speed,
        max_first_ball_speed,
        min_receive_ball_speed,
        max_receive_ball_speed,
        ball_move_dist,
        ball_move_angle: AngleDeg,
    ):
        import pyrusgeom.soccer_math as smath

        debug_pass = True
        sp = ServerParam.i()
        index = 0
        for step in range(min_step, max_step + 1):
            index += 1
            first_ball_speed = smath.calc_first_term_geom_series(
                ball_move_dist, sp.ball_decay(), step
            )

            if first_ball_speed < min_first_ball_speed:
                if debug_pass:
                    log.sw_log().pass_().add_text(
                        "##Pass {},to {} {}, step:{}, ball_speed:{}, first ball speed is low".format(
                            index,
                            receiver.unum(),
                            receiver.pos(),
                            step,
                            first_ball_speed,
                        )
                    )
                    # self.debug_list.append((index, receive_point, False))
                break

            if max_first_ball_speed < first_ball_speed:
                if debug_pass:
                    log.sw_log().pass_().add_text(
                        "##Pass {},to {} {}, step:{}, ball_speed:{}, first ball speed is high".format(
                            index,
                            receiver.unum(),
                            receiver.pos(),
                            step,
                            first_ball_speed,
                        )
                    )
                    # self.debug_list.append((self.index, receive_point, False))
                continue

            receive_ball_speed = first_ball_speed * pow(sp.ball_decay(), step)

            if receive_ball_speed < min_receive_ball_speed:
                if debug_pass:
                    log.sw_log().pass_().add_text(
                        "##Pass {},to {} {}, step:{}, ball_speed:{}, rball_speed:{}, receive ball speed is low".format(
                            index,
                            receiver.unum(),
                            receiver.pos(),
                            step,
                            first_ball_speed,
                            receive_ball_speed,
                        )
                    )
                    # self.debug_list.append((self.index, receive_point, False))
                break

            if max_receive_ball_speed < receive_ball_speed:
                if debug_pass:
                    log.sw_log().pass_().add_text(
                        "##Pass {},to {} {}, step:{}, ball_speed:{}, rball_speed:{}, receive ball speed is high".format(
                            index,
                            receiver.unum(),
                            receiver.pos(),
                            step,
                            first_ball_speed,
                            receive_ball_speed,
                        )
                    )
                    # self.debug_list.append((self.index, receive_point, False))
                continue
            # print("ball speed is ", first_ball_speed)
            self.accel_ball_vel(
                Vector2D.polar2vector(first_ball_speed * 0.5, ball_move_angle)
            )
            return

    def do_kick_2(self, receiver, speed):
        import pyrusgeom.soccer_math as smath
        import math

        debug_pass = True
        sp = ServerParam.i()
        min_receive_step = 4
        max_receive_step = 20

        min_leading_pass_dist = 3.0
        max_leading_pass_dist = 0.8 * smath.inertia_final_distance(
            sp.ball_speed_max(), sp.ball_decay()
        )
        max_receive_ball_speed = sp.ball_speed_max() * pow(
            sp.ball_decay(), min_receive_step
        )

        ## not needed but for now minimum distance is set to half of the field
        max_player_distance = 20.0
        if receiver.pos().dist(self.world().ball().pos()) > max_player_distance:
            if debug_pass:
                log.sw_log().pass_().add_text(
                    "#####LPass to {} {}, player is far".format(
                        receiver.unum(), receiver.pos()
                    )
                )
            return

        abgle_divs = 8
        angle_step = 360.0 / abgle_divs
        dist_divs = 4
        dist_step = 1.1

        ptype = receiver.player_type()
        max_ball_speed = self.world().self().kick_rate() * sp.max_power()
        if self.world().game_mode().type() == GameModeType.PlayOn:
            max_ball_speed = sp.ball_speed_max()
        min_ball_speed = sp.default_player_speed_max()

        max_receive_ball_speed = min(
            max_receive_ball_speed,
            ptype.kickable_area()
            + (sp.max_dash_power() * ptype.dash_power_rate() * ptype.effort_max())
            * 1.5,
        )
        min_receive_ball_speed = 0.001

        angle_from_ball = (receiver.pos() - self.world().ball().pos()).th()
        for d in range(1, dist_divs + 1):
            ## compare this move distance with old implementation
            player_move_dist = dist_step * d
            a_step = 2 if player_move_dist * 2.0 * math.pi / abgle_divs < 0.6 else 1
            for a in range(abgle_divs + 1):
                angle = angle_from_ball + angle_step * a
                receive_point = receiver.inertia_point(1) + Vector2D.from_polar(
                    player_move_dist, angle
                )
                move_dist_penalty_step = 0
                ball_move_line = Line2D(self.world().ball().pos(), receive_point)
                player_line_dist = ball_move_line.dist(receiver.pos())
                move_dist_penalty_step = int(player_line_dist * 0.3)
                if (
                    receive_point.x() > sp.keepaway_length() / 2 - 3.0
                    or receive_point.x() < -sp.keepaway_length() / 2 + 5.0
                    or receive_point.abs_y() > sp.keepaway_width() / 2 - 3.0
                ):
                    if debug_pass:
                        log.sw_log().pass_().add_text(
                            "#####LPass to {} {}, out of field".format(
                                receiver.unum(), receive_point
                            )
                        )
                    continue
                ball_move_dist = self.world().ball().pos().dist(receive_point)

                if (
                    ball_move_dist < min_leading_pass_dist
                    or max_leading_pass_dist < ball_move_dist
                ):
                    if debug_pass:
                        log.sw_log().pass_().add_text(
                            "#####LPass to {} {}, so far or so close".format(
                                receiver.unum(), receive_point
                            )
                        )
                    continue

                teammates = self.update_receiver()
                nearest_receiver = Tools.get_nearest_teammate(
                    self.world(), receive_point, teammates
                )
                if nearest_receiver.unum() != receiver.unum():
                    if debug_pass:
                        log.sw_log().pass_().add_text(
                            "#####LPass to {} {}, {} is closer than receiver ".format(
                                receiver.unum(), receive_point, nearest_receiver.unum()
                            )
                        )
                    continue
                receiver_step = (
                    self.predict_receiver_reach_step(receiver, receive_point, True, "L")
                    + move_dist_penalty_step
                )
                ball_move_angle = (receive_point - self.world().ball().pos()).th()

                min_ball_step = sp.ball_move_step(sp.ball_speed_max(), ball_move_dist)

                start_step = max(max(min_receive_step, min_ball_step), receiver_step)

                if debug_pass:
                    log.sw_log().pass_().add_text(
                        "#####LPass to {} {}".format(receiver.unum(), receive_point)
                    )
                max_step = start_step + 3

                self.accel_ball_vel_to(
                    receiver,
                    receive_point,
                    start_step,
                    max_step,
                    min_ball_speed,
                    max_ball_speed,
                    min_receive_ball_speed,
                    max_receive_ball_speed,
                    ball_move_dist,
                    ball_move_angle,
                )

                return

    def do_kick_to(self, teammate, speed):
        from keepaway.lib.messenger.pass_messenger import PassMessenger

        SP = ServerParam.i()
        tar_pos = teammate.pos()
        # print("kick position ", tar_pos)
        debug_pass = True
        # print("do kick to is called", tar_pos, speed)

        ptype = teammate.player_type()
        receive_point = ptype.inertiaFinalPoint(teammate.pos(), teammate.vel())
        tar_pos = receive_point
        # print("receive point is ", receive_point)

        ball_pos = self.world().ball().pos()
        ball_vel = self.world().ball().vel()
        travel_dist = tar_pos - ball_pos
        curr_pos = self.world().self().pos()

        # set polar
        cal_travel_speed = Tools.get_kick_travel(
            travel_dist.r(), speed
        )  # check calculation

        ## this is speed is consistent ()
        vel_des = tar_pos - self.world().ball().pos()
        vel_des.set_length(cal_travel_speed)

        # vel_des = Vector2D.polar2vector(cal_travel_speed, travel_dist.dir())
        # vel_des = (tar_pos - curr_pos).normalized() * speed
        predict_pos = Tools.predict_pos_after_n_cycles(self.world().self(), 1, 0)

        if predict_pos.dist(ball_pos + vel_des) < SP.ball_size() + SP.player_size():
            line_segment = Line2D(ball_pos, ball_pos + vel_des)
            body_proj = line_segment.projection(curr_pos)  # is this projection?
            dist = ball_pos.dist(body_proj)
            if vel_des.r() < dist:
                dist -= SP.ball_size() + SP.player_size()
            else:
                dist += SP.ball_size() + SP.player_size()

            if debug_pass:
                # log.sw_log().pass_().add_text(
                # f"=============== Lead Pass to {r.unum()} pos: {r.pos()}")
                log.os_log().debug(f"dist is {dist}")
                log.sw_log().pass_().add_text(
                    "#####Lkick results in collision, change vel_des from {} ".format(
                        vel_des
                    )
                )

            vel_des = vel_des.set_polar(dist, vel_des.dir())

        log.sw_log().pass_().add_text(
            "ball ({},{}), agent ({},{}), to ({},{}) ang {} {}".format(
                ball_pos.get_x(),
                ball_pos.get_y(),
                self.world().self().pos().get_x(),
                self.world().self().pos().get_y(),
                tar_pos.get_x(),
                tar_pos.get_y(),
                self.world().self().body(),
                self.world().self().neck(),
            )
        )

        # log.sw_log(
        #     f"ball ({ball_pos.get_x()},{ball_pos.get_y()}), agent ({self.world().self().pos().get_x()},{self.world().self().pos().get_y()}), to ({tar_pos.get_x()},{tar_pos.get_y()}) ang {self.world().self().body()} {self.world().self().neck()}",
        # )

        # dist_opp = 1000.0
        # closest_opp = self.world().opponents_from_ball()
        # if closest_opp[0] is not None:
        #     dist_opp = closest_opp[0].pos().dist(ball_pos)

        teammates = self.update_opponents()

        nearest_opp = Tools.get_nearest_teammate(
            self.world(), receive_point, teammates
        )  ## this fails sometimes
        if nearest_opp is None:
            nearest_opp_list = self.world().opponents_from_ball()
            if nearest_opp_list[0] is not None:
                nearest_opp = nearest_opp_list[0]

        if nearest_opp.unum() != teammate.unum():
            if debug_pass:
                log.sw_log().pass_().add_text(
                    "#####kpLPass to {} {}, {} is closer than receiver ".format(
                        teammate.unum(), receive_point, nearest_opp.unum()
                    )
                )

        dist_opp = nearest_opp.pos().dist(ball_pos)

        # // can never reach point
        if vel_des.r() > SP.ball_speed_max():
            pow = SP.max_power()
            speed = self.world().self().player_type().kick_power_rate() * pow
            tmp = ball_vel.rotate(-vel_des.dir()).get_y()
            ang = vel_des.dir() - AngleDeg.asin_deg(tmp / speed)
            speedpred = (ball_vel + Vector2D.polar2vector(speed, ang)).r()
            # but ball acceleration in right direction is very high

            # player kick prop 0.85 - handcoded
            if speedpred > 0.85 * SP.ball_accel_max():
                if debug_pass:
                    log.sw_log().pass_().add_text(
                        "#####LPass pos {} {} too far, but can acc ball good to  {} , {} , {} ".format(
                            vel_des.x(), vel_des.y(), speed, speedpred, tmp
                        )
                    )
                # if debug_pass:
                #     log.sw_log().pass_().add_text(
                #         "##### pos {} {} too far, but can acc ball good to  {} , {} , {} ".format(
                #             vel_des.x(), vel_des.y(), speed, speedpred, tmp
                #         )
                #     )

                # // shoot nevertheless
                # accelerateBallToVelocity(vel_des)

                # print("saying pass message")
                self.add_say_message(
                    PassMessenger(
                        teammate.unum_,
                        tar_pos,
                        self.effector().queued_next_ball_pos(),
                        self.effector().queued_next_ball_vel(),
                    )
                )

                self.accel_ball_vel(vel_des)
                ## add message
                return
            elif (
                self.world().self().player_type().kick_power_rate()
                > 0.85 * SP.kick_power_rate()
            ):
                if debug_pass:
                    log.sw_log().pass_().add_text(
                        "#####LPass point too far, freeze ball"
                    )
                # // freeze ball
                return self.freeze_ball()
            else:
                # Log.log(102, "point too far, reposition ball (k_r = %f)",
                #         WM->getActualKickPowerRate() / (SS->getKickPowerRate()));
                # // else position ball better
                # kickBallCloseToBody(0);
                if debug_pass:
                    log.sw_log().pass_().add_text(
                        "#####LPass point too far, reposition ball".format(
                            self.world().self().player_type().kick_power_rate()
                            / SP.kick_power_rate()
                        )
                    )

                # print("kick_ball_close_to_body 1")
                self.add_say_message(
                    PassMessenger(
                        teammate.unum(),
                        tar_pos,
                        self.effector().queued_next_ball_pos(),
                        self.effector().queued_next_ball_vel(),
                    )
                )

                return self.kick_ball_close_to_body(0, 0.16)
        # // can reach point
        else:
            # print("can reach point")
            # print("is pass accurate ?? ", tar_pos)
            # not not target position here
            accBallDes = vel_des - ball_vel
            dPower = self.world().get_kick_power_speed(accBallDes.r())
            # // with current ball speed
            if dPower <= 1.05 * SP.max_power() or (
                dist_opp < 2.0 and dPower <= 1.30 * SP.max_power()
            ):
                # // perform shooting action
                # accelerateBallToVelocity(velDes);
                # print("saying pass message 2")
                self.add_say_message(
                    PassMessenger(
                        teammate.unum(),
                        tar_pos,
                        self.effector().queued_next_ball_pos(),
                        self.effector().queued_next_ball_vel(),
                    )
                )
                return self.accel_ball_vel(vel_des)
            else:
                if debug_pass:
                    log.sw_log().pass_().add_text(
                        "#####LPass point good, but reposition ball since need {}".format(
                            dPower
                        )
                    )
                ## TODO: check this part this wrong
                # command = self.kick_ball_close_to_body(0, 0.16)
                vecDesired = tar_pos - self.world().ball().pos()
                vecShoot = vecDesired - self.world().ball().vel()
                ang_actual = vecShoot.dir() - self.world().self().body()
                ang_actual.normal()

                command = self._effector.set_kick(dPower, ang_actual)
                # command = self._last_body_command[-1]
                # print("command is ", command.type())
                # WM->predictBallInfoAfterCommand(soc, &posPredBall);
                ball_pred_pos, ball_pred_vel = Tools.predict_ball_after_command(
                    self.world(),
                    command,
                    ball_pos,
                    ball_vel,
                )
                dist_opp = ball_pred_pos.dist(self.world().self().pos())

                self.add_say_message(
                    PassMessenger(
                        teammate.unum(),
                        tar_pos,
                        self.effector().queued_next_ball_pos(),
                        self.effector().queued_next_ball_vel(),
                    )
                )

            return self.kick_ball_close_to_body(0, 0.16)

    # def do_kick_to(self, power: float, rel_dir: AngleDeg, target: Vector2D):
    #     print("kick to is called")
    #     if self.world().self().is_frozen():
    #         log.os_log().error(
    #             f"(do kick) player({self._real_world.self_unum()} is frozen!"
    #         )
    #         return False
    #     self._last_body_command.append(
    #         self._effector.set_kick_to(power, rel_dir, target)
    #     )
    #     return True

    def do_tackle(self, power_or_dir: float, foul: bool):
        if self.world().self().is_frozen():
            log.os_log().error(
                f"(do tackle) player({self._real_world.self_unum()} is frozen!"
            )
            return False
        self._last_body_command.append(self._effector.set_tackle(power_or_dir, foul))
        return True

    def do_catch(self):
        wm = self.world()
        if wm.self().is_frozen():
            log.os_log().error(
                f"(do catch) player({self._real_world.self_unum()} is frozen!"
            )
            return False

        if not wm.self().goalie():
            log.os_log().error(
                f"(do catch) player({self._real_world.self_unum()} is not goalie!"
            )
            return False

        if (
            wm.game_mode().type() is not GameModeType.PlayOn
            and not wm.game_mode().type().is_penalty_taken()
        ):
            log.os_log().error(
                f"(do catch) player({self._real_world.self_unum()} play mode is not play_on!"
            )
            return False

        if not wm.ball().rpos_valid():
            log.os_log().error(
                f"(do catch) player({self._real_world.self_unum()} ball rpos is not valid!"
            )
            return False

        self._last_body_command.append(self.effector().set_catch())

    def do_turn_neck(self, moment: AngleDeg) -> bool:
        self._last_body_command.append(self._effector.set_turn_neck(moment))
        return True

    def do_change_view(self, width: ViewWidth) -> bool:
        self._last_body_command.append(self._effector.set_change_view(width))
        return True

    def do_change_focus(self, moment_dist: float, moment_dir: Union[float, AngleDeg]):
        if isinstance(moment_dir, float) or isinstance(moment_dir, int):
            moment_dir = AngleDeg(moment_dir)

        aligned_moment_dist = moment_dist
        if self.world().self().focus_point_dist() + aligned_moment_dist < 0.0:
            log.os_log().warn(
                f"(do_change_focus) player({self._real_world.self_unum()} focus dist can not be less than 0"
            )
            aligned_moment_dist = -self.world().self().focus_point_dist()
        if self.world().self().focus_point_dist() + aligned_moment_dist > 40.0:
            log.os_log().warn(
                f"(do_change_focus) player({self._real_world.self_unum()} focus dist can not be more than 40"
            )
            aligned_moment_dist = 40.0 - self.world().self().focus_point_dist()
        next_view = self.effector().queued_next_view_width()
        next_half_angle = next_view.width() * 0.5

        aligned_moment_dir = moment_dir
        focus_point_dir_after_change_view = AngleDeg(
            min_max(
                -next_half_angle,
                self.world().self().focus_point_dir().degree(),
                next_half_angle,
            )
        )
        if (
            focus_point_dir_after_change_view.degree() + aligned_moment_dir.degree()
            < -next_half_angle
        ):
            aligned_moment_dir = (
                -next_half_angle - focus_point_dir_after_change_view.degree()
            )
        elif (
            focus_point_dir_after_change_view.degree() + aligned_moment_dir.degree()
            > next_half_angle
        ):
            aligned_moment_dir = (
                next_half_angle - focus_point_dir_after_change_view.degree()
            )

        self._last_body_command.append(
            self._effector.set_change_focus(aligned_moment_dist, aligned_moment_dir)
        )

        return True

    def add_say_message(self, message: Messenger):
        self._effector.add_say_message(message)

    def do_attentionto(self, side: SideID, unum: int):
        if side is SideID.NEUTRAL:
            # log.os_log().error("(player agent do attentionto) side is neutral!")
            return False

        if unum == UNUM_UNKNOWN or not (1 <= unum <= 11):
            # log.os_log().error(f"(player agent do attentionto) unum is not in range! unum={unum}")
            return False

        if self.world().our_side() == side and self.world().self().unum() == unum:
            # log.os_log().error(f"(player agent do attentionto) attentioning to self!")
            return False

        if (
            self.world().self().attentionto_side() == side
            and self.world().self().attentionto_unum() == unum
        ):
            # log.os_log().error(f"(player agent do attentionto) already attended to the player! unum={unum}")
            return False

        self._last_body_command.append(self._effector.set_attentionto(side, unum))
        return True

    def do_attentionto_off(self):
        self._last_body_command.append(self._effector.set_attentionto_off())
        return True

    if team_config.WORLD_IS_REAL_WORLD:

        def world(self):
            return self._real_world

        def main_world(self):
            return self._real_world

        def first_world(self):
            return self._real_world

    else:

        def world(self) -> WorldModel:
            return self._full_world

        def main_world(self):
            return self._full_world

        def first_world(self):
            return self._full_world

    if team_config.S_WORLD_IS_REAL_WORLD:

        def s_world(self):
            return self._real_world

        def secondary_world(self):
            return self._real_world

        def second_world(self):
            return self._real_world

    else:

        def s_world(self) -> WorldModel:
            return self._full_world

        def secondary_world(self):
            return self._full_world

        def second_world(self):
            return self._full_world

    def real_world(self) -> WorldModel:
        return self._real_world

    def full_world(self) -> WorldModel:
        return self._full_world

    def effector(self):
        return self._effector

    def action_impl(self):
        pass

    def full_world_exists(self):
        if ServerParam.i().is_fullstate(self._real_world.our_side()):
            return True
        return False

    def debug_after_sense_msg(self):
        if DEBUG:
            log.sw_log().world().add_text(
                "===Sense Body Results self===\n" + str(self.world().self())
            )
            log.sw_log().world().add_text(
                "===Sense Body Results ball===\n" + str(self.world().ball())
            )
            log.os_log().debug(
                "===Sense Body Results self===\n" + str(self.world().self())
            )
            log.os_log().debug(
                "===Sense Body Results ball===\n" + str(self.world().ball())
            )

    def update_real_world_before_decision(self):
        self._effector.check_command_count(self._sense_body_parser)
        self.real_world().update_by_last_cycle(self._effector, self._current_time)
        self.real_world().update_world_after_sense_body(
            self._sense_body_parser, self._effector, self._current_time
        )
        self.debug_after_sense_msg()
        if self._see_parser.time() == self._current_time:
            self.real_world().update_world_after_see(
                self._see_parser,
                self._sense_body_parser,
                self.effector(),
                self._current_time,
            )
        self.real_world().update_just_before_decision(
            self._effector, self._current_time
        )

    def update_full_world_before_decision(self):
        self._effector.check_command_count_with_fullstate_parser(
            self._full_state_parser
        )
        self.full_world().update_by_last_cycle(self._effector, self._current_time)
        self.full_world().update_world_after_sense_body(
            self._sense_body_parser, self._effector, self._current_time
        )
        self.full_world().update_by_full_state_message(self._full_state_parser)
        self.full_world().update_just_before_decision(
            self._effector, self._current_time
        )

    def update_before_decision(self):
        self.update_real_world_before_decision()
        if self.full_world_exists():
            self.update_full_world_before_decision()

    def action(self):
        if (
            self.world().self_unum() is None
            or self.world().self().unum() != self.world().self_unum()
        ):
            return
        self.update_before_decision()

        KickTable.instance().create_tables(
            self.world().self().player_type()
        )  # TODO should be moved!

        self._effector.reset()
        self.action_impl()
        self.do_view_action()
        self.do_neck_action()
        self.do_change_focus_action()

        self.communicate_impl()

        self._last_decision_time = self._current_time.copy()
        log.os_log().debug("body " + str(self.world().self().body()))
        log.os_log().debug("pos " + str(self.world().self().pos()))

        self.real_world().update_just_after_decision(self._effector)
        if self.full_world_exists():
            self.full_world().update_just_after_decision(self._effector)
        if DEBUG:
            log.os_log().debug("======Self after decision======")
            log.os_log().debug("turn " + str(self.effector().get_turn_info()))
            log.os_log().debug("dash " + str(self.effector().get_dash_info()))
            log.os_log().debug(
                "next body " + str(self.effector().queued_next_self_body())
            )
            log.os_log().debug(
                "next pos " + str(self.effector().queued_next_self_pos())
            )
            # log.os_log().debug(str(self.world().self().long_str()))

        self._see_state.set_view_mode(self.world().self().view_width())

        message_command = self._effector.make_say_message_command(self.world())
        if message_command:
            self._last_body_command.append(message_command)
        commands = self._last_body_command
        # if self.world().our_side() == SideID.RIGHT:
        # PlayerCommandReverser.reverse(commands) # unused :\ # its useful :) # nope not useful at all :(
        if self._is_synch_mode:
            commands.append(PlayerDoneCommand())
        message = self.make_commands(commands)
        log.debug_client().add_message("\nsent message: " + str(message))
        if DEBUG:
            log.os_log().debug("sent message: " + str(message))
        self._client.send_message(message)

        self._last_body_command = []
        self._effector.clear_all_commands()

    def make_commands(self, commands):
        self._effector.update_after_actions()

        message = PlayerSendCommands.all_to_str(commands)
        return message

    def parse_init(self, message):
        message = message.split(" ")
        unum = int(message[2])
        side = message[1]

        self._real_world.init(self._team_name, side, unum, self._goalie)
        # if self.full_world_exists():
        self._full_world.init(self._team_name, side, unum, False)
        log.setup(self._team_name, unum, self._current_time)

    def set_view_action(self, view_action: ViewAction):
        self._view_action = view_action

    def set_neck_action(self, neck_action: NeckAction):
        self._neck_action = neck_action

    def set_focus_point_action(self, focus_point_action: FocusPointAction):
        self._focus_point_action = focus_point_action

    def flush_logs(self):
        if log.debug_client():
            log.debug_client().write_all(self.world(), None)  # TODO add action effector
            log.sw_log().flush()
