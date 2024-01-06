from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from absl import app
import absl.flags as flags
from absl import logging
from subprocess import Popen
from time import strftime

# from Pyrus2D import team_config

# Default values
default_port = 6000
default_size = 20


def define_flags():
    flags.DEFINE_integer("keepers", 3, "Number of keepers (default: 3)")
    flags.DEFINE_integer("takers", 2, "Number of takers (default: 2)")
    flags.DEFINE_bool("render", True, "Whether to do game rendering.")

    flags.DEFINE_boolean("coach", False, "Use trainer instead of server referee.")
    flags.DEFINE_integer("coach_port", None, "Offline trainer port.")
    flags.DEFINE_integer("field_length", default_size, "Playing field x-axis size.")
    flags.DEFINE_integer("field_width", default_size, "Playing field y-axis size.")
    flags.DEFINE_boolean(
        "file_per_player",
        False,
        "Replace last occurrence of # in player file names with the player's index number.",
    )
    flags.DEFINE_integer(
        "game_start",
        8,
        "Game start delay time, although we also now kick off 1 second after takers appear.",
    )
    flags.DEFINE_string(
        "keeper_input", None, "Input (file) name for keeper policy agent."
    )
    flags.DEFINE_boolean("keeper_learn", False, "Turn learning on for keepers.")
    flags.DEFINE_string(
        "keeper_output", None, "Output (file) name for keeper policy agent."
    )
    flags.DEFINE_string(
        "keeper_policy",
        "rand",
        "The policy for the keepers to follow: hand, hold, learned or rand",
    )
    flags.DEFINE_string("label", "", "Prefix to the extension for log files.")
    # flags.DEFINE_string("log_dir", "./logs", "Directory for storing log files.")
    flags.DEFINE_boolean("log_game", False, "Save rcg log file.")
    flags.DEFINE_boolean("log_text", False, "Save rcl (message/command) log file.")
    flags.DEFINE_boolean("monitor", False, "Launch the monitor to watch the play.")
    flags.DEFINE_boolean("log_keepaway", True, "Save kwy log file.")
    flags.DEFINE_integer("online_coach_port", None, "Online coach port.")
    flags.DEFINE_integer("port", default_port, "RCSS server port.")
    flags.DEFINE_boolean(
        "restricted_vision", False, "Restrict player vision to less than 360 degrees."
    )
    flags.DEFINE_boolean("synch_mode", False, "Speed up with synchronous mode.")
    flags.DEFINE_string(
        "taker_input", None, "Input (file) name for taker policy agent."
    )
    flags.DEFINE_boolean("taker_learn", False, "Turn learning on for takers.")
    flags.DEFINE_string(
        "taker_output", None, "Output (file) name for taker policy agent."
    )
    flags.DEFINE_string("taker_policy", "hand", "The policy for the takers to follow.")
    flags.DEFINE_integer("log_level", 0, "Text log level.")
    flags.DEFINE_boolean(
        "fullstate", False, "Use fullstate information for left and right."
    )
    flags.DEFINE_boolean(
        "hierarchical_fsm", False, "Use hierarchical FSMs for learning."
    )
    flags.DEFINE_boolean("crossEntropy", False, "Use cross entropy for learning.")
    flags.DEFINE_boolean("qlearning", False, "Use QLearning (instead of SARSA).")
    flags.DEFINE_float("gamma", 1.0, "gamma.")
    flags.DEFINE_float("lambd", 0.0, "lambda.")
    flags.DEFINE_float("alpha", 0.125, "alpha.")
    flags.DEFINE_boolean("memory_check", False, "Use valgrind to check memory bugs.")
    flags.DEFINE_float("initial_weight", 0.0, "Initial weight values.")


def launch_monitor(FLAGS=flags.FLAGS):
    monitor_options = [("server-port", FLAGS.port)]
    monitor_options = ["--%s=%s" % option for option in monitor_options]
    command = ["soccerwindow2 &"]
    Popen(command, shell=True)


def launch_server():
    """
    Launches the server.
    Returns its process id.
    """

    # Some helpful vars.
    log_name = "%s" % strftime("%Y%m%d%H%M%S")
    if flags.FLAGS.label:
        log_name += "-" + flags.FLAGS.label

    # Build up the server arguments. Alphabetical order follows.
    server_options = []

    # Coach/trainer mode.
    server_options += [
        ("coach", int(flags.FLAGS.coach)),
        ("coach_port", flags.FLAGS.coach_port),
    ]

    # Hardcoded settings for keepaway play.
    server_options += [("forbid_kick_off_offside", 1)]
    server_options += [("half_time", -1)]

    # Either keepaway or trainer mode. Field size.
    server_options += [("keepaway", int(not flags.FLAGS.coach))]
    server_options += [("keepaway_start", flags.FLAGS.game_start)]
    server_options += [
        ("keepaway_length", flags.FLAGS.field_length),
        ("keepaway_width", flags.FLAGS.field_width),
    ]

    if flags.FLAGS.log_keepaway:
        server_options += [
            ("keepaway_logging", 1),
            ("keepaway_log_dir", flags.FLAGS.log_dir),
            ("keepaway_log_fixed", 1),
            ("keepaway_log_fixed_name", log_name),
        ]

    if flags.FLAGS.log_game:
        server_options += [
            ("game_log_compression", 1),
            ("game_log_dir", flags.FLAGS.log_dir),
            ("game_log_fixed", 1),
            ("game_log_fixed_name", log_name),
            ("game_log_version", 5),
        ]
    else:
        server_options += [("game_logging", 0)]

    # Server and online coach ports.
    server_options += [
        ("olcoach_port", flags.FLAGS.online_coach_port),
        ("port", flags.FLAGS.port),
    ]

    server_options += [("stamina_inc_max", 3500)]

    server_options += [("fullstate_l", int(flags.FLAGS.fullstate))]
    server_options += [("fullstate_r", int(flags.FLAGS.fullstate))]

    server_options += [
        ("synch_mode", int(flags.FLAGS.synch_mode)),
        ("synch_offset", 60),
        ("synch_see_offset", 0),
    ]

    if flags.FLAGS.log_text:
        server_options += [
            ("text_log_compression", 1),
            ("text_log_dir", flags.FLAGS.log_dir),
            ("text_log_fixed", 1),
            ("text_log_fixed_name", log_name),
        ]
    else:
        server_options += [("text_logging", 0)]

    # More hardcoded settings for keepaway play.
    server_options += [("use_offside", 0)]

    # Vision limits. TODO What's the normal default?
    if not flags.FLAGS.restricted_vision:
        server_options += [("visible_angle", 360)]

    server_options = ["server::%s=%s" % option for option in server_options]

    # Build rcssserver command, and fork it off.
    # TODO Locate rcssserver executable reliably.
    command = ["rcssserver"] + server_options
    Popen(command)


def main(argv):
    # Parse flags
    define_flags()
    flags.FLAGS(argv)
    launch_monitor(FLAGS=flags.FLAGS)
    launch_server()

    # Access flag values
    num_keepers = flags.FLAGS.keepers
    num_takers = flags.FLAGS.takers
    # Perform some action based on the flag values
    print("Number of keepers: {}".format(num_keepers))
    print("Number of takers: {}".format(num_takers))


if __name__ == "__main__":
    import sys

    main(sys.argv)
