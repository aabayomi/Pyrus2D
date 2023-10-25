import time
from base.decision import (
    get_decision,
    get_decision_keepaway,
)

from base.sample_communication import SampleCommunication
from base.view_tactical import ViewTactical
from lib.action.go_to_point import GoToPoint
from lib.action.intercept import Intercept
from lib.action.neck_body_to_ball import NeckBodyToBall
from lib.action.neck_turn_to_ball import NeckTurnToBall
from lib.action.neck_turn_to_ball_or_scan import NeckTurnToBallOrScan
from lib.action.scan_field import ScanField
from lib.debug.debug import log
from lib.debug.level import Level

# from lib.player.keepaway_player_agent import PlayerAgent
from lib.player.kp_agent import PlayerAgent
from lib.rcsc.server_param import ServerParam
from lib.rcsc.types import GameModeType

from lib.debug.debug import log
from lib.debug.level import Level
from pyrusgeom.vector_2d import Vector2D
from lib.player.trainer_agent import TrainerAgent
from lib.rcsc.types import GameModeType


### TODO :
## 1. Initialization of the world model
## 2. Set main loop
##   a.
## say a message to the player
## conditions for keepers
## keeper with the ball
##  - interpret keeper action
##  - keeper support
##  - look object
##  - taker


# class KeepawayPlayer(PlayerAgent):
#     def __init__(self, team_name):
#         super().__init__(team_name)
#         self._communication = SampleCommunication()

#     # def action_impl(self):
#     #     if self.world().team_name_left() == "":  # TODO left team name...  # TODO is empty...
#     #         self.do_teamname()
#     #         return
#     #     self.sample_action()

#     def action_impl(self):
#         wm = self.world()

#         if self.do_preprocess():
#             return

#         # self.sample_action()
#         get_decision(self)

#     def do_preprocess(self):
#         wm = self.world()

#         if wm.self().is_frozen():
#             self.set_view_action(ViewTactical())
#             self.set_neck_action(NeckTurnToBallOrScan())
#             return True

#         if not wm.self().pos_valid():
#             self.set_view_action(ViewTactical())
#             ScanField().execute(self)
#             return True

#         count_thr = 10 if wm.self().goalie() else 5
#         if wm.ball().pos_count() > count_thr or (
#             wm.game_mode().type() is not GameModeType.PlayOn
#             and wm.ball().seen_pos_count() > count_thr + 10
#         ):
#             self.set_view_action(ViewTactical())
#             NeckBodyToBall().execute(self)
#             return True

#         self.set_view_action(ViewTactical())

#         # if self.do_heard_pass_receive():
#         #     return True

#         return False

#     def sample_action(self):
#         log.sw_log().block().add_text("Sample Action")

#         wm = self.world()
#         ballpos = wm.ball().pos()
#         if ballpos.abs_x() > 10 or ballpos.abs_y() > 10:
#             # for i in range(2, 5):
#             self.do_move_player(wm.team_name_l(), i, Vector2D(-40, i * 5 - 30))
#             self.do_move_ball(Vector2D(0, 0), Vector2D(0, 0))
#             self.do_change_mode(GameModeType.PlayOn)

# ## main loop for keep-away player
# def run(self):
#     last_time_rec = time.time()
#     waited_msec: int = 0
#     timeout_count: int = 0
#     while self._client.is_server_alive():


# class KeepawayPlayer(PlayerAgent):
#     def __init__(self, team_name):
#         super().__init__(team_name)

#         self._communication = SampleCommunication()

#     def start_episode(self, state):
#         """start of a new episode for the agent"""

#         print("start of episode ", state)

#     def end_episode(self, state):
#         """end of the episode for the agent"""
#         print("end of episode ", state)

#     def step(self, reward, state):
#         """step of the agent"""
#         print("step in", reward, state)
#         return 0

