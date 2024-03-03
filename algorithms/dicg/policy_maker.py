
import sys
import os

current_file_path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_file_path + '/../../')

from args import args
from garage.envs import GarageEnv
from torch_.policies import *
from args import args

def make_mlp_policy(env, device):
    g_env = GarageEnv(env)
    if args.policy == 'proximal_cg':
        policy = ProximalCGCECategoricalMLPPolicy(
            env_spec=g_env.spec,
            n_agents=env.n_agents,
            n_gcn_layers=args.n_gcn_layers,
            device=device)
    
    elif args.policy == 'dicg_ce':
        policy = policy = DICGCECategoricalMLPPolicy2(
            env_spec=g_env.spec,
            n_agents=env.n_agents,
            n_gcn_layers=args.n_gcn_layers,
            device=device)
    elif args.policy == 'de':
        policy = DecCategoricalMLPPolicy2(
            env_spec=g_env, 
            n_agents=env.n_agents,
            device=device)
    else:
        NotImplementedError
    
    return policy
