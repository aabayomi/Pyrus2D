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

from keepaway.dicg.torch.algos import CentralizedMAPPO
from keepaway.dicg.torch.baselines import CentValueFunction
from keepaway.dicg.sampler import CentralizedMAOnPolicySampler

# from policy_maker import make_mlp_policy
# from env_maker import make_env
# from envs.utils import record_gym_video
import keepaway.dicg.util

# from args import args

import os
import collections
import numpy as np
import argparse
import yaml 
import joblib
import time
from types import SimpleNamespace
import torch
from torch.nn import functional as F

import akro
# import garage
# from garage import wrap_experiment
# from garage.envs import GarageEnv
from os.path import dirname, abspath
# from garage.experiment.deterministic import set_seed

from keepaway.envs.keepaway_env import KeepawayEnv
from keepaway.dicg.torch.baselines import GaussianMLPBaseline
from keepaway.dicg.torch.algos import CentralizedMAPPO
from keepaway.dicg.torch.policies.dicg_ce_categorical_lstm_policy import DICGCECategoricalLSTMPolicy
# from dicg.experiment.local_runner_wrapper import LocalRunnerWrapper
from keepaway.dicg.sampler import CentralizedMAOnPolicyVectorizedSampler


results_path = os.path.join(dirname(dirname(abspath(__file__))), "dicg-results")

def run(args):

    if args.exp_name is None:
        exp_layout = collections.OrderedDict([
            ('dicg{}_ce_ppo', args.n_gcn_layers),
            ('incact={}', bool(args.state_include_actions)),
            ('atype={}', args.attention_type),
            ('res={}', bool(args.residual)),
            ('entcoeff={}', args.ent),
            ('map={}', args.map),
            ('difficulty={}', args.difficulty),
            ('bs={:0.0e}', args.bs),
            ('nenvs={}', args.n_envs),
            ('splits={}', args.opt_n_minibatches),
            ('miniepoch={}', args.opt_mini_epochs),
            ('seed={}', args.seed)
        ])

        exp_name = '_'.join(
            [key.format(val) for key, val in exp_layout.items()]
        )

        if args.comment != '':
            exp_name = exp_name + '_' + args.comment
    else:
        exp_name = args.exp_name


    prefix = 'keepaway'
    id_suffix = ('_' + str(args.run_id)) if args.run_id != 0 else ''
    exp_dir = './data/' + args.loc +'/' + exp_name + id_suffix

    # Enforce
    args.center_adv = False if args.entropy_method == 'max' else args.center_adv
    set_seed(args.seed)

    if args.mode == 'train':
        # making sequential log dir if name already exists
        @wrap_experiment(name=exp_name,
                         prefix=prefix,
                         log_dir=exp_dir,
                         snapshot_mode='last', 
                         snapshot_gap=1)
        
        def train_smac(ctxt=None, args_dict=vars(args)):
            args = SimpleNamespace(**args_dict)
            
            env = SMACWrapper(
                centralized=True,
                map_name=args.map,
                difficulty=args.difficulty,
                # seed=args.seed
            )
            env = GarageEnv(env)

            runner = LocalRunnerWrapper(
                ctxt,
                eval=args.eval_during_training,
                n_eval_episodes=args.n_eval_episodes,
                eval_greedy=args.eval_greedy,
                eval_epoch_freq=args.eval_epoch_freq,
                save_env=env.pickleable
            )

            hidden_nonlinearity = F.relu if args.hidden_nonlinearity == 'relu' \
                                    else torch.tanh
            policy = DICGCECategoricalLSTMPolicy(
                env.spec,
                n_agents=env.n_agents,
                encoder_hidden_sizes=args.encoder_hidden_sizes,
                embedding_dim=args.embedding_dim,
                attention_type=args.attention_type,
                n_gcn_layers=args.n_gcn_layers,
                residual=bool(args.residual),
                gcn_bias=bool(args.gcn_bias),
                lstm_hidden_size=args.lstm_hidden_size,
                state_include_actions=args.state_include_actions,
                name='dicg_ce_categorical_lstm_policy'
            )

            baseline = GaussianMLPBaseline(env_spec=env.spec,
                                           hidden_sizes=(64, 64, 64))
            
            # Set max_path_length <= max_steps
            # If max_path_length > max_steps, algo will pad obs
            # obs.shape = torch.Size([n_paths, algo.max_path_length, feat_dim])
            algo = CentralizedMAPPO(
                env_spec=env.spec,
                policy=policy,
                baseline=baseline,
                max_path_length=env.episode_limit, # Notice
                discount=args.discount,
                center_adv=bool(args.center_adv),
                positive_adv=bool(args.positive_adv),
                gae_lambda=args.gae_lambda,
                policy_ent_coeff=args.ent,
                entropy_method=args.entropy_method,
                stop_entropy_gradient=True \
                   if args.entropy_method == 'max' else False,
                clip_grad_norm=args.clip_grad_norm,
                optimization_n_minibatches=args.opt_n_minibatches,
                optimization_mini_epochs=args.opt_mini_epochs,
            )
            
            runner.setup(algo, env,
                sampler_cls=CentralizedMAOnPolicyVectorizedSampler, 
                sampler_args={'n_envs': args.n_envs})
            runner.train(n_epochs=args.n_epochs, 
                         batch_size=args.bs)

        train_smac(args_dict=vars(args))

    elif args.mode in ['restore', 'eval']:
        env = SMACWrapper(
            centralized=True,
            map_name=args.map,
            difficulty=args.difficulty,
            replay_dir=exp_dir,
            replay_prefix='dicg_ce_lstm',
            # seed=args.seed
        )
        if args.mode == 'restore':
            from dicg.experiment.runner_utils import restore_training
            env = GarageEnv(env)
            restore_training(exp_dir, exp_name, args,
                             env_saved=False, env=env)

        elif args.mode == 'eval':
            data = joblib.load(exp_dir + '/params.pkl')
            algo = data['algo']
            env.eval(algo.policy, n_episodes=args.n_eval_episodes, 
                greedy=args.eval_greedy, load_from_file=True, 
                save_replay=args.save_replay)
            env.close()


if __name__ == '__main__':
    params = ["--config=dicg"]
    parent_dir = os.getcwd()
    config_file_path = os.path.join(parent_dir, "config", "dicg.yaml")
    with open(config_file_path, "r") as f:
        try:
            config_dict = yaml.safe_load(f)
        except yaml.YAMLError as exc:
            assert False, "default.yaml error: {}".format(exc)
    
    print("config_dict: ", config_dict)
    # run(args)


