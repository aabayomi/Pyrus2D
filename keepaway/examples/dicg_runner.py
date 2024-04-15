import os
import time
import torch
from tqdm import tqdm
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

# from args import args

import collections
import argparse
import yaml 
import joblib
import time
from types import SimpleNamespace as SN
import torch
from torch.nn import functional as F

import akro
from os.path import dirname, abspath
# from garage.experiment.deterministic import set_seed

from keepaway.envs.keepaway_env import KeepawayEnv
from keepaway.envs.ka2pz import keepaway_env
from keepaway.dicg.torch.baselines import GaussianMLPBaseline
from keepaway.dicg.torch.algos import CentralizedMAPPO
from keepaway.dicg.torch.policies.dicg_ce_categorical_lstm_policy import DICGCECategoricalLSTMPolicy
# from dicg.experiment.local_runner_wrapper import LocalRunnerWrapper
from keepaway.dicg.sampler import CentralizedMAOnPolicyVectorizedSampler
from keepaway.dicg.torch.policies.dicg_ce_categorical_mlp_policy2 import DICGCECategoricalMLPPolicy2


results_path = os.path.join(dirname(dirname(abspath(__file__))), "dicg-results")

# def run(args):


#     if args.exp_name is None:
#         exp_layout = collections.OrderedDict([
#             ('dicg{}_ce_ppo', args.n_gcn_layers),
#             ('incact={}', bool(args.state_include_actions)),
#             ('atype={}', args.attention_type),
#             ('res={}', bool(args.residual)),
#             ('entcoeff={}', args.ent),
#             ('map={}', args.map),
#             ('difficulty={}', args.difficulty),
#             ('bs={:0.0e}', args.bs),
#             ('nenvs={}', args.n_envs),
#             ('splits={}', args.opt_n_minibatches),
#             ('miniepoch={}', args.opt_mini_epochs),
#             ('seed={}', args.seed)
#         ])

#         exp_name = '_'.join(
#             [key.format(val) for key, val in exp_layout.items()]
#         )

#         if args.comment != '':
#             exp_name = exp_name + '_' + args.comment
#     else:
#         exp_name = args.exp_name


#     prefix = 'keepaway'
#     id_suffix = ('_' + str(args.run_id)) if args.run_id != 0 else ''
#     exp_dir = './data/' + args.loc +'/' + exp_name + id_suffix

#     # Enforce
#     args.center_adv = False if args.entropy_method == 'max' else args.center_adv
#     set_seed(args.seed)

#     if args.mode == 'train':
#         # making sequential log dir if name already exists
#         @wrap_experiment(name=exp_name,
#                          prefix=prefix,
#                          log_dir=exp_dir,
#                          snapshot_mode='last', 
#                          snapshot_gap=1)
        
#         def train_smac(ctxt=None, args_dict=vars(args)):
#             args = SN(**args_dict)
            
#             # env = SMACWrapper(
#             #     centralized=True,
#             #     map_name=args.map,
#             #     difficulty=args.difficulty,
#             #     # seed=args.seed
#             # )
#             env = KeepawayEnv(**args)
            
#             # env = GarageEnv(env)

#             runner = LocalRunnerWrapper(
#                 ctxt,
#                 eval=args.eval_during_training,
#                 n_eval_episodes=args.n_eval_episodes,
#                 eval_greedy=args.eval_greedy,
#                 eval_epoch_freq=args.eval_epoch_freq,
#                 save_env=env.pickleable
#             )

#             hidden_nonlinearity = F.relu if args.hidden_nonlinearity == 'relu' \
#                                     else torch.tanh
#             policy = DICGCECategoricalLSTMPolicy(
#                 env.spec,
#                 n_agents=env.n_agents,
#                 encoder_hidden_sizes=args.encoder_hidden_sizes,
#                 embedding_dim=args.embedding_dim,
#                 attention_type=args.attention_type,
#                 n_gcn_layers=args.n_gcn_layers,
#                 residual=bool(args.residual),
#                 gcn_bias=bool(args.gcn_bias),
#                 lstm_hidden_size=args.lstm_hidden_size,
#                 state_include_actions=args.state_include_actions,
#                 name='dicg_ce_categorical_lstm_policy'
#             )

#             baseline = GaussianMLPBaseline(env_spec=env.spec,
#                                            hidden_sizes=(64, 64, 64))
            
#             # Set max_path_length <= max_steps
#             # If max_path_length > max_steps, algo will pad obs
#             # obs.shape = torch.Size([n_paths, algo.max_path_length, feat_dim])
#             algo = CentralizedMAPPO(
#                 env_spec=env.spec,
#                 policy=policy,
#                 baseline=baseline,
#                 max_path_length=env.episode_limit, # Notice
#                 discount=args.discount,
#                 center_adv=bool(args.center_adv),
#                 positive_adv=bool(args.positive_adv),
#                 gae_lambda=args.gae_lambda,
#                 policy_ent_coeff=args.ent,
#                 entropy_method=args.entropy_method,
#                 stop_entropy_gradient=True \
#                    if args.entropy_method == 'max' else False,
#                 clip_grad_norm=args.clip_grad_norm,
#                 optimization_n_minibatches=args.opt_n_minibatches,
#                 optimization_mini_epochs=args.opt_mini_epochs,
#             )
            
