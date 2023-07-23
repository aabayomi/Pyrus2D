import argparse
from time import sleep

import base.main_keepaway_player as kp
import base.main_coach as main_c
import multiprocessing as mp


import team_config


## Launch server


def launch_monitor(options):
    from subprocess import Popen

    # I can't find any way to zoom automatically on startup. Oh well.
    monitor_options = [("server-port", options.port)]
    monitor_options = ["--%s=%s" % option for option in monitor_options]

    command = ["soccerwindow2 &"]
    # command = ['rcssmonitor'] + monitor_options
    # print command
    # print " ".join(command)
    Popen(command, shell=True)


def launch_server(options):
    """
    Launches the server.
    Returns its process id.
    """
    from subprocess import Popen
    from time import strftime

    # Some helpful vars.
    log_name = "%s" % strftime("%Y%m%d%H%M%S")
    if options.label:
        log_name += "-" + options.label

    # Build up the server arguments. Alphabetical order follows.
    server_options = []

    # Coach/trainer mode.
    server_options += [
        ("coach", int(options.coach)),
        ("coach_port", options.coach_port),
    ]

    # Hardcoded settings for keepaway play.
    server_options += [("forbid_kick_off_offside", 1)]
    server_options += [("half_time", -1)]

    # Either keepaway or trainer mode. Field size.
    server_options += [("keepaway", int(not options.coach))]
    server_options += [("keepaway_start", options.game_start)]
    server_options += [
        ("keepaway_length", options.field_length),
        ("keepaway_width", options.field_width),
    ]

    if options.log_keepaway:
        server_options += [
            ("keepaway_logging", 1),
            ("keepaway_log_dir", options.log_dir),
            ("keepaway_log_fixed", 1),
            ("keepaway_log_fixed_name", log_name),
        ]

    if options.log_game:
        server_options += [
            ("game_log_compression", 1),
            ("game_log_dir", options.log_dir),
            ("game_log_fixed", 1),
            ("game_log_fixed_name", log_name),
            ("game_log_version", 5),
        ]
    else:
        server_options += [("game_logging", 0)]

    # Server and online coach ports.
    server_options += [
        ("olcoach_port", options.online_coach_port),
        ("port", options.port),
    ]

    # Hardcoded stamina inc. This was hardcoded in keepaway.sh.
    # TODO What's the effect, and what's default?
    # TODO Any changes to other new defaults in rcssserver to retain benchmarks?
    server_options += [("stamina_inc_max", 3500)]

    server_options += [("fullstate_l", int(options.fullstate))]
    server_options += [("fullstate_r", int(options.fullstate))]

    # Synch mode. TODO What's default, and does synch offset matter when not
    # TODO in synch mode?
    server_options += [
        ("synch_mode", int(options.synch_mode)),
        ("synch_offset", 60),
        ("synch_see_offset", 0),
    ]

    if options.log_text:
        server_options += [
            ("text_log_compression", 1),
            ("text_log_dir", options.log_dir),
            ("text_log_fixed", 1),
            ("text_log_fixed_name", log_name),
        ]
    else:
        server_options += [("text_logging", 0)]

    # More hardcoded settings for keepaway play.
    server_options += [("use_offside", 0)]

    # Vision limits. TODO What's the normal default?
    if not options.restricted_vision:
        server_options += [("visible_angle", 360)]

    server_options = ["server::%s=%s" % option for option in server_options]

    # Build rcssserver command, and fork it off.
    # TODO Locate rcssserver executable reliably.

    print(server_options)

    command = ["rcssserver"] + server_options

    # print command
    # print " ".join(command)
    # logging.debug("Built the command to connect to the server")
    popen = Popen(command)

    # Wait until the server is ready.
    # wait_for_server(options.port)
    return popen.pid


