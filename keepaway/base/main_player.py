#!/usr/bin/python3
from keepaway.base.sample_player import SamplePlayer


def main():
    agent = SamplePlayer()
    if not agent.handle_start():
        agent.handle_exit()
        return
    agent.run()


if __name__ == "__main__":
    main()
