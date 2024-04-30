import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
# from keepaway.garage.torch.algos import filter_valids

def filter_valids(tensor, valids):
    """Filter out tensor using valids (last index of valid tensors).

    valids contains last indices of each rows.

    Args:
        tensor (torch.Tensor): The tensor to filter
        valids (list[int]): Array of length of the valid values

    Returns:
        torch.Tensor: Filtered Tensor

    """
    return [tensor[i][:valids[i]] for i in range(len(valids))]

class CentValueFunction(nn.Module):
    def __init__(self,
                 state_size,
                 hidden_size=256,
                 device='cpu'):
        
        super().__init__()

        self.device = device

        self.vf = self.vf = nn.Sequential(
            nn.Linear(state_size, hidden_size),
            nn.ReLU(),
            nn.Linear(hidden_size, 64),
            nn.ReLU(),
            nn.Linear(64, 1)
        )

    def grad_norm(self):
        return np.sqrt(
            np.sum([p.grad.norm(2).item() ** 2 for p in self.parameters()]))

    def compute_loss(self, state, true_val):
        # returns.shape = (n_paths, max_t)
        est_returns = self.forward(state) #
        # flatten len = valids[0] + valids[1] + ...
        # print('valid_est_returns.shape =', valid_est_returns.shape)
        
        return F.mse_loss(true_val, est_returns)


    def forward(self, state):
        # print('state.shape =', state.shape)
        if not torch.is_tensor(state):
            state = torch.tensor(state).float().to(self.device) # (n_paths, max_t, state_dim)
        est_returns = self.vf(state).squeeze()
        # print('est_returns.shape =', est_returns.shape)
        return est_returns