def parse_options(args=None, **defaults):
    """
    Parses the given list of args, defaulting to sys.argv[1:].
    Provide [] for default options.
    """
    from optparse import OptionParser

    parser = OptionParser()
    default_port = defaults.get("port", 6000)
    default_size = defaults.get("size", 20)

    # TODO Apply other defaults below?
    parser.add_option(
        "--coach",
        action="store_true",
        default=False,
        help="Use trainer instead of server referee.",
    )
    parser.add_option(
        # TODO More options are needed before coach/trainer is ready.
        "--coach-port",
        type="int",
        default=None,
        help="Offline trainer port.",
    )
    parser.add_option(
        "--field-length",
        type="int",
        default=default_size,
        help="Playing field x-axis size.",
    )
    parser.add_option(
        "--field-width",
        type="int",
        default=default_size,
        help="Playing field y-axis size.",
    )
    parser.add_option(
        "--file-per-player",
        action="store_true",
        default=False,
        help="Replace last occurrence of # in player file names with the "
        "player's index number.",
    )
    parser.add_option(
        "--game-start",
        type="int",
        default=8,
        help="Game start delay time, although we also now kick off 1 second "
        "after takers appear.",
    )
    parser.add_option(
        "--keeper-count", type="int", default=3, help="Number of keepers."
    )
    parser.add_option(
        "--keeper-input", help="Input (file) name for keeper policy agent."
    )
    parser.add_option(
        "--keeper-learn",
        action="store_true",
        default=False,
        help="Turn learning on for keepers.",
    )
    parser.add_option(
        "--keeper-output", help="Output (file) name for keeper policy agent."
    )
    parser.add_option(
        "--keeper-policy",
        # Allow --keeper-policy=ext=./whatever.so, so remove choices.
        # TODO Nicer syntax for extensions?
        # type = 'choice', choices = ['hand', 'hold', 'learned', 'rand'],
        default="rand",
        help="The policy for the keepers to follow: hand, hold, learned or rand",
    )
    parser.add_option(
        "--label", default="", help="Prefix to the extension for log files."
    )
    parser.add_option(
        "--log-dir", default="./logs", help="Directory for storing log files."
    )
    parser.add_option(
        "--log-game", action="store_true", default=False, help="Save rcg log file."
    )
    parser.add_option(
        "--log-text",
        action="store_true",
        default=False,
        help="Save rcl (message/command) log file.",
    )
    parser.add_option(
        "--monitor",
        action="store_true",
        default=False,
        help="Launch the monitor to watch the play.",
    )
    parser.add_option(
        "--no-log-keepaway",
        action="store_false",
        default=True,
        dest="log_keepaway",
        help="Do not save kwy log file.",
    )
    parser.add_option(
        "--online-coach-port", type="int", default=None, help="Online coach port."
    )
    parser.add_option(
        "--port", type="int", default=default_port, help="RCSS server port."
    )
    parser.add_option(
        "--restricted-vision",
        action="store_true",
        default=False,
        help="Restrict player vision to less than 360 degrees.",
    )
    # TODO Perhaps kick off a monitor here to watch for episodes?
    parser.add_option(
        "--synch-mode",
        action="store_true",
        default=False,
        help="Speed up with synchronous mode.",
    )
    parser.add_option("--taker-count", type="int", default=2, help="Number of takers.")
    parser.add_option("--taker-input", help="Input (file) name for taker policy agent.")
    parser.add_option(
        "--taker-learn",
        action="store_true",
        default=False,
        help="Turn learning on for takers.",
    )
    parser.add_option(
        "--taker-output", help="Output (file) name for taker policy agent."
    )
    parser.add_option(
        "--taker-policy",
        default="hand",
        # Allow --keeper-policy=ext=./whatever.so, so remove choices.
        # TODO Nicer syntax for extensions?
        # type = 'choice', choices = ['hand', 'learned'],
        help="The policy for the takers to follow.",
    )
    parser.add_option("--log-level", type="int", default=0, help="Text log level.")
    parser.add_option(
        "--fullstate",
        action="store_true",
        default=False,
        help="Use fullstate information for left and right.",
    )
    parser.add_option(
        "--hierarchical-fsm",
        action="store_true",
        default=False,
        help="Use hierarchical FSMs for learning.",
    )
    parser.add_option(
        "--crossEntropy",
        action="store_true",
        default=False,
        help="Use cross entropy for learning.",
    )
    parser.add_option(
        "--qlearning",
        action="store_true",
        default=False,
        help="Use QLearning (instead of SARSA).",
    )
    parser.add_option("--gamma", type="float", default=1.0, help="gamma.")
    parser.add_option("--lambd", type="float", default=0.0, help="lambda.")
    parser.add_option("--alpha", type="float", default=0.125, help="alpha.")
    parser.add_option(
        "--memory-check",
        action="store_true",
        default=False,
        help="Use valgrind to check memory bugs.",
    )
    parser.add_option(
        "--initial-weight", type="float", default=0.0, help="Initial weight values."
    )

    options = parser.parse_args(args)[0]
    # Set coach_port and online_coach_port here, if not set previously.
    # This will allow them to be based on the args-given port.
    # This way, things still work even if just given a new main port.
    if not options.coach_port:
        options.coach_port = options.port + 1
    if not options.online_coach_port:
        # Seems nicer to base this on coach port, in case it was given manually.
        options.online_coach_port = options.coach_port + 1
    return options


def launch_players():
    players = []
    from lib.player.world_model import WorldModel

    # keepers = 3
    # for i in range(2, keepers + 2):
    #     proc = mp.Process(target=kp.main, args=("keepers", i, False))
    #     proc.start()
    #     players.append(proc)
    #     sleep(0.25)

    # sleep(5)

    # takers_list = []

    takers = 2
    for i in range(2, takers + 2):
        proc = mp.Process(target=kp.main, args=("takers", i, False))
        proc.start()
        takers_list.append(proc)
        sleep(0.25)

    sleep(5)


if __name__ == "__main__":
    # main()
    # options =
    # default_port = defaults.get('port', 6000)
    # default_size = defaults.get('size', 20)
    options = parse_options()
    launch_server(options)
    launch_monitor(options)
    launch_players()
