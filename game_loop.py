## Test game loop for keepaway

from time import sleep
import base.main_keepaway_player as kp
import lib.player.world_model as wm

from time import sleep


import base.main_keepaway_player as kp
import base.main_coach as main_c
import multiprocessing as mp


def launch_players():
    players = []
    from lib.player.world_model import WorldModel

    keepers = 3
    for i in range(2, keepers + 2):
        proc = mp.Process(target=kp.main, args=("keepers", i, False), name="keeper")
        proc.start()
        players.append(proc)
        sleep(0.25)

    sleep(5)

    takers_list = []

    takers = 2
    for i in range(2, takers + 2):
        proc = mp.Process(target=kp.main, args=("takers", i, False), name="taker")
        proc.start()
        # takers_list.append(proc)
        sleep(0.25)

    sleep(5)


launch_players()
