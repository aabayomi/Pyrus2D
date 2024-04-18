import os
import time
import torch
from tqdm import tqdm
import copy
import numpy as np
import random
from json import dumps
from tensorboardX import SummaryWriter
import dowel
from dowel import logger, tabular
# from keepaway.garage.envs import GarageEnv

from keepaway.dicg.torch.algos import CentralizedMAPPO2
from keepaway.dicg.torch.baselines import CentValueFunction
from keepaway.dicg.sampler import CentralizedMAOnPolicySampler
from keepaway.config.game_config import get_config
import keepaway.dicg.util as util


import yaml 
import time
from types import SimpleNamespace as SN
import torch
from os.path import dirname, abspath
from keepaway.envs.keepaway_env import KeepawayEnv
from keepaway.envs.keepaway_wrapper import keepaway_env
from keepaway.dicg.torch.policies.dicg_ce_categorical_lstm_policy import DICGCECategoricalLSTMPolicy
# from dicg.experiment.local_runner_wrapper import LocalRunnerWrapper
from keepaway.dicg.sampler import CentralizedMAOnPolicyVectorizedSampler
from keepaway.dicg.torch.policies.dicg_ce_categorical_mlp_policy2 import DICGCECategoricalMLPPolicy2


results_path = os.path.join(dirname(dirname(abspath(__file__))), "dicg-results")