#     def sample_action(self):
#         log.sw_log().block().add_text("Sample Action")
#         print("Sample Action")
#         wm = self.world()
#         ballpos = wm.ball().pos()
#         if ballpos.abs_x() > 10 or ballpos.abs_y() > 10:
#             for i in range(1, 12):
#                 self.do_move_player(wm.team_name_l(), i, Vector2D(-40, i * 5 - 30))
#             # self.do_move_ball(Vector2D(0, 0), Vector2D(0, 0))
#             # self.do_change_mode(GameModeType.PlayOn)

#     # def search_ball(self):
#     #     wm = self.world()
#     #     # print(self._team_name)
#     #     if self.do_preprocess_search():
#     #         return
#     #     keepaway_decision(self)

#     # def taker(self):
#     #     if self.do_preprocess_search():
#     #         return
#     #     # taker_decision(self)
#     #     # self.sample_action(self)
#     #     get_decision(self)

#     def action_impl(self):
#         wm = self.world()
#         # print(self._team_name)
#         print("do_preprocess ball position: ", wm.ball().pos())
#         if self.do_preprocess_search():
#             return
#         # get_decision(self)
#         get_decision_keepaway(self)

#     def do_preprocess_search(self):
#         wm = self.world()

#         if wm.self().is_frozen():
#             self.set_view_action(ViewTactical())
#             self.set_neck_action(NeckTurnToBallOrScan())
#             return True

#         if not wm.self().pos_valid():
#             self.set_view_action(ViewTactical())
#             ScanField().execute(self)
#             return True

#         count_thr = 10 if wm.self().goalie() else 5
#         if wm.ball().pos_count() > count_thr or (
#             wm.game_mode().type() is not GameModeType.PlayOn
#             and wm.ball().seen_pos_count() > count_thr + 10
#         ):
#             self.set_view_action(ViewTactical())
#             NeckBodyToBall().execute(self)
#             return True

#         self.set_view_action(ViewTactical())
#         return False

#     def do_preprocess(self):
#         wm = self.world()

#         if wm.self().is_frozen():
#             self.set_view_action(ViewTactical())
#             self.set_neck_action(NeckTurnToBallOrScan())
#             return True

#         if not wm.self().pos_valid():
#             self.set_view_action(ViewTactical())
#             ScanField().execute(self)
#             return True

#         count_thr = 10 if wm.self().goalie() else 5
#         if wm.ball().pos_count() > count_thr or (
#             wm.game_mode().type() is not GameModeType.PlayOn
#             and wm.ball().seen_pos_count() > count_thr + 10
#         ):
#             self.set_view_action(ViewTactical())
#             NeckBodyToBall().execute(self)
#             return True

#         self.set_view_action(ViewTactical())

#         if self.do_heard_pass_receive():
#             return True

#         return False

#     def do_heard_pass_receive(self):
#         wm = self.world()

#         if (
#             wm.messenger_memory().pass_time() != wm.time()
#             or len(wm.messenger_memory().pass_()) == 0
#             or wm.messenger_memory().pass_()[0]._receiver != wm.self().unum()
#         ):
#             return False

#         self_min = wm.intercept_table().self_reach_cycle()
#         intercept_pos = wm.ball().inertia_point(self_min)
#         heard_pos = wm.messenger_memory().pass_()[0]._pos

#         log.sw_log().team().add_text(
#             f"(sample player do heard pass) heard_pos={heard_pos}, intercept_pos={intercept_pos}"
#         )

#         if (
#             not wm.kickable_teammate()
#             and wm.ball().pos_count() <= 1
#             and wm.ball().vel_count() <= 1
#             and self_min < 20
#         ):
#             log.sw_log().team().add_text(
#                 f"(sample player do heard pass) intercepting!, self_min={self_min}"
#             )
#             log.debug_client().add_message("Comm:Receive:Intercept")
#             Intercept().execute(self)
#             self.set_neck_action(NeckTurnToBall())
#         else:
#             log.sw_log().team().add_text(
#                 f"(sample palyer do heard pass) go to point!, cycle={self_min}"
#             )
#             log.debug_client().set_target(heard_pos)
#             log.debug_client().add_message("Comm:Receive:GoTo")

