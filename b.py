import argparse
from time import sleep
import logging


import base.main_keepaway_player as kp
import base.main_coach as main_c
import multiprocessing as mp


takers_list = []

takers = 2
for i in range(2, takers + 2):
    proc = mp.Process(target=kp.main, args=("takers", i, False), name="taker")
    proc.start()
    # takers_list.append(proc)
    sleep(0.25)
