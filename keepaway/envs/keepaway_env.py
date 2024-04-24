import os
import akro
import atexit
import copy
import yaml
import time
import torch
from tqdm import tqdm
import numpy as np
from absl import logging
import multiprocessing
from subprocess import Popen
import keepaway.utils.main_keepaway_player as kp
from keepaway.lib.player.world_model import WorldModel
from keepaway.envs.multiagentenv import MultiAgentEnv
from keepaway.envs.spaces import MultiAgentActionSpace, MultiAgentObservationSpace


config_dir = os.getcwd() + "/config"


class KeepawayEnv(MultiAgentEnv):
    """
        robocup2d keepaway environment for multi-agent reinforcement learning scenarios version 0.1.0.
    """

    def __init__(self, **kwargs):
        """
        Initialize a keep-away environment.

        Parameters obtained from kwargs:
        - num_keepers: Number of keepers in the environment.
        - num_takers: Number of takers in the environment.
        - pitch_size: Size of the pitch (field).
        - sparse_reward: Whether to use sparse rewards.
        - time: Time module to use for sleep.
        - config_dir: Directory containing the configuration files.
        - num_agents: Number of agents in the environment.
        - actions: Number of actions an agent can take.
        - _episode_count_: Number of episodes.
        - _episode_steps_: Number of steps in an episode.
        - _total_steps_: Total number of steps.
        - force_restarts: Number of forced restarts.
        - episode_limit: Maximum number of episodes.
        - _event: Event to synchronize the agents.
        - _world: World model for the environment.
        - _lock: Lock for the world model.
        - _barrier: Barrier for the agents.
        - _episode_count: Episode count for the world model.
        - _episode_steps: Episode steps for the world model.
        - _total_steps: Total steps for the world model.
        - _event_from_subprocess: Event from the subprocess.
        - _main_process_event: Event for the main process.
        - _actions: Actions for the agents.
        - _shared_actions: Shared actions for the agents.
        - _obs: Observations for the agents.
        - last_action_time: Last action time.
        - _last_action_time: Last action time for the world model.
        - _proximity_adj_mat: Proximity adjacency matrix.
        - _reward: Reward for the world model.
        - _terminated: Termination signal for the world model.
        - _episode_reward: Episode reward.
        - _proximity_threshold: Proximity threshold.
        - renderer: Renderer for the environment.
        - _run_flag: Flag to run the environment.

        """
        super().__init__()

        ## Default game configuration.

        default_num_keepers = 3
        default_num_takers = 2
        default_pitch_size = 20

        self.num_keepers = kwargs.get("num_keepers", default_num_keepers)
        self.num_takers = kwargs.get("num_takers", default_num_takers)
        self.pitch_size = kwargs.get("pitch_size", default_pitch_size)
        self.sparse_reward = kwargs.get("sparse_reward", default_pitch_size)
        self.actions = self.num_keepers  # 0: hold, 1: pass

        self._episode_count_ = 0
        self._episode_steps_ = 0
        self._total_steps_ = 0
        self.force_restarts = 0
        self.episode_limit = 10000

        self.num_agents = self.num_keepers + self.num_takers

        ## Set up shared variables
        manager = multiprocessing.Manager()
        self._event = multiprocessing.Event()
        self._world = WorldModel("real", self.num_keepers, manager)  # for all agents
        self._lock = self._world
        self._barrier = multiprocessing.Barrier(self.num_keepers)
        self._episode_count = self._world._episode_count
        self._episode_steps = self._world._episode_steps
        self._total_steps = self._world._total_steps
        self._event_from_subprocess = multiprocessing.Event()
        self._main_process_event = (
            multiprocessing.Event()
        )  # To be set by main process to wake up all subprocesses

        self._actions = [0] * self.num_keepers
        self._shared_actions = multiprocessing.Array("i", self._actions)

        self._obs = self._world._obs
        self.last_action_time = 0
        self._last_action_time = multiprocessing.Value("i", self.last_action_time)
        self._proximity_adj_mat = self._world._adjacency_matrix

        ## shared reward
        self._reward = self._world._reward

        ## Episode termination
        self._terminated = self._world._terminated

        self._episode_reward = []
        self._proximity_threshold = 2

        self.renderer = None
        self._run_flag = False

        self._action_time = self._world._action_time
        self._action_time_counter = self._world._action_time_counter

        ## TODO:  This should in in a wrapper class
        self.action_spaces = [akro.Discrete(3) for _ in range(self.num_keepers)]
        self.action_spaces = MultiAgentActionSpace(self.action_spaces)
        self.action_space = self.action_spaces[0]
        self.centralized = True

        self.alive_mask = np.array([True] * self.num_keepers)
        self.threshold = 2
        self.self_connected_adj = False
        self.inv_D = False
        self.pickleable = True

        # Initialize Keepers and Takers
        self._keepers = [
            multiprocessing.Process(
                target=kp.main,
                args=(
                    "keepers",
                    i,
                    False,
                    self._shared_actions,
                    self._barrier,
                    self._lock,
                    self._event,
                    self._event_from_subprocess,
                    self._main_process_event,
                    self._world,
                    self._obs,
                    self._last_action_time,
                    self._reward,
                    self._terminated,
                    self._proximity_adj_mat,
                    self._proximity_threshold,
                    self._episode_count,
                    self._episode_steps,
                    self._total_steps,
                ),
                name="keeper",
            )
            for i in range(self.num_keepers)
        ]

        self._takers = [
            multiprocessing.Process(
                target=kp.main,
                args=(
                    "takers",
                    i,
                    False,
                    self._shared_actions,
                    self._barrier,
                    self._lock,
                    self._event,
                    self._event_from_subprocess,
                    self._main_process_event,
                    self._world,
                    self._obs,
                    self._last_action_time,
                    self._reward,
                    self._terminated,
                    self._proximity_adj_mat,
                    self._proximity_threshold,
                    self._episode_count,
                    self._episode_steps,
                    self._total_steps,
                ),
                name="takers",
            )
            for i in range(self.num_takers)
        ]

        # Initialize the coach, uncomment to use
        # self._coach = [multiprocessing.Process(target=main_c.main)]
        # coach = mp.Process(target=main_c.main)

        self._server = []
        self._render = []
        self._sleep = time

    def _is_game_started(self) -> bool:
        """
        Check if the game has started.

        returns: bool
        """
        if self._world.game_mode().type() == "play_on":
            return True
        return False

    def _agents(self):
        """
        Utility to return all agents in the environment.

        returns: list
        """
        return self._keepers + self._takers

    def _launch_monitor(self) -> int:
        """Launches the soccer window."""

        logging.debug("Built the command to connect to the server")

        monitor_cmd = f"soccerwindow2 &"
        popen = Popen(monitor_cmd, shell=True)

        return popen

    def load_agent_config(self, file_path) -> dict:
        """
        Load the agent configuration from the given file path.
        """

        with open(file_path) as f:
            return yaml.safe_load(f)

    def _parse_options(self, args=None, **defaults):
        """
        Parses the given list of args, defaulting to sys.argv[1:].
        Retrieve other options from the YAML config file.
        """

        # Load the default values from YAML file
        with open(f"{config_dir}/server-config.yml", "r") as ymlfile:
            config = yaml.safe_load(ymlfile)

        class ConfigOptions:
            pass

        options = ConfigOptions()
        # options, _ = parser.parse_args(args)
        # Merging command-line options with YAML defaults
        for key, value in config.items():
            if not getattr(options, key, None):
                setattr(options, key, value)
        return options

    def _launch_server(self, options):
        """Launch the RCSS Server and Monitor"""

        log_name = f"{time.strftime('%Y%m%d%H%M%S')}"

        server_options = [
            f"server::{opt}={val}"
            for opt, val in {
                "coach": int(options.coach),
                "coach_port": int(options.coach_port),
                "forbid_kick_off_offside": 1,
                "half_time": -1,
                "keepaway": int(not options.coach),
                "keepaway_start": options.game_start,
                "keepaway_length": int(options.field_length),
                "keepaway_width": int(options.field_width),
                "keepaway_logging": 1 if options.log_keepaway else 0,
                "keepaway_log_dir": options.log_dir if options.log_keepaway else None,
                "keepaway_log_fixed": 1 if options.log_keepaway else 0,
                "keepaway_log_fixed_name": log_name if options.log_keepaway else None,
                "game_log_compression": 0,
                "game_log_dir": options.game_log_dir if options.log_game else None,
                "game_log_fixed": 1 if options.log_game else 0,
                "game_log_fixed_name": log_name if options.log_game else None,
                "game_log_version": 5 if options.log_game else 0,
                "game_logging": 1,
                "olcoach_port": options.online_coach_port,
                "port": options.port,
                "stamina_inc_max": 3500,
                "fullstate_l": int(options.fullstate),
                "fullstate_r": int(options.fullstate),
                "synch_mode": int(options.synch_mode),
                "synch_offset": 60,
                "synch_see_offset": 0,
                "text_log_compression": 0,
                "text_log_dir": options.game_log_dir if options.log_text else None,
                "text_log_fixed": 1 if options.log_text else 0,
                "text_log_fixed_name": log_name if options.log_text else None,
                "text_logging": 1,
                "use_offside": 0,
                "visible_angle": 360 if not options.restricted_vision else None,
            }.items()
            if val is not None
        ]

        # Build rcssserver command, and fork it off.
        # print(server_options)
        command = ["rcssserver"] + server_options
        popen = Popen(command)

        return popen

    def _launch_game(self):
        """Launch a keepaway game instance."""
        # print("launching game")
        options = self._parse_options()
        # print(options.)
        # args, other_args = parser.parse_known_args()
        self._server.append(self._launch_server(options))

    def reset(
        self,
    ):
        """Reset the environment. Required after each full episode."""

        # print("resetting")
        self._episode_steps_ = 0
        self._total_steps_ = 0

        if self._episode_steps.get_lock():
            self._episode_steps.value = 0

        if self._total_steps.get_lock():
            self._total_steps.value = 0

        self.last_action = None
        self._episode_reward = []
        self.info = {}
        if self._world._terminated.get_lock():
            self._world._terminated.value = False

        return (self._obs,)

    def reward(self):
        """
        returns the reward for the current state
        """
        r = self._world.time().cycle() - self._terminal_time.cycle()
        return r

    def _check_agents(self):
        """
        Check if all agents process are running.
        """
        for p in self._keepers:
            if not p.is_alive():
                return False
        for p in self._takers:
            if not p.is_alive():
                return False
        return True

    def _restart(self):
        self.full_restart()

    def full_restart(self):
        """Restart the environment. Required after each full episode."""
        # TODO process management utility
        self._launch_game()
        self.force_restarts += 1

    def start(self):
        if self._episode_count_ == 0:
            for i in range(self.num_keepers):
                self._keepers[i].start()

            self._sleep.sleep(0.5)

            for i in range(self.num_takers):
                self._takers[i].start()

            self._sleep.sleep(2.0)
            # print("starting coach")
            # self._coach[0].start()

            atexit.register(self.close)
            self._episode_count_ += 1
        else:
            pass

    def close(self):
        """Close the environment. No other method calls possible afterwards."""

        for p in self._keepers:
            p.terminate()

        for s in self._server:
            s.terminate()

        for t in self._takers:
            t.terminate()

        for r in self._render:
            r.terminate()
            self.renderer = None

        # self._coach[0].terminate()

    def render(self, mode="human"):
        """Render the environment using the monitor."""
        self._render.append(self._launch_monitor())
        self.renderer = mode

    def get_avail_actions(self):
        """Returns the available actions for agent_id."""
        avail_actions = [[1] * self.action_space.n for _ in range(self.num_keepers)]
        if not self.centralized:
            return avail_actions
        else:
            return np.concatenate(avail_actions)

    def get_total_actions(self):
        pass

    def get_obs(self):
        # obs = np.frombuffer(self._obs, dtype=np.float64)
        # print("obs ", self._obs) .
        return self._obs

    def get_obs_agent(self, agent_id):
        """Returns the observation for agent_id."""
        return self._obs[agent_id]

    def get_total_actions(self):
        """Returns the total number of actions an agent could ever take."""
        return self.actions

    def get_obs_size(self):
        """Returns the shape of the observation."""
        # print("length ", len(self._obs.values()[0]))
        return len(self._obs.values()[0])

    def get_state_size(self):
        """Returns the shape of the state."""
        # print("obs size us ", self.get_obs_size() * self.num_agents)
        # print("numbr of keepers ", self.num_keepers)
        return self.get_obs_size() * self.num_keepers

    ## TODO: Should be a wrapper method.
    def get_proximity_adj_mat(self, raw, con_adj, inv_d):
        adjacent_matrix = np.frombuffer(self._proximity_adj_mat, dtype=np.float64)

        adj = copy.deepcopy(adjacent_matrix)
        adj = adj.reshape(self.num_keepers, self.num_keepers)

        ## calculate the renormalized adjacency matrix

        adj_raw = copy.deepcopy(adj)

        if raw:
            return adj_raw

        if not inv_d:
            adj = (adj + np.eye(self.num_keepers)) if con_adj else adj
            sqrt_D = np.diag(np.sqrt(np.sum(adj, axis=1)))
            adj_renormalized = sqrt_D @ adj @ sqrt_D
        else:
            adj = adj + np.eye(self.num_keepers)
            inv_sqrt_D = np.diag(np.sum(adj, axis=1) ** (-0.5))
            adj_renormalized = inv_sqrt_D @ adj @ inv_sqrt_D

            return adj_renormalized

    def get_state(self):
        """Returns the global state."""

        ## TODO: verify state variables to be for all agents or just one
        ## check for dec execution/
        ## partial observation or state variables
        # print("obs ," ,self.get_obs())
        obs = self.get_obs().values()
        obs = [
            item if isinstance(item, np.ndarray) else item["state_vars"] for item in obs
        ]
        obs_concat = np.concatenate(obs, axis=0)
        return obs_concat

    def _step(self, actions):
        """
        A single environment step. Returns reward, terminated, info.

        Args:
            actions: list of actions for each agent

        Returns:
            Tuple of time-step data for each agent

        """

        if isinstance(actions, torch.Tensor):
            actions = actions.cpu().tolist()

        if actions is None or len(actions) != self.num_keepers:
            self.agents = []
            return {}, {}, {}, {}

        actions_int = actions

        # if self._total_steps.get_lock():
        #     self._total_steps.value += 1

        # if self._episode_steps.get_lock():
        #     self._episode_steps.value += 1

        total_reward = 0
        i = {}
        # terminated = False
        self._actions = copy.deepcopy(actions_int)
        self._shared_values = multiprocessing.Array("i", self._actions)
        self._observation = self._world._obs

        t = self._world._terminated.value
        r = self._reward.value

        # if game_state == 1:
        #     terminated = True
        #     if not self.sparse_reward:
        #         total_reward = self._reward.value
        #         pass
        #     else:
        #         total_reward = self._reward.value

        #     self._terminal_time = self._world.time()

        if t == 1:
            self._episode_count.value += 1

        return self._reward.value, self._world._terminated.value, i

    def step(self, actions):
        """A single environment step. Returns reward, terminated, info.

        Args:
            actions: list of actions for each agent

        Returns:
            Tuple of time-step data for each agent


        applies all actions to the
        send an action signal and return observation.
        """

        if isinstance(actions, torch.Tensor):
            actions = actions.cpu().tolist()

        if actions is None or len(actions) != self.num_keepers:
            self.agents = []
            return {}, {}, {}, {}

        actions_int = actions
        self._total_steps_ += 1
        self._episode_steps_ += 1
        total_reward = 0
        info = {}
        terminated = False
        self._actions = copy.deepcopy(actions_int)
        self._shared_values = multiprocessing.Array("i", self._actions)
        self._observation = self._world._obs
        game_state = self._world._terminated.value
        if game_state == 1:
            terminated = True
            if not self.sparse_reward:
                total_reward = self._reward.value
                pass
            else:
                total_reward = self._reward.value

            self._terminal_time = self._world.time()
        if terminated:
            self._episode_count_ += 1
            self._episode_count.value = 2

            ## check if all agents are running
            # if not self._check_agents():
            #     print("restarting")
            #     # self.close()
            #     self._restart()
            #     self.start()
        # print("total reward ", total_reward, "terminated ", terminated, "info ", info)
        return total_reward, terminated, info

    def convert_to_numpy(self, proxy):
        if isinstance(proxy, dict):
            regular_dict = dict
        else:
            regular_dict = dict(proxy)
        values = [
            item if isinstance(item, np.ndarray) else item["state_vars"]
            for item in regular_dict.values()
        ]
        numpy_array = np.stack(values, axis=0)
        return numpy_array

    ## TODO: Should be a wrapper method.

    def eval(
        self,
        epoch,
        policy,
        max_episode_steps,
        n_eval_episodes=10,
        greedy=True,
        visualize=False,
        log=None,
        tbx=None,
        tabular=None,
    ):
        eval_avg_return = 0
        eval_env_steps = 0
        # self.env._launch_game()
        # self.env.render()
        with torch.no_grad(), tqdm(total=n_eval_episodes) as progress_bar:
            for i_ep in range(n_eval_episodes):
                # Start episode
                obses = self.env.reset()  # (n_agents, obs_dim)
                ob = obses[0]
                # print("ob ", ob)
                obs_ = self.convert_to_numpy(ob)
                # env.start()

                for t in range(max_episode_steps):
                    if policy.proximity_adj:
                        adjs = self.get_proximity_adj_mat()
                        alive_masks = None
                    else:
                        adjs = None
                        alive_masks = np.array(self.alive_mask)
                    avail_actions = self.env.get_avail_actions()
                    actions, agent_infos_n = policy.get_actions(
                        obs_,
                        avail_actions,
                        adjs=adjs,
                        alive_masks=alive_masks,
                        greedy=greedy,
                    )

                    rewards, done, info = self.env.step(actions)

                    eval_avg_return += np.mean(rewards)
                    if done:
                        eval_env_steps += t + 1
                        break
                    # obses = next_obses
                    # obses = self.convert_to_numpy(obses[0])
                # end episode
                progress_bar.set_postfix(
                    metric="{:.2f}".format(eval_avg_return / (i_ep + 1))
                )
                progress_bar.update(1)
            # end eval

        eval_avg_return /= n_eval_episodes
        eval_env_steps /= n_eval_episodes

        log_strs = [
            "avg_return         {:.2f}".format(eval_avg_return),
            "avg_episode_steps  {}".format(eval_env_steps),
        ]

        tbx_results = {
            "avg_return": eval_avg_return,
            "avg_episode_steps": eval_env_steps,
        }

        # Logging...
        log.info("Eval" + "-" * 36)
        for item in log_strs:
            log.info(item)
        log.info("-" * 40)

        for k, v in tbx_results.items():
            if k[0] != ":":
                tbx.add_scalar(f"eval/{k}", v, epoch)
            else:
                tbx.add_histogram(f"eval/{k[1:]}", v, epoch)

        tabular.record(self.metric_name, eval_env_steps)

        return eval_avg_return  # saver metric
