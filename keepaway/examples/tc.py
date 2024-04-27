import numpy as np
import math

class ValueFunctionWithTile():
    def __init__(self,
                 state_low:np.array,
                 state_high:np.array,
                 num_tilings:int,
                 tile_width:np.array):
        """
        state_low: possible minimum value for each dimension in state
        state_high: possible maximum value for each dimension in state
        num_tilings: # tilings
        tile_width: tile width for each dimension
        """
        self.num_tilings = num_tilings
        self.tile_width = tile_width
        self.num_tiles = []
        self.offsets = []

        for i in range(len(self.tile_width)):

            self.num_tiles.append((math.ceil((state_high[i]-state_low[i])/self.tile_width[i])+1))

        # self.weights = np.zeros(np.append(self.num_tilings, self.num_tiles))

        for i in range(self.num_tilings):
            self.offsets.append((state_low - (i / self.num_tilings) * self.tile_width))

    def get_feature_vector(self,s): #10 x 5 x 5

        #self.active_tiles = np.zeros((self.num_tilings, self.num_tiles[0], self.num_tiles[0])) 
        self.indices = []
        for tile in range(self.num_tilings):
            # print("s", s)
            # print("offsets ", self.offsets[tile])
            d = np.floor((s - self.offsets[tile]) / self.tile_width).astype(int)
            x = d[0]
            y = d[1]
            self.indices.append(tile * 5 * 5 + x * 5 + y)
            #self.active_tiles[tile][x][y] = 1
        # return np.sum(self.weights * self.active_tiles)
        return np.sum(self.indices)

    def get_feature_vector_size(self):
        return (self.num_tilings, self.num_tiles[0], self.num_tiles[0])

    # def update(self,alpha,G,s_tau):
    #     self.idxs = []
    #     self.active_tiles = np.zeros(np.append(self.num_tilings, self.num_tiles))
    #     for tile in range(self.num_tilings):
    #         d = np.floor((s_tau - self.offsets[tile]) / self.tile_width).astype(int)
    #         x = d[0]
    #         y = d[1]
    #         self.active_tiles[tile][x][y] = 1
    #         self.idxs.append([tile, x, y])

    #     for tile, x, y in self.idxs:
    #         self.weights[tile][x][y] += alpha * (G - np.sum(self.weights * self.active_tiles))