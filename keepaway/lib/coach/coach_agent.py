import logging
import time

from keepaway.lib.debug.debug import log
from keepaway.lib.messenger.free_form_messenger import FreeFormMessenger
from keepaway.lib.messenger.messenger import Messenger
from keepaway.lib.network.udp_socket import IPAddress
from keepaway.lib.coach.gloabl_world_model import GlobalWorldModel
from keepaway.lib.player.world_model import WorldModel
from keepaway.lib.player.soccer_agent import SoccerAgent
from keepaway.lib.player_command.coach_command import (
    CoachChangePlayerTypeCommand,
    CoachCommand,
    CoachDoneCommand,
    CoachEyeCommand,
    CoachLookCommand,
    CoachFreeFormMessageCommand,
    CoachInitCommand,
    CoachSendCommands,
    CoachTeamnameCommand,
    CoachCheckBallCommand,
)
from keepaway.lib.rcsc.game_mode import GameMode
from keepaway.lib.rcsc.game_time import GameTime
from keepaway.lib.rcsc.server_param import ServerParam
from keepaway.lib.rcsc.types import HETERO_DEFAULT, HETERO_UNKNOWN, GameModeType

# from keepaway.config import team_config
from keepaway.config from keepaway.config import team_config


# TODO PLAYER PARAMS?


