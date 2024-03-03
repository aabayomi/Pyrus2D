import gym
import torch
import numpy as np
from gym import spaces
from gym.utils import seeding

import copy
from tqdm import tqdm
from envs.ma_gym.test_env.env import KeepawayEnv
from envs.ma_gym.utils.action_space import MultiAgentActionSpace
from envs.ma_gym.utils.observation_space import MultiAgentObservationSpace


class KeepawayWrapper(KeepawayEnv):
    def __init__(
        self,
        centralized,
        other_agent_visible=False,
        self_connected_adj=False,
        inv_D=False,
        proximity_threshold=2,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.centralized = centralized
        self.other_agent_visible = other_agent_visible

        self.mask_size = np.prod((5, 5))
        # self.action_space = MultiAgentActionSpace(
        #     [spaces.Discrete(5) for _ in range(self.num_keepers)]
        # )
        self.action_space = gym.spaces.Discrete(self.actions)
        self.n_agents = self.num_keepers

        ## verify this
        self._obs_high = np.array(
            [1.0, 1.0] + [1.0] * self.mask_size + [1.0], dtype=np.float32
        )
        self._obs_low = np.array(
            [0.0, 0.0] + [0.0] * self.mask_size + [0.0], dtype=np.float32
        )

        self.observation_space = MultiAgentObservationSpace(
            [spaces.Box(self._obs_low, self._obs_high) for _ in range(self.num_keepers)]
        )

        ## SMAC clone
        # self.agent_obs_dim = np.sum([np.prod(self.get_obs_move_feats_size()),
        #                              np.prod(self.get_obs_enemy_feats_size()),
        #                              np.prod(self.get_obs_ally_feats_size()),
        #                              np.prod(self.get_obs_own_feats_size())])
        # self.observation_space_low = [0] * self.agent_obs_dim
        # self.observation_space_high = [1] * self.agent_obs_dim
        # self.observation_space = gym.spaces.Box(
        #         low=np.array(self.observation_space_low),
        #         high=np.array(self.observation_space_high))
        ###

        ## not needed for now ..
        if self.other_agent_visible:
            self._obs_low = np.array([0.0, 0.0] + [0.0] * self.mask_size * 2 + [0.0])
            self._obs_high = np.array([1.0, 1.0] + [1.0] * self.mask_size * 2 + [1.0])
            self.observation_space = gym.spaces.Box(self._obs_low, self._obs_high)
        else:
            self.observation_space = self.observation_space[0]

        self.centralized = centralized
        if centralized:
            self.observation_space = gym.spaces.Box(
                low=np.array(list(self.observation_space.low) * self.num_keepers),
                high=np.array(list(self.observation_space.high) * self.num_keepers),
            )
        self.pickleable = True

        self.alive_mask = np.array([True] * self.num_keepers)
        self.threshold = proximity_threshold
        self.self_connected_adj = self_connected_adj
        self.inv_D = inv_D
        self.pickleable = True
        self.metric_name = "EvalAverageReturn"
        self.max_steps = 100
        
        self.start()

    ## gym version ..
    def get_avail_actions(self):
        avail_actions = [[1] * self.action_space.n for _ in range(self.num_keepers)]
        if not self.centralized:
            return avail_actions
        else:
            return np.concatenate(avail_actions)

    def get_agent_obs(self):
        obs = super().get_obs()
        # if self._agent_visible:
        #     for i_agent in range(self.n_agents):
        #         pos = self.agent_pos[i_agent]
        #         # check if other agents are in the view area
        #         _agent_pos = np.zeros(self._agent_view_mask)
        #         for row in range(
        #             max(0, pos[0] - 2), min(pos[0] + 2 + 1, self._grid_shape[0])
        #         ):
        #             for col in range(
        #                 max(0, pos[1] - 2), min(pos[1] + 2 + 1, self._grid_shape[1])
        #             ):
        #                 if PRE_IDS["agent"] in self._full_obs[row][col]:
        #                     # get relative position for the prey loc:
        #                     _agent_pos[row - (pos[0] - 2), col - (pos[1] - 2)] = 1

        #         obs[i_agent].extend(_agent_pos.flatten().tolist())
        return obs

    def step(self, actions):
        obses, rewards, dones, infos = super().step(actions)
        if not self.centralized:
            return obses, rewards, dones, infos
        else:
            return np.concatenate(obses), np.mean(rewards), np.all(dones), infos

    ## check for centralization.
    def reset(self):
        obses = super().reset()
        # Convert all None values to 0
        # obses = {k: (0 if v is None else v) for k, v in obses.items()}
        # obses = {k: (np.array(0) if v is None else v) for k, v in obses.items()}
        # print("jjf ", obses)

        if not self.centralized:
            return obses
        else:
            ## note observation is a dec np array 
            return obses

    ## maybe implement in real environment

    ## should this be here?.
    def get_proximity_adj_mat(self, raw=False):
        """Returns the proximity adjacency matrix of the agents. for DICG"""

        ## TODO include for adveserial coordination graph

        import math

        a = super().get_proximity_adj_mat()
        n = int(math.sqrt(len(a)))
        print("a ", a)
        adj = np.zeros((n,n))
        adj[:] = a.reshape(adj.shape)
        self.adj_raw = copy.deepcopy(adj)

        if raw:
            return adj

        if not self.inv_D:
            adj = (adj + np.eye(self.num_keepers)) if self.self_connected_adj else adj
            sqrt_D = np.diag(np.sqrt(np.sum(adj, axis=1)))
            adj_renormalized = sqrt_D @ adj @ sqrt_D
            print("adj ", adj_renormalized)
        else:
            adj = adj + np.eye(self.num_keepers)
            inv_sqrt_D = np.diag(np.sum(adj, axis=1) ** (-0.5))
            adj_renormalized = inv_sqrt_D @ adj @ inv_sqrt_D
            print("adj renormalized  ", adj_renormalized)
            return adj_renormalized

    # def get_proximity_adj_mat(self, raw=False):
    #     adj = np.zeros((self.num_keepers, self.num_keepers))
    #     for i in range(self.num_keepers - 1):
    #         for j in range(i + 1, self.num_keepers):
    #             pi, pj = self.agent_pos[i], self.agent_pos[j]
    #             dist = np.sqrt((pi[0] - pj[0]) ** 2 + (pi[1] - pj[1]) ** 2)
    #             if dist <= self.threshold:
    #                 adj[i, j] = 1
    #                 adj[j, i] = 1
    #     self.adj_raw = copy.deepcopy(adj)
    #     if raw:
    #         return adj
    #     if not self.inv_D:
    #         adj = (adj + np.eye(self.n_agents)) if self.self_connected_adj else adj
    #         sqrt_D = np.diag(np.sqrt(np.sum(adj, axis=1)))
    #         adj_renormalized = sqrt_D @ adj @ sqrt_D
    #     else:
    #         adj = adj + np.eye(self.n_agents)
    #         inv_sqrt_D = np.diag(np.sum(adj, axis=1) ** (-0.5))
    #         adj_renormalized = inv_sqrt_D @ adj @ inv_sqrt_D
    #     return adj_renormalized

    def eval(
        self,
        epoch,
        policy,
        n_eval_episodes=100,
        greedy=True,
        visualize=False,
        log=None,
        tbx=None,
        tabular=None,
    ):
        eval_avg_return = 0
        eval_env_steps = 0

        with torch.no_grad(), tqdm(total=n_eval_episodes) as progress_bar:
            for i_ep in range(n_eval_episodes):
                # Start episode
                obses = self.reset()  # (n_agents, obs_dim)

                for t in range(self.max_steps):
                    if policy.proximity_adj:
                        adjs = self.get_proximity_adj_mat()
                        alive_masks = None
                    else:
                        adjs = None
                        alive_masks = np.array(self.alive_mask)
                    avail_actions = self.get_avail_actions()
                    actions, agent_infos_n = policy.get_actions(
                        obses,
                        avail_actions,
                        adjs=adjs,
                        alive_masks=alive_masks,
                        greedy=greedy,
                    )

                    # if visualize:
                    #     self.render()
                    #     time.sleep(0.1)
                    # input()

                    next_obses, rewards, done, info = self.step(actions)

                    eval_avg_return += np.mean(rewards)
                    if done:
                        eval_env_steps += t + 1
                        break
                    obses = next_obses
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


if __name__ == "__main__":
    env = KeepawayWrapper(centralized=True)
    print(env.action_space)
    print(env.observation_space)
