from __future__ import absolute_import, division, print_function

import time
from absl import logging
from env import KeepawayEnv
logging.set_verbosity(logging.DEBUG)
from env import KeepawayEnv


def main():
    env = KeepawayEnv()
    print("launching game")
    env._launch_game()
    time.sleep(10)
    print("closing game")
    env.close()


if __name__ == "__main__":
    main()