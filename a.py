import base.main_keepaway_player as kp
import base.main_coach as main_c
import multiprocessing as mp
from time import sleep

players = []
from lib.player.world_model import WorldModel

keepers = 3
for i in range(2, keepers + 2):
    proc = mp.Process(target=kp.main, args=("keepers", i, False), name="keeper")
    proc.start()
    players.append(proc)
    sleep(0.25)

sleep(5)
