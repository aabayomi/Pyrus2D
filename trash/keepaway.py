import argparse
from time import sleep
import keeepaway_utils.main_keepaway_player as kp
import base.main_coach as main_c
import multiprocessing as mp
import team_config


## Launch server


players = []
keepers = 3
for i in range(2, keepers + 2):
    proc = mp.Process(target=kp.main, args=("keepers", i, False))
    proc.start()
    players.append(proc)
    sleep(0.25)

sleep(5)


takers = 2
for i in range(2, takers + 2):
    proc = mp.Process(target=kp.main, args=("takers", i, False))
    proc.start()
    players.append(proc)
    sleep(0.25)

sleep(5)