#             runner.setup(algo, env,
#                 sampler_cls=CentralizedMAOnPolicyVectorizedSampler, 
#                 sampler_args={'n_envs': args.n_envs})
#             runner.train(n_epochs=args.n_epochs, 
#                          batch_size=args.bs)

#         train_smac(args_dict=vars(args))

#     elif args.mode in ['restore', 'eval']:
#         env = SMACWrapper(
#             centralized=True,
#             map_name=args.map,
#             difficulty=args.difficulty,
#             replay_dir=exp_dir,
#             replay_prefix='dicg_ce_lstm',
#             # seed=args.seed
#         )
#         if args.mode == 'restore':
#             from dicg.experiment.runner_utils import restore_training
#             env = GarageEnv(env)
#             restore_training(exp_dir, exp_name, args,
#                              env_saved=False, env=env)

#         elif args.mode == 'eval':
#             data = joblib.load(exp_dir + '/params.pkl')
#             algo = data['algo']
#             env.eval(algo.policy, n_episodes=args.n_eval_episodes, 
#                 greedy=args.eval_greedy, load_from_file=True, 
#                 save_replay=args.save_replay)
#             env.close()


# if __name__ == '__main__':
#     params = ["--config=dicg"]
#     parent_dir = os.getcwd()
#     config_file_path = os.path.join(parent_dir, "config", "dicg.yaml")
#     with open(config_file_path, "r") as f:
#         try:
#             config_dict = yaml.safe_load(f)
#         except yaml.YAMLError as exc:
#             assert False, "default.yaml error: {}".format(exc)
    
#     # print("config_dict: ", config_dict)
#     config = get_config()["3v2"]
#     config = config | config_dict
#     config["log_level"] = "INFO"
#     config["name"] = "keepaway"
#     config["exp_name"] = ""
#     config["n_agents"] = config["num_keepers"]
#     # config["n_agents"] = config["num_keepers"] + config["num_takers"]
#     config["n_actions"] = config["num_keepers"] 


#     args = SN(**config)
#     run(args)



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
    policy = DICGCECategoricalMLPPolicy2(
            env_spec=env,
            n_agents=env.num_keepers,
            n_gcn_layers=args.n_gcn_layers,
            device=device)
    
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
                epoch=1,
                policy=algo.policy, 
                n_eval_episodes=args.n_eval_episodes, 
                greedy=args.eval_greedy, 
                visualize=args.visualize, 
                log=log, 
                tbx=tbx, 
                tabular=tabular,)
        elif args.record:
            record_gym_video(env, args.video_save_path, 
                             n_episodes=5, policy=algo.policy)
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
    paths = sampler.obtain_samples(1, tbx)
    avg_return = algo.train_once(1, paths, tbx)

    # for epoch in range(start_epoch, start_epoch + args.n_epochs):
    #     epoch += 1
    #     log.info(f'[epoch] {epoch} starting...')
    #     tbx.add_scalar('train/n_epochs', epoch, epoch)

    #     paths = sampler.obtain_samples(epoch, tbx)
    #     avg_return = algo.train_once(epoch, paths, tbx)

    #     epochs_till_eval -= 1
    #     log.info(f'[epoch] {epoch}: avg episode reward: {avg_return}')

    #     # Eval
    #     if epochs_till_eval <= 0 or epoch == 1:
    #         log.info(f'[epoch] {epoch} evaluating...')
    #         algo.eval()
    #         eval_metric = env.eval(
    #             epoch=epoch,
    #             policy=algo.policy, 
    #             n_eval_episodes=args.n_eval_episodes, 
    #             greedy=args.eval_greedy, 
    #             visualize=args.visualize, 
    #             log=log, 
    #             tbx=tbx, 
    #             tabular=tabular,)
    #         algo.train()
    #         epochs_till_eval = args.eval_epochs
    #         tbx.add_scalar('eval/env_steps', sampler.tot_num_env_steps, epoch)

    #         # Save
    #         saver.save(epoch, sampler.tot_num_env_steps, algo, eval_metric, device)
    #     else:
    #         tabular.record(env.metric_name, np.nan)
        
    #     log.info(args.exp_name)
    #     logger.log(tabular)
    #     logger.dump_all(epoch)
    #     tabular.clear()

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
    config = get_config()["3v2"]
    config = config | config_dict
    config["log_level"] = "INFO"
    config["name"] = "keepaway"
    config["exp_name"] = ""
    config["n_agents"] = config["num_keepers"]
    # config["n_agents"] = config["num_keepers"] + config["num_takers"]
    config["n_actions"] = config["num_keepers"] 

    config = config | config_dict


    args = SN(**config)
    print(args)
    # args = config
    train(args)
