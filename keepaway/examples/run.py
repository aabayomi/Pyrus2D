
import os
import datetime
import pprint
import time
import threading
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


def run(_run, _config, _log):

    # check args sanity
    _config = args_sanity_check(_config, _log)

    args = SN(**_config)
    args.device = "cuda" if args.use_cuda else "cpu"

    # setup loggers
    logger = Logger(_log)

    _log.info("Experiment Parameters:")
    experiment_params = pprint.pformat(_config,
                                       indent=4,
                                       width=1)
    _log.info("\n\n" + experiment_params + "\n")

    # configure tensorboard logger
    unique_token = "{}__{}".format(args.name, datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))
    args.unique_token = unique_token
    if args.use_tensorboard:
        tb_logs_direc = os.path.join(dirname(dirname(abspath(__file__))), "results", "tb_logs")
        tb_exp_direc = os.path.join(tb_logs_direc, "{}").format(unique_token)
        logger.setup_tb(tb_exp_direc)

    # sacred is on by default
    logger.setup_sacred(_run)

    # Run and train
    run_sequential(args=args, logger=logger)

    # Clean up after finishing
    print("Exiting Main")

    print("Stopping all threads")
    for t in threading.enumerate():
        if t.name != "MainThread":
            print("Thread {} is alive! Is daemon: {}".format(t.name, t.daemon))
            t.join(timeout=1)
            print("Thread joined")

    print("Exiting script")

    # Making sure framework really exits
    os._exit(os.EX_OK)




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
        "avail_actions": {"vshape": (env_info["n_actions"],), "group": "agents", "dtype": th.int},
        "reward": {"vshape": (1,)},
        "terminated": {"vshape": (1,), "dtype": th.uint8},
    }

    groups = {
        "agents": args.n_agents
    }
    preprocess = {
        "actions": ("actions_onehot", [OneHot(out_dim=args.n_actions)])
    }

    buffer = ReplayBuffer(scheme, groups, args.buffer_size, env_info["episode_limit"] + 1,
                          preprocess=preprocess,
                          device="cpu" if args.buffer_cpu_only else args.device)
    

    mac = DeepCoordinationGraphMAC(scheme, groups, args)

    runner.setup(scheme=scheme, groups=groups, preprocess=preprocess, mac=mac)

    # Learner
    # learner = le_REGISTRY[args.learner](mac, buffer.scheme, logger, args)
    learner = DCGLearner(mac, buffer.scheme, logger, args)
    
    if args.use_cuda:
        learner.cuda()

    if args.checkpoint_path != "":

        timesteps = []
        timestep_to_load = 0

        if not os.path.isdir(args.checkpoint_path):
            logger.console_logger.info("Checkpoint directory {} doesn't exist".format(args.checkpoint_path))
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
    last_test_T = -test_interval - 1
    last_log_T = 0
    model_save_time = 0

    start_time = time.time()
    last_time = start_time

    logger.console_logger.info("Beginning training for {} timesteps".format(args.t_max))
    

    while runner.t_env <= t_max:
        episode_batch = runner.run(test_mode=False)
        buffer.insert_episode_batch(episode_batch)
        if buffer.can_sample(batch_size):
            episode_sample = buffer.sample(batch_size)
            max_ep_t = episode_sample.max_t_filled()
            episode_sample = episode_sample[:, :max_ep_t]
            if episode_sample.device != args.device:
                episode_sample.to(args.device)

            learner.train(episode_sample, runner.t_env, episode)
            n_test_runs = max(1, test_nepisode // runner.batch_size)
            if (runner.t_env - last_test_T) / args.test_interval >= 1.0:

                logger.console_logger.info("t_env: {} / {}".format(runner.t_env, args.t_max))
                logger.console_logger.info("Estimated time left: {}. Time passed: {}".format( time_left(last_time, last_test_T, runner.t_env, args.t_max), time_str(time.time() - start_time)))
                last_time = time.time()
                last_test_T = runner.t_env

                for _ in range(n_test_runs):
                    runner.run(test_mode=True)
            
            if save_model and (runner.t_env - model_save_time >= save_model_interval or model_save_time == 0):
                print("saving model")
                model_save_time = runner.t_env
                save_path = os.path.join(args.local_results_path, "models", args.unique_token, str(runner.t_env))
                #"results/models/{}".format(unique_token)
                os.makedirs(save_path, exist_ok=True)
                logger.console_logger.info("Saving models to {}".format(save_path))

                # learner should handle saving/loading -- delegate actor save/load to mac,
                # use appropriate filenames to do critics, optimizer states
                learner.save_models(save_path)

            episode += batch_size_run
            if (runner.t_env - last_log_T) >= log_interval:
                logger.log_stat("episode", episode, runner.t_env)
                logger.print_recent_stats()
                last_log_T = runner.t_env
    runner.close_env()
    logger.console_logger.info("Finished Training")
 