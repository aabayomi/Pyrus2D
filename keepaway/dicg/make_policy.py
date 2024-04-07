# from args import args
from keepaway.garage.envs import GarageEnv
# from keepaway.dicg.torch.policies.proximal_cg_ce_categorical_mlp_policy import ProximalCGCECategoricalMLPPolicy
# from keepaway.dicg.torch.policies.dec_categorical_mlp_policy2 import DecCategoricalMLPPolicy
# from keepaway.dicg.torch.policies.dicg_ce_categorical_mlp_policy2 import DICGCECategoricalMLPPolicy

from keepaway.dicg.torch.policies.proximal_cg_ce_categorical_mlp_policy import ProximalCGCECategoricalMLPPolicy
from keepaway.dicg.torch.policies.dec_categorical_mlp_policy2 import DecCategoricalMLPPolicy2
from keepaway.dicg.torch.policies.dicg_ce_categorical_mlp_policy2 import DICGCECategoricalMLPPolicy2

# from args import args

def select_policy(env,args, device):
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