def train(args):
    if not args.enforce_cpu:
        device = util.get_available_devices()
    else:
        device = 'cpu'

    # Create Environment
    env = KeepawayEnv(**vars(args))
    env = keepaway_env(env)

    args.max_episode_steps = env.episode_limit

    # Setup logging
    if args.continuing_checkpoint:
        args.save_dir = '/'.join(args.continuing_checkpoint.split('/')[:-1])
        for uid in range(1, 100):
            log_dir = os.path.join(args.save_dir, f'log-{uid}.txt')
            if not os.path.exists(log_dir):
                continuing_flag = f'-{uid}'
                break
    else:
        training = not (args.eval or args.record)
        args.save_dir = util.get_save_dir(args, training=training, name= args.exp_name)
        continuing_flag = ''
    
    log = util.get_logger(args.save_dir, args.name, continuing_flag)
    log.info(f'Device: {device}')
    tbx = SummaryWriter(args.save_dir)
    tabular_log_file = os.path.join(args.save_dir, 'progress' + continuing_flag + '.csv')
    text_log_file = os.path.join(args.save_dir, 'debug' + continuing_flag + '.log')
    logger.add_output(dowel.TextOutput(text_log_file))
    logger.add_output(dowel.CsvOutput(tabular_log_file))
    logger.add_output(dowel.StdOutput())
    log.info(f'Args: {dumps(vars(args), indent=4, sort_keys=True)}')

    # Set random seed
    log.info(f'Using random seed {args.seed}...')
    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    torch.cuda.manual_seed_all(args.seed)

    # Get model
    log.info('Building model...')
    # policy = make_mlp_policy(env, device)
    print("number of keepers: ", env.num_keepers)
    policy = DICGCECategoricalMLPPolicy2(
            env_spec=env,
            n_agents=env.num_agents,
            n_gcn_layers=args.n_gcn_layers,
            device=device)
    
    # print("state size : ", env.observation_space.shape[0])

    vf = CentValueFunction(
        state_size=env.observation_space.shape[0],
        device=device)
    
    policy = policy.to(device)
    vf = vf.to(device)
    
    algo = CentralizedMAPPO2(
        policy=policy,
        baseline=vf,
        optimizer=torch.optim.Adam,
        baseline_optimizer=torch.optim.Adam,
        optimization_n_minibatches=args.optimization_n_minibatches,
        optimization_mini_epochs=args.optimization_mini_epochs,
        policy_lr=args.policy_lr,
        baseline_lr=args.baseline_lr,
        max_path_length=args.max_episode_steps,
        discount=args.discount,
        gae_lambda=args.gae_lambda,
        center_adv=True,
        positive_adv=False,
        policy_ent_coeff=args.ent,
        use_softplus_entropy=False,
        stop_entropy_gradient=False,
        entropy_method='regularized',
        clip_grad_norm=args.max_grad_norm,
        lr_clip_range=args.lr_clip_range,
        device=device)

    if args.load_path or args.continuing_checkpoint:
        path = args.load_path if args.load_path is not None else args.continuing_checkpoint
        log.info(f'Loading checkpoint from {path}...')
        algo, start_epoch, start_env_steps = util.load_model(algo, path)
        algo = algo.to(device)
        if args.eval:
            eval_metric = env.eval(
                env=env,
                epoch=1,
                policy=algo.policy, 
                n_eval_episodes=args.n_eval_episodes, 
                greedy=args.eval_greedy, 
                visualize=args.visualize, 
                log=log, 
                tbx=tbx, 
                tabular=tabular,)
        elif args.record:
            pass
            # record_gym_video(env, args.video_save_path, 
            #                  n_episodes=5, policy=algo.policy)
        exit()
    else:
        start_epoch, start_env_steps = 0, 0

    algo = algo.to(device)
    algo.train()

    # Trajectory sampler
    sampler = CentralizedMAOnPolicySampler(
        algo, env,
        batch_size=args.batch_size,
        n_trajs_limit=args.n_trajs_limit,
        limit_by_traj=args.limit_by_traj)
    
    if start_env_steps != 0:
        sampler.tot_num_env_steps = start_env_steps

    # Get saver
    saver = util.CheckpointSaver(
        args.save_dir,
        max_checkpoints=args.max_checkpoints,
        metric_name=env.metric_name,
        maximize_metric=args.maximize_metric,
        log=log)

    # Training loop
    log.info('Training...')
    epochs_till_eval = args.eval_epochs
    
    for epoch in range(start_epoch, start_epoch + args.n_epochs):
        epoch += 1
        log.info(f'[epoch] {epoch} starting...')
        tbx.add_scalar('train/n_epochs', epoch, epoch)

        paths = sampler.obtain_samples(epoch, tbx)
        # print("paths: ", paths)

        avg_return = algo.train_once(epoch, paths, tbx)

        epochs_till_eval -= 1
        log.info(f'[epoch] {epoch}: avg episode reward: {avg_return}')

        # Eval
        if epochs_till_eval <= 0 or epoch == 1:
            log.info(f'[epoch] {epoch} evaluating...')
            algo.eval()
            eval_metric = env.eval(
                epoch=epoch,
                policy=algo.policy, 
                max_episode_length=args.max_episode_steps,
                n_eval_episodes=args.n_eval_episodes, 
                greedy=args.eval_greedy, 
                visualize=args.visualize, 
                log=log, 
                tbx=tbx, 
                tabular=tabular,)
            algo.train()
            epochs_till_eval = args.eval_epochs
            tbx.add_scalar('eval/env_steps', sampler.tot_num_env_steps, epoch)

            # Save
            saver.save(epoch, sampler.tot_num_env_steps, algo, eval_metric, device)
        else:
            tabular.record(env.metric_name, np.nan)
        
        log.info(args.exp_name)
        logger.log(tabular)
        logger.dump_all(epoch)
        tabular.clear()

if __name__ == '__main__':

    params = ["--config=dicg"]
    parent_dir = os.getcwd()
    config_file_path = os.path.join(parent_dir, "config", "dicg.yaml")
    with open(config_file_path, "r") as f:
        try:
            config_dict = yaml.safe_load(f)
        except yaml.YAMLError as exc:
            assert False, "default.yaml error: {}".format(exc)
    
    # print("config_dict: ", config_dict)
    config = get_config()["4v3"]
    config = config | config_dict
    config["log_level"] = "INFO"
    config["name"] = "keepaway"
    config["exp_name"] = ""
    config["n_agents"] = config["num_keepers"]
    # config["n_agents"] = config["num_keepers"] + config["num_takers"]
    config["n_actions"] = config["num_keepers"] 

    config = config | config_dict


    args = SN(**config)
    # print(args)
    # args = config
    train(args)
