import yaml
from optparse import OptionParser
import yaml
import sys
from subprocess import Popen
from time import strftime


def launch_monitor(options):
    """Launches the monitor."""
    monitor_cmd = f"soccerwindow2 &"
    # monitor_cmd = f"rcssmonitor --server-port={options.port}"

    Popen(monitor_cmd, shell=True)


def launch_server(options):
    """Launches the server with the given options."""

    # Some helpful vars.
    log_name = f"{strftime('%Y%m%d%H%M%S')}"
    # if options.label:
    #     log_name += f"-{options.label}"

    # Build up the server arguments. Alphabetical order follows.
    server_options = [
        f"server::{opt}={val}"
        for opt, val in {
            "coach": int(options.coach),
            "coach_port": int(options.coach_port),
            "forbid_kick_off_offside": 1,
            "half_time": -1,
            "keepaway": int(not options.coach),
            "keepaway_start": options.game_start,
            "keepaway_length": int(options.field_length),
            "keepaway_width": int(options.field_width),
            "keepaway_logging": 1 if options.log_keepaway else 0,
            "keepaway_log_dir": options.log_dir if options.log_keepaway else None,
            "keepaway_log_fixed": 1 if options.log_keepaway else 0,
            "keepaway_log_fixed_name": log_name if options.log_keepaway else None,
            "game_log_compression": 1,
            "game_log_dir": options.log_dir if options.log_game else None,
            "game_log_fixed": 1 if options.log_game else 0,
            "game_log_fixed_name": log_name if options.log_game else None,
            "game_log_version": 5 if options.log_game else 0,
            "game_logging": 0,
            "olcoach_port": options.online_coach_port,
            "port": options.port,
            "stamina_inc_max": 3500,
            "fullstate_l": int(options.fullstate),
            "fullstate_r": int(options.fullstate),
            "synch_mode": int(options.synch_mode),
            "synch_offset": 60,
            "synch_see_offset": 0,
            "text_log_compression": 1 if options.log_text else 0,
            "text_log_dir": options.log_dir if options.log_text else None,
            "text_log_fixed": 1 if options.log_text else 0,
            "text_log_fixed_name": log_name if options.log_text else None,
            "text_logging": 0,
            "use_offside": 0,
            "visible_angle": 360 if not options.restricted_vision else None,
        }.items()
        if val is not None
    ]

    # Build rcssserver command, and fork it off.
    print(server_options)

    command = ["rcssserver"] + server_options
    Popen(command)


def parse_options(args=None):
    """
    Parses the given list of args, defaulting to sys.argv[1:].
    Retrieve other options from the YAML config file.
    """

    # Load the default values from YAML file
    with open("config.yml", "r") as ymlfile:
        config = yaml.safe_load(ymlfile)

    parser = OptionParser()

    # Command line arguments
    # parser.add_option("--field-length", type="int", help="Playing field x-axis size.")
    # parser.add_option("--field-width", type="int", help="Playing field y-axis size.")
    # parser.add_option("--keeper-count", type="int", help="Number of keepers.")
    # parser.add_option("--taker-count", type="int", help="Number of takers.")
    # parser.add_option(
    #     "--log-dir", default="./logs", help="Directory for storing log files."
    # )

    # New options for launching server and monitor
    # parser.add_option(
    #     "--launch-server",
    #     action="store_true",
    #     default=False,
    #     help="Launch the server with the given options.",
    # )

    # parser.add_option(
    #     "--launch-monitor",
    #     action="store_true",
    #     default=False,
    #     help="Launch the monitor with the given options.",
    # )

    options, _ = parser.parse_args(args)
    # Merging command-line options with YAML defaults
    for key, value in config.items():
        if not getattr(options, key, None):
            setattr(options, key, value)
    return options


if __name__ == "__main__":
    options = parse_options(sys.argv[1:])
    print(options)  # to verify the parsed options
    # launch_monitor(options)
    launch_server(options)

    # if options.launch_server:
    #     launch_server(options)

    # if options.launch_monitor:
    #     launch_monitor(options)
