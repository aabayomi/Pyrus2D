import argparse
from time import sleep
import base.main_player as main_p
import base.main_coach as main_c
import multiprocessing as mp
import team_config


## 



players = []

# goalie = mp.Process(target=main_p.main, args=(1,True))
# goalie.start()

# players.append(goalie)
keepers = 4

for i in range(2,keepers):
    proc = mp.Process(target=main_p.main)
    proc.start()
    players.append(proc)
    sleep(0.25)

sleep(5)

# coach = mp.Process(target=main_c.main)
# coach.start()
