import os
import datetime
import pprint
import time
import threading
import copy
import torch as th
import numpy as np
import yaml
from types import SimpleNamespace as SN
from keepaway.dcg.utils.logging import Logger
from keepaway.dcg.utils.timehelper import time_left, time_str
from os.path import dirname, abspath
from keepaway.dcg.components.episode_buffer import ReplayBuffer
from keepaway.dcg.components.transforms import OneHot
from collections.abc import Mapping
from keepaway.dcg.learner.q_learner import QLearner
from keepaway.dcg.learner.dcg_learner import DCGLearner
from keepaway.dcg.runners.episode_runner import EpisodeRunner
from keepaway.envs.keepaway_env import KeepawayEnv
from keepaway.config.game_config import get_config
from keepaway.dcg.controller.dcg_controller import DeepCoordinationGraphMAC
from keepaway.dcg.utils.logging import get_logger
logger = get_logger()
results_path = os.path.join(dirname(dirname(abspath(__file__))), "results")


def evaluate_sequential(args, runner):
    for _ in range(args.test_nepisode):
        runner.run(test_mode=True)
    # if args.save_replay:
    #     runner.save_replay()
    # runner.close_env()


def run_sequential(args, logger):
    runner = EpisodeRunner(args, logger)
    scheme = {
        "state": {"vshape": env_info["state_shape"]},
        "obs": {"vshape": env_info["obs_shape"], "group": "agents"},
        "actions": {"vshape": (1,), "group": "agents", "dtype": th.long},
        "avail_actions": {
            "vshape": (env_info["n_actions"],),
            "group": "agents",
            "dtype": th.int,
        },
        "reward": {"vshape": (1,)},
        "terminated": {"vshape": (1,), "dtype": th.uint8},
    }

    groups = {"agents": args.n_agents}
    preprocess = {"actions": ("actions_onehot", [OneHot(out_dim=args.n_actions)])}

    buffer = ReplayBuffer(
        scheme,
        groups,
        args.buffer_size,
        env_info["episode_limit"] + 1,
        preprocess=preprocess,
        device="cpu" if args.buffer_cpu_only else args.device,
    )

    mac = DeepCoordinationGraphMAC(scheme, groups, args)

    # Give runner the scheme
    runner.setup(scheme=scheme, groups=groups, preprocess=preprocess, mac=mac)

    # Learner
    learner = DCGLearner(mac, buffer.scheme, logger, args)

    if args.use_cuda:
        learner.cuda()

    if args.checkpoint_path != "":
        timesteps = []
        timestep_to_load = 0

        if not os.path.isdir(args.checkpoint_path):
            logger.console_logger.info(
                "Checkpoint directory {} doesn't exist".format(args.checkpoint_path)
            )
            return

        for name in os.listdir(args.checkpoint_path):
            full_name = os.path.join(args.checkpoint_path, name)
            # Check if they are dirs the names of which are numbers
            if os.path.isdir(full_name) and name.isdigit():
                timesteps.append(int(name))

        if args.load_step == 0:
            # choose the max timestep
            timestep_to_load = max(timesteps)
        else:
            # choose the timestep closest to load_step
            timestep_to_load = min(timesteps, key=lambda x: abs(x - args.load_step))

        model_path = os.path.join(args.checkpoint_path, str(timestep_to_load))
        logger.console_logger.info("Loading model from {}".format(model_path))
        learner.load_models(model_path)
        runner.t_env = timestep_to_load
        if args.evaluate or args.save_replay:
            evaluate_sequential(args, runner)
            return

    episode = 0
    last_test_T = -args.test_interval - 1
    last_log_T = 0
    model_save_time = 0

    start_time = time.time()
    last_time = start_time

    logger.console_logger.info("Beginning training for {} timesteps".format(args.t_max))

    while runner.t_env <= args.t_max:
        episode_batch = runner.run(test_mode=False)
        buffer.insert_episode_batch(episode_batch)

        if buffer.can_sample(args.batch_size):
            episode_sample = buffer.sample(args.batch_size)
            # Truncate batch to only filled timesteps
            max_ep_t = episode_sample.max_t_filled()
            episode_sample = episode_sample[:, :max_ep_t]

            if episode_sample.device != args.device:
                episode_sample.to(args.device)

            print("episode sample ", episode_sample)
            learner.train(episode_sample, runner.t_env, episode)
            n_test_runs = max(1, args.test_nepisode // runner.batch_size)
            if (runner.t_env - last_test_T) / args.test_interval >= 1.0:
                logger.console_logger.info(
                    "t_env: {} / {}".format(runner.t_env, args.t_max)
                )
                logger.console_logger.info(
                    "Estimated time left: {}. Time passed: {}".format(
                        time_left(last_time, last_test_T, runner.t_env, args.t_max),
                        time_str(time.time() - start_time),
                    )
                )
                last_time = time.time()
                last_test_T = runner.t_env

                for _ in range(n_test_runs):
                    runner.run(test_mode=True)

            if args.save_model and (
                runner.t_env - model_save_time >= args.save_model_interval
                or model_save_time == 0
            ):
                model_save_time = runner.t_env
                save_path = os.path.join(
                    args.local_results_path,
                    "models",
                    args.unique_token,
                    str(runner.t_env),
                )
                os.makedirs(save_path, exist_ok=True)
                logger.console_logger.info("Saving models to {}".format(save_path))

                # learner should handle saving/loading -- delegate actor save/load to mac,
                # use appropriate filenames to do critics, optimizer states
                learner.save_models(save_path)

            episode += args.batch_size_run
            if (runner.t_env - last_log_T) >= args.log_interval:
                logger.log_stat("episode", episode, runner.t_env)
                logger.print_recent_stats()
                last_log_T = runner.t_env

    print("runner t_env ", runner.t_env)
    runner.close_env()
    logger.console_logger.info("Finished Training")


def args_sanity_check(config, _log):
    # set CUDA flags
    # config["use_cuda"] = True # Use cuda whenever possible!
    # print(config["use_cuda"])

    if config.use_cuda and not th.cuda.is_available():
        config.use_cuda = False
        _log.warning(
            "CUDA flag use_cuda was switched OFF automatically because no CUDA devices are available!"
        )

    if config.test_nepisode < config.batch_size_run:
        config.test_nepisode = config.batch_size_run
    else:
        config.test_nepisode = (
            config.test_nepisode // config.batch_size_run
        ) * config.batch_size_run

    return config


def _get_config(params, arg_name, subfolder):
    config_name = None
    for _i, _v in enumerate(params):
        if _v.split("=")[0] == arg_name:
            config_name = _v.split("=")[1]
            del params[_i]
            break

    if config_name is not None:
        current_working_dir = os.getcwd()
        config_path = os.path.join(
            current_working_dir, "config", "{}.yaml".format(config_name)
        )
        with open(config_path, "r") as f:
            try:
                config_dict = yaml.safe_load(f)
            except yaml.YAMLError as exc:
                assert False, "{}.yaml error: {}".format(config_name, exc)
        return config_dict


def recursive_dict_update(d, u):
    for k, v in u.items():
        if isinstance(v, Mapping):
            d[k] = recursive_dict_update(d.get(k, {}), v)
        else:
            d[k] = v
    return d


def config_copy(config):
    if isinstance(config, dict):
        return {k: config_copy(v) for k, v in config.items()}
    elif isinstance(config, list):
        return [config_copy(v) for v in config]
    else:
        return copy.deepcopy(config)


def run(_config, _log):
    args = SN(**_config)
    args = args_sanity_check(args, _log)
    args.device = th.device(
        "cuda" if th.cuda.is_available() and args.use_cuda else "cpu"
    )
    logger = Logger(_log)

    ####
    unique_token = "{}__{}".format(
        args.name, datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    )
    args.unique_token = unique_token
    if args.use_tensorboard:
        tb_logs_direc = os.path.join(
            dirname(dirname(abspath(__file__))), "results", "tb_logs"
        )
        tb_exp_direc = os.path.join(tb_logs_direc, "{}").format(unique_token)
        logger.setup_tb(tb_exp_direc)

    # print("args run sequential ")
    print(args.env)
    run_sequential(args=args, logger=logger)


if __name__ == "__main__":
    # Load the configuration
    params = ["--config=dcg"]

    parent_dir = os.getcwd()
    config_file_path = os.path.join(parent_dir, "config", "default.yaml")
    # print(config_file_path)
    with open(config_file_path, "r") as f:
        try:
            config_dict = yaml.safe_load(f)
        except yaml.YAMLError as exc:
            assert False, "default.yaml error: {}".format(exc)

    # Load algorithm and env base configs
    alg_config = _get_config(params, "--config", "algs")
    config_dict = recursive_dict_update(config_dict, alg_config)

    config = get_config()["4v3"]
    config = config | config_dict
    config["log_level"] = "INFO"
    config["name"] = "keepaway"
    config["n_agents"] = config["num_keepers"]
    # config["n_agents"] = config["num_keepers"] + config["num_takers"]
    config["n_actions"] = config["num_keepers"]

    # Set the random seed
    # Set the device
    device = th.device("cuda" if th.cuda.is_available() else "cpu")
    # Set the unique token
    unique_token = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    # # Set the local results path
    local_results_path = os.path.join(dirname(abspath(__file__)), "results")
    # # Set the global results path
    global_results_path = os.path.join(dirname(abspath(__file__)), "..", "results")
    # # Set the checkpoint path
    checkpoint_path = os.path.join(local_results_path, "models", unique_token)
    # # print(checkpoint_path)
    # os.makedirs(checkpoint_path, exist_ok=True)
    # Set the load step
    load_step = 0
    # Set the evaluate flag
    evaluate = False
    # Set the save replay flag
    save_replay = False
    # Set the buffer CPU only flag
    buffer_cpu_only = False
    # Set the use CUDA flag
    use_cuda = True
    # Set the logger
    # logger = Logger(config["log_level"])
    # Set the environment
    env = KeepawayEnv(**config)
    # # Get the environment information
    env_info = {
        "state_shape": env.get_state_size(),
        "obs_shape": env.get_obs_size(),
        "n_actions": env.get_total_actions(),
        "episode_limit": env.episode_limit,
    }
    print(env_info)
    run(config, logger)
