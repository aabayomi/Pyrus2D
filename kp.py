import argparse
from time import sleep
import logging


# import base.main_keepaway_player as kp
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
    # command = ["rcssmonitor"] + monitor_options
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
    Popen(command)

    # Wait until the server is ready.
    # wait_for_server(options.port)
    # return popen.pid


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


def relative(path):
    """
    Returns a full path, relative to the current script's dir.
    """
    from os.path import abspath, dirname, join

    full = abspath(join(dirname(__file__), path))
    return full


# def launch_player(player_type, index, options):
#     """Launcher for both keepers and takers."""

#     from itertools import chain
#     from subprocess import Popen

#     # Build up the options for the player process.
#     # TODO $klog_opts $kdraw_opts $kweight_opts

#     # change use to locate saved policy in directory

#     # player_options = dict(
#     #     i="1",  # verbose
#     #     m="0",  # running mode
#     #     g=float(options.gamma),
#     #     L=float(options.lambd),
#     #     A=float(options.alpha),
#     #     I=float(options.initial_weight),
#     #     z=int(options.hierarchical_fsm),
#     #     E=int(options.crossEntropy),
#     #     Q=int(options.qlearning),
#     #     l=options.log_level,  # log level
#     #     o="logs/{}_{}_{}.log".format(player_type, options.label, index + 1),
#     #     e=int(getattr(options, player_type + "_learn")),
#     #     j=options.taker_count,
#     #     k=options.keeper_count,
#     #     p=options.port,
#     #     q=getattr(options, player_type + "_policy"),
#     #     t=player_type + "s",  # Pluralize for team name. TODO Really?
#     # )

#     # Handle optional args.
#     # def put_player_file(key, name):
#     #     value = getattr(options, name, None)
#     #     if value:
#     #         if options.file_per_player:
#     #             # Append player index before the extension.
#     #             # TODO Support prefixed 0 if more than 10 players?
#     #             pound_index = value.rfind("#")
#     #             if pound_index == -1:
#     #                 raise RuntimeError("No # in: " + value)
#     #             value = value[:pound_index] + str(index) + value[pound_index + 1 :]
#     #         if key.endswith("_output"):
#     #             # For output, we want to make sure we have a place to store it.
#     #             # Note that this assumes the value is proper file path/name.
#     #             # This isn't needed for input (and I have some policy modules
#     #             # that use input in fancier ways than just as file names).
#     #             ensure_parent_dir(value)
#     #         player_options[key] = value

#     # TODO Append player indices? Standard keepaway.sh does, and
#     # TODO LinearSarsaAgent saves for each player.
#     # TODO However, for my own input, I don't want independent files. Hrmm.
#     # put_player_file("f", player_type + "_output")
#     # put_player_file("w", player_type + "_input")

#     # Change the dict to a sorted list of args.
#     # player_options = player_options.items()
#     # player_options.sort()
#     # player_options = [("-%s" % option[0], str(option[1])) for option in player_options]
#     # player_options = list(chain(*player_options))

#     # Build keepaway_player command, and fork it off.
#     # if options.memory_check:
#     #     command = ['valgrind', relative('./player/keepaway_player')] + player_options
#     # else:
#     #     command = [relative('./player/keepaway_player')] + player_options

#     command = [relative("./base/main_trainer.py")]

#     # command = mp.Process(target=kp.main, args=("keepers", index, False))

#     logging.debug(command)
#     # print (" ".join(command))
#     popen = Popen(command)
#     return popen.pid


def run(options):
    """
    Run with an options object already given.
    Handy for calling from other scripts rather than a shell.
    """
    # print options
    # First, make sure a server isn't already running on this port.
    # if server_running(options.port):
    #     raise RuntimeError("Server already running on port {0}.".format(options.port))

    # Kick off server.
    # server_pid = launch_server(options)
    # print(server_pid)

    # Then keepers.
    keeper_pids = []
    # for i in range(options.keeper_count):
    for i in range(2, 4):
        proc = launch_player("keeper", i, options)
        keeper_pids.append(proc)
        # proc = mp.Process(target=kp.main, args=("keeper",i,False))
        # proc.start()
        # keeper_pids.append(proc)
        sleep(0.5)

    # Watch for the team to make sure keepers are team 0.
    logging.debug("Finished creating the keepers")
    # wait_for_players(options.port, "keepers")
    logging.debug("finished waiting for keeper players")

    # Then takers.
    logging.debug("number of takers received by the server: ")
    logging.debug(options.taker_count)

    for i in range(2):
        launch_player("taker", i, options)
        sleep(0.5)

    # # Allow dispstart to kick off play.
    # wait_for_players(options.port, "takers", True)

    # Then monitor.
    # if options.monitor:
    #     launch_monitor(options)

    # All done.
    # print(Any(keeper_pids=keeper_pids, server_pid=server_pid))
    # return Any(keeper_pids=keeper_pids, server_pid=server_pid)


if __name__ == "__main__":
    # main()
    # options =
    # default_port = defaults.get('port', 6000)
    # default_size = defaults.get('size', 20)
    options = parse_options()
    launch_server(options)
    launch_monitor(options)
    # run(options)
    # launch_players()