#             GoToPoint(heard_pos, 0.5, ServerParam.i().max_dash_power()).execute(self)
#             self.set_neck_action(NeckTurnToBall())


# # TODO INTENTION?!?

import multiprocessing
class KeepawayPlayer(PlayerAgent):
    def __init__(self, team_name, shared_values, manager, lock, event,event_from_subprocess,main_process_event,world):
        # super().__init__()
        super().__init__(shared_values, manager, lock, event, team_name)
        self._communication = SampleCommunication()
        self._count_list = shared_values
        self._barrier = manager
        self._event_from_subprocess = event_from_subprocess
        self._main_process_event = main_process_event
        self._real_world = world
        self._full_world = world

        # TODO: check the use of full or real world.
        # self._full_world = world 
    
  
    def count(self):
        # Wait for all processes to be ready to start
        # print("count list", self._count_list)
        wm = self.world()
        self._barrier.wait()
        index = wm.self().unum()
        
        # Each process will increment its count in count_list by 1, 100 times
        for i in range(1, 101):
            with self._count_list.get_lock():
                self._count_list[index] = self._current_time.cycle()
                # print("count list", self._count_list)
            # print(list(self._count_list))


    def action_impl(self):
        wm = self.world()
        # if self.world().team_name_left() == "takers":
        # pass
        # print("team name: ", self.world().team_name())
        if self.do_preprocess():
            return

        # get_decision(self)
        # self.count()
        # print("world: ", self._real_world.time())
        get_decision_keepaway(self, self._count_list, self._barrier, self._event_from_subprocess, self._main_process_event)

    def do_preprocess(self):
        wm = self.world()

        # print("do_preprocess ball position: ", wm.ball().pos())

        if wm.self().is_frozen():
            self.set_view_action(ViewTactical())
            self.set_neck_action(NeckTurnToBallOrScan())
            return True

        if not wm.self().pos_valid():
            self.set_view_action(ViewTactical())
            ScanField().execute(self)
            return True

        count_thr = 10 if wm.self().goalie() else 5
        if wm.ball().pos_count() > count_thr or (
            wm.game_mode().type() is not GameModeType.PlayOn
            and wm.ball().seen_pos_count() > count_thr + 10
        ):
            self.set_view_action(ViewTactical())
            NeckBodyToBall().execute(self)
            return True

        self.set_view_action(ViewTactical())

        if self.do_heard_pass_receive():
            return True

        return False

    def do_heard_pass_receive(self):
        wm = self.world()

        if (
            wm.messenger_memory().pass_time() != wm.time()
            or len(wm.messenger_memory().pass_()) == 0
            or wm.messenger_memory().pass_()[0]._receiver != wm.self().unum()
        ):
            return False

        self_min = wm.intercept_table().self_reach_cycle()
        intercept_pos = wm.ball().inertia_point(self_min)
        heard_pos = wm.messenger_memory().pass_()[0]._pos

        log.sw_log().team().add_text(
            f"(sample palyer do heard pass) heard_pos={heard_pos}, intercept_pos={intercept_pos}"
        )

        if (
            not wm.kickable_teammate()
            and wm.ball().pos_count() <= 1
            and wm.ball().vel_count() <= 1
            and self_min < 20
        ):
            log.sw_log().team().add_text(
                f"(sample palyer do heard pass) intercepting!, self_min={self_min}"
            )
            log.debug_client().add_message("Comm:Receive:Intercept")
            Intercept().execute(self)
            self.set_neck_action(NeckTurnToBall())
        else:
            log.sw_log().team().add_text(
                f"(sample palyer do heard pass) go to point!, cycle={self_min}"
            )
            log.debug_client().set_target(heard_pos)
            log.debug_client().add_message("Comm:Receive:GoTo")

            GoToPoint(heard_pos, 0.5, ServerParam.i().max_dash_power()).execute(self)
            self.set_neck_action(NeckTurnToBall())

        # TODO INTENTION?!?
