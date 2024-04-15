from keepaway.utils.decision import get_decision_keepaway
from keepaway.base.sample_communication import SampleCommunication
from keepaway.base.view_tactical import ViewTactical
from keepaway.lib.action.go_to_point import GoToPoint
from keepaway.lib.action.neck_body_to_ball import NeckBodyToBall
from keepaway.lib.action.neck_turn_to_ball import NeckTurnToBall
from keepaway.lib.action.neck_turn_to_ball_or_scan import NeckTurnToBallOrScan
from keepaway.utils.keepaway_actions import ScanField
from keepaway.lib.debug.debug import log
from keepaway.lib.debug.level import Level
from keepaway.utils.keepaway_agent import PlayerAgent
from keepaway.lib.rcsc.server_param import ServerParam
from keepaway.lib.rcsc.types import GameModeType

from keepaway.lib.debug.debug import log


class KeepawayPlayer(PlayerAgent):
    def __init__(
        self,
        team_name,
        shared_values,
        manager,
        lock,
        event,
        event_from_subprocess,
        main_process_event,
        world,
        obs,
        last_action_time,
        reward,
        terminated,
        proximity_adj_mat,
        proximity_threshold,
        episode_count,
        episode_step,
        total_steps,
    ):
        super().__init__(
            shared_values, manager, lock, event, world, reward, terminated, team_name
        )
        self._communication = SampleCommunication()
        self._count_list = shared_values  # actions
        self._barrier = manager  #
        self._event_from_subprocess = event_from_subprocess  #
        self._main_process_event = main_process_event
        self._real_world = world
        self._full_world = world
        self._obs = obs
        self._last_action_time = last_action_time
        self._reward = reward
        self._terminated = terminated
        self._adj_matrix = proximity_adj_mat
        self._proximity_threshold = proximity_threshold
        self._episode_count = episode_count
        
        self._episode_step = episode_step
        self._total_steps = total_steps

        # TODO: check the use of full or real world.
        # self._full_world = world


    def action_impl(self):
        wm = self.world()
        
        ## Update the total steps
        if self._total_steps.get_lock():
            self._total_steps.value = wm.time().cycle()

        if self.do_preprocess():
            return

        get_decision_keepaway(
            self,
            self._count_list,
            self._barrier,
            self._event_from_subprocess,
            self._main_process_event,
            self._obs,
            self._last_action_time,
            self._reward,
            self._terminated,
            self._full_world,
            self._adj_matrix,
        )

    def do_preprocess(self):
        wm = self.world()

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

        print(
            "(sample player do heard pass) heard_pos={heard_pos}, intercept_pos={intercept_pos}".format(
                heard_pos=heard_pos, intercept_pos=intercept_pos
            )
        )

        log.sw_log().team().add_text(
            f"(sample player do heard pass) heard_pos={heard_pos}, intercept_pos={intercept_pos}"
        )

        if (
            not wm.kickable_teammate()
            and wm.ball().pos_count() <= 1
            and wm.ball().vel_count() <= 1
            and self_min < 20
        ):
            log.sw_log().team().add_text(
                f"(sample player do heard pass) intercepting!, self_min={self_min}"
            )
            log.debug_client().add_message("Comm:Receive:Intercept")
            GoToPoint(heard_pos, 0.5, ServerParam.i().max_dash_power()).execute(self)
            return True
        else:
            log.sw_log().team().add_text(
                f"(sample player do heard pass) go to point!, cycle={self_min}"
            )
            log.debug_client().set_target(heard_pos)
            log.debug_client().add_message("Comm:Receive:GoTo")

            GoToPoint(heard_pos, 0.5, ServerParam.i().max_dash_power()).execute(self)
            self.set_neck_action(NeckTurnToBall())
            return True