class CoachAgent(SoccerAgent):
    def __init__(self):
        super().__init__()
        self._think_received: bool = True
        self._server_cycle_stopped: bool = True
        self._current_time: GameTime = GameTime(-1, 0)
        self._game_mode: GameMode = GameMode()
        self._world: GlobalWorldModel = GlobalWorldModel()
        # self._world: WorldModel = WorldModel("full")
        self._is_synch_mode: bool = True
        self._last_body_command: list[CoachCommand] = []
        self._free_from_messages: list[FreeFormMessenger] = []

    def send_init_command(self):
        # TODO check reconnection
        # TODO make config class for these data
        # com = CoachInitCommand(team_config.TEAM_NAME, team_config.COACH_VERSION)

        com = CoachInitCommand("keepers", team_config.COACH_VERSION)

        print(com.str())

        if self._client.send_message(com.str()) <= 0:
            print("ERROR failed to connect to server")

            log.os_log().error("ERROR failed to connect to server")
            self._client.set_server_alive(False)
            return False
        return True

    def send_bye_command(self):
        if self._client.is_server_alive() is True:
            # TODO Coach Bye Command needs to be implemented
            # com = PlayerByeCommand()
            # self._agent._client.send_message(com.str())
            self._client.set_server_alive(False)

    @property  # TODO REMOVE PROPERTY
    def think_received(self):
        return self._think_received

    def analyze_init(self, message):
        self.init_dlog(message)
        self.do_eye(True)

    def see_parser(self, message: str):
        if not message.startswith("(player_type"):
            self.parse_cycle_info(message, True)

        self.world().parse(message)
        self.world().update_after_see(self._current_time)

    def parse_cycle_info(self, message: str, by_see_global: bool):
        cycle = int(message.split(" ")[1])
        self.update_current_time(cycle, by_see_global)

    def update_current_time(self, new_time: int, by_see_global: bool):
        if self._server_cycle_stopped:
            if new_time != self._current_time.cycle():
                self._current_time.assign(new_time, 0)
            else:
                if by_see_global:
                    self._current_time.assign(
                        self._current_time.cycle(),
                        self._current_time.stopped_cycle() + 1,
                    )
        else:
            self._current_time.assign(new_time, 0)

    def hear_parser(self, message: str):
        self.parse_cycle_info(message, False)

        _, cycle, sender = tuple(message.split(" ")[:3])
        cycle = int(cycle)

        if sender[0].isnumeric() or sender[0] == "-":  # PLAYER MESSAGE
            self.hear_player_parser(message)
        elif sender == "referee":
            self.hear_referee_parser(message)

    def hear_player_parser(self, message):
        pass

    def update_server_status(self):
        if self._server_cycle_stopped:
            self._server_cycle_stopped = False

        if self._game_mode.is_server_cycle_stopped_mode():
            self._server_cycle_stopped = True

    def hear_referee_parser(self, message: str):
        mode = message.split(" ")[-1].strip(")")
        self._game_mode.update(mode, self._current_time)

        # TODO CARDS AND OTHER STUFF

        self.update_server_status()

        if self._game_mode.type() is GameModeType.TimeOver:
            self.send_bye_command()
            return
        self.world().update_game_mode(self._game_mode, self._current_time)
        # TODO FULL STATE WORLD update

    def analyze_change_player_type(self, msg: str):
        data = msg.strip("()").split(" ")
        n = len(data)
        if n == 4:
            pass
        elif n == 3:
            unum, type = int(data[1]), int(data[2].removesuffix(")\x00"))
            self.world().change_player_type(self.world().our_side(), unum, type)
        elif n == 2:
            unum = int(data[1].removesuffix(")\x00"))
            self.world().change_player_type(
                self.world().their_side(), unum, HETERO_UNKNOWN
            )

    def handle_start(self):
        # print(self._client)
        # print(team_config.COACH_PORT)

        if self._client is None:
            return False

        if team_config.COACH_VERSION < 18:
            log.os_log().error(
                "PYRUS2D keepaway.base code does not support coach version less than 18."
            )
            print("PYRUS2D keepaway.base code does not support coach version less than 18.")
            self._client.set_server_alive(False)
            return False

        # TODO check for config.host not empty

        # print(self._client.connect_to(IPAddress(team_config.HOST, 6002)))

        if not self._client.connect_to(
            IPAddress(team_config.HOST, team_config.COACH_PORT)
        ):
            log.os_log().error("ERROR failed to connect to server")
            print("ERROR failed to connect to server")
            self._client.set_server_alive(False)
            return False

        # print("coach agent handle start 2")
        # print(self.send_init_command())

        if not self.send_init_command():
            return False
        return True

    def handle_exit(self):
        if self._client.is_server_alive():
            self.send_bye_command()
        # log.os_log().info(f"player( {self._real_world.self_unum()} ): finished")

    # def run(self):
    #     while self._client.is_server_alive():
    #         # self.do_check_ball()
    #         length, message, server_address = self._client.recv_message()
    #         if len(message) != 0:
    #             print("coach ", message)
    #             self.parse_message(message.decode())
    #         else:
    #             self._client.set_server_alive(False)
    #             break

    def run(self):
        # print("coach agent run")
        last_time_rec = time.time()
        while True:
            while True:
                self.do_check_ball()
                length, message, server_address = self._client.recv_message()
                if len(message) != 0:
                    print("coach ", message)

                    self.parse_message(message.decode())
                    last_time_rec = time.time()
                    break
                elif time.time() - last_time_rec > 3:
                    self._client.set_server_alive(False)
                    break
                if self.think_received:
                    last_time_rec = time.time()
                    break

            if not self._client.is_server_alive():
                log.os_log().info(f"{team_config.TEAM_NAME} Agent : Server Down")
                break

            if self.think_received:
                self.action()
                self._think_received = False
    # TODO elif for not sync mode

    def do_check_ball(self):
        # command = CoachCheckBallCommand()
        # print(command.str())
        command = CoachTeamnameCommand()
        self._client.send_message(command.str())

    def parse_message(self, message):
        if message.find("(init") != -1:  # TODO Use startwith instead of find
            self.analyze_init(message)
        elif message.find("(server_param") != -1:
            ServerParam.i().parse(message)
        elif message.find("(player_param") != -1:
            pass  # TODO
        elif message.find("(change_player_type") != -1:
            self.analyze_change_player_type(message)
        elif message.find("(see") != -1 or message.find("(player_type") != -1:
            self.see_parser(message)
            self._think_received = True
        elif message.find("(hear") != -1:
            self.hear_parser(message)
        elif message.find("think") != -1:
            self._think_received = True
        elif message.find("(ok") != -1:
            self._client.send_message(CoachDoneCommand().str())
        else:
            self._client.send_message(CoachTeamnameCommand().str())

    def init_dlog(self, message):
        log.setup(self.world().team_name_l(), "coach", self._current_time)

    def world(self) -> GlobalWorldModel:
        return self._world

    def full_world(self) -> GlobalWorldModel:
        return self._world

    def action(self):
        self.action_impl()
        commands = self._last_body_command
        # if self.world().our_side() == SideID.RIGHT:
        # PlayerCommandReverser.reverse(commands) # unused :\ # its useful :) # nope not useful at all :(
        commands.append(CoachDoneCommand())
        for com in commands:
            self._client.send_message(com.str())
        log.sw_log().flush()
        self._last_body_command = []

    def action_impl(self):
        pass

    def do_teamname(self):
        command = CoachTeamnameCommand()
        self._last_body_command.append(command)
        return True

    def send_command(self, commands):  # TODO it should be boolean
        self._client.send_message(CoachSendCommands.all_to_str(commands))

    def do_eye(self, on: bool):
        self._client.send_message(CoachEyeCommand(on).str())

    def do_look(self):
        self._client.send_message(CoachLookCommand().str())

    def do_change_player_type(self, unum: int, type: int):
        if not 1 <= unum <= 11:
            log.os_log().error(
                f"(coach agent do change player type) illegal unum! unum={unum}"
            )
            return False

        if not HETERO_DEFAULT <= type < 18:  # TODO Player PARAM
            log.os_log().error(
                f"(coach agent do change player type) illegal player type! type={type}"
            )
            return False

        self._last_body_command.append(CoachChangePlayerTypeCommand(unum, type))
        return True

    def do_change_player_types(self, types: list[tuple[int, int]]):
        if len(types) == 0:
            log.os_log().error(f"(coach agent do change player types) list is empty")
            return False

        for t in types:
            self.do_change_player_type(t[0], t[1])

        return True

    def add_free_form_message(self, message: FreeFormMessenger):
        self._free_from_messages.append(message)

    def send_free_form_message(self):
        if not self.world().can_send_free_form():
            self._free_from_messages.clear()
            return

        msg = Messenger.encode_all(self._world, self._free_from_messages)
        self._last_body_command.append(CoachFreeFormMessageCommand(msg))
        self.world().inc_free_form_send_count()
