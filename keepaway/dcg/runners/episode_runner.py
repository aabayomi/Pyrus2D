import time
import numpy as np
from keepaway.envs import REGISTRY as env_REGISTRY
from functools import partial
from keepaway.dcg.components.episode_buffer import EpisodeBatch
from keepaway.envs.keepaway_env import KeepawayEnv

class EpisodeRunner:

    def __init__(self, args, logger):
        self.args = args
        self.logger = logger
        self.batch_size = self.args.batch_size_run
        assert self.batch_size == 1
        self.env_config = vars(args) ## should do some optimzations.
        self.env = env_REGISTRY[self.args.env](num_keepers=self.args.num_keepers, num_takers=self.args.num_takers, pitch_size=self.args.pitch_size)
        self.episode_limit = 1000
        self.t = 0
        self.t_env = 0

        self.train_returns = []
        self.test_returns = []
        self.train_stats = {}
        self.test_stats = {}
        # Log the first run
        self.log_train_stats_t = -1000000

    def setup(self, scheme, groups, preprocess, mac):
        self.new_batch = partial(EpisodeBatch, scheme, groups, self.batch_size, self.episode_limit + 1,
                                 preprocess=preprocess, device=self.args.device)
        self.mac = mac

    def get_env_info(self):
        return self.env.get_env_info()

    def save_replay(self):
        self.env.save_replay()

    def close_env(self):
        self.env.close()

    def reset(self):
        self.batch = self.new_batch()
        self.env.reset()
        self.t = 0
    
    def game_abstraction(self):
        from keepaway.envs.policies.random_agent import RandomPolicy
        episodes = 1
        print("Training episodes")
        print("launching game")
        self.env._launch_game()
        policy = RandomPolicy(self.env_config)
        self.env.render()
        for e in range(episodes):
            self.env.reset()
            terminated = False
            episode_reward = 0
            self.env.start()
            # self.run(terminated,test_mode=False)

            while not terminated:
                obs = self.env.get_obs()
                print("obs ", obs)
                actions, agent_infos = policy.get_actions(obs)
                # actions = self.mac.select_actions(self.batch, t_ep=self.t, t_env=self.t_env, test_mode=test_mode)
                # print(actions)
                reward, terminated, info = self.env.step(actions)
                # time.sleep(0.15)
                episode_reward += reward
        self.env.close()



    def run(self, test_mode=False):
        ## set the environment flag

        if self.env._run_flag == False:
            self.env._launch_game()
            self.env.render()
            self.reset()
            self.env._run_flag = True
            
        terminated = False
        episode_return = 0
        self.mac.init_hidden(batch_size=self.batch_size)
        self.env.start()

        
        # from keepaway.envs.policies.random_agent import RandomPolicy
        # policy = RandomPolicy(self.env_config)

        # while self.env._is_game_started() != True:
        #     print("Game started")
        #     while not terminated:
        #         obs = self.env.get_obs()
        #         # if (obs[1]  is not None ):
        #         #     print("obs ", obs[1]["state_vars"].shape)
        #         actions, agent_infos = policy.get_actions(obs)
        #         # print(actions)
        #         reward, terminated, info = self.env.step(actions)
        #         episode_return += reward

        #     print("episode_return ", episode_return)
        # self.env._episode_count += 1
        # import time
        # time.sleep(10)

        while not terminated:

            if not self.env._is_game_started():
                time.sleep(1)
                continue

            pre_transition_data = {
                "state": [self.env.get_state()],
                "avail_actions": [self.env.get_avail_actions()],
                "obs": [self.convert_to_numpy(self.env.get_obs())]
            }

            self.batch.update(pre_transition_data, ts=self.t)

            # Pass the entire batch of experiences up till now to the agents
            # Receive the actions for each agent at this time step in a batch of size 1
            actions = self.mac.select_actions(self.batch, t_ep=self.t, t_env=self.t_env, test_mode=test_mode)
            
            # print("actions ", actions)
            reward, terminated, env_info = self.env.step(actions[0])
            episode_return += reward

            post_transition_data = {
                "actions": actions,
                "reward": [(reward,)],
                "terminated": [(terminated != env_info.get("episode_limit", False),)],
            }
            # print("post_transition_data ", post_transition_data)
            self.batch.update(post_transition_data, ts=self.t)
            self.t += 1

        # print("episode_return ", episode_return)
        self.env._episode_count += 1

        # print("episode_return ", episode_return, " episode_count ", self.env._episode_count)
        last_data = {
            "state": [self.env.get_state()],
            "avail_actions": [self.env.get_avail_actions()],
            "obs": [self.convert_to_numpy(self.env.get_obs())]
        }
        self.batch.update(last_data, ts=self.t)

        # # Select actions in the last stored state
        actions = self.mac.select_actions(self.batch, t_ep=self.t, t_env=self.t_env, test_mode=test_mode)
        self.batch.update({"actions": actions}, ts=self.t)

        cur_stats = self.test_stats if test_mode else self.train_stats
        cur_returns = self.test_returns if test_mode else self.train_returns
        log_prefix = "test_" if test_mode else ""
        cur_stats.update({k: cur_stats.get(k, 0) + env_info.get(k, 0) for k in set(cur_stats) | set(env_info)})
        cur_stats["n_episodes"] = 1 + cur_stats.get("n_episodes", 0)
        cur_stats["ep_length"] = self.t + cur_stats.get("ep_length", 0)

        if not test_mode:
            self.t_env += self.t

        cur_returns.append(episode_return)

        if test_mode and (len(self.test_returns) == self.args.test_nepisode):
            self._log(cur_returns, cur_stats, log_prefix)
        elif self.t_env - self.log_train_stats_t >= self.args.runner_log_interval:
            self._log(cur_returns, cur_stats, log_prefix)
            if hasattr(self.mac.action_selector, "epsilon"):
                self.logger.log_stat("epsilon", self.mac.action_selector.epsilon, self.t_env)
            self.log_train_stats_t = self.t_env

        return self.batch
        
    


    def convert_to_numpy(self,proxy):
        regular_dict = dict(proxy)
        values = [item if isinstance(item, np.ndarray) else item['state_vars'] for item in regular_dict.values()] 
        # for i in range(len(values)):
        #     print("values ", values[i], "length ", len(values[i]))
        # print("values ", values[0], "length ", len(values[0]))
        numpy_array = np.stack(values, axis=0)
        return numpy_array

    def _log(self, returns, stats, prefix):
        self.logger.log_stat(prefix + "return_mean", np.mean(returns), self.t_env)
        self.logger.log_stat(prefix + "return_std", np.std(returns), self.t_env)
        returns.clear()

        for k, v in stats.items():
            if k != "n_episodes":
                self.logger.log_stat(prefix + k + "_mean" , v/stats["n_episodes"], self.t_env)
        stats.clear()
