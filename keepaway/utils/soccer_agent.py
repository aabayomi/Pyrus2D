import argparse
# from keepaway.config import team_config
from keepaway.config import team_config
from keepaway.lib.player.basic_client import BasicClient


class SoccerAgent:
    def __init__(self):
        self.load_config()  # Load configuration first
        self._client = BasicClient()
        self._goalie = False
    
    def load_config(self):
        self.team_name = team_config.TEAM_NAME
        self.out_option = team_config.OUT
        self.host = team_config.HOST
        self.player_port = team_config.PLAYER_PORT
        self.coach_port = team_config.COACH_PORT
        self.trainer_port = team_config.TRAINER_PORT
    
    
    def init_impl(self, goalie: bool) -> bool:
        pass

    def handle_start(self) -> bool:
        pass

    def run(self):
        pass

    def handle_exit(self):
        pass


# class SoccerAgent:
#     def __init__(self):
#         # self.parse_arguments()
#         self.team_name = self.parse_team_name_argument()
#         self.load_config()
#         self._client: BasicClient = BasicClient()
#         self._goalie = False
    
#     def load_config(self):
#         # Assuming the config file is named 'config.yaml' and located at the root
#         # with open('config.yaml', 'r') as file:
#         #     config = yaml.safe_load(file) 
#         self.team_name = team_config.TEAM_NAME
#         self.out_option = team_config.OUT
#         self.host = team_config.HOST
#         self.player_port = team_config.PLAYER_PORT
#         self.coach_port = team_config.COACH_PORT
#         self.trainer_port = team_config.TRAINER_PORT

#     def parse_team_name_argument(self):
#         parser = argparse.ArgumentParser(description='Start the Team. Runs the players and the coach.')
#         parser.add_argument('-t', '--team-name', required=True,
#                             help='Team name to display')
#         args = parser.parse_args()
#         return args.team_name



#     def init_impl(self, goalie: bool) -> bool:
#         pass

#     def handle_start(self) -> bool:
#         pass

#     def run(self):
#         pass

#     def handle_exit(self):
#         pass


# class SoccerAgent:
#     def __init__(self):
#         self.parse_arguments()
#         self._client: BasicClient = BasicClient()

#     def parse_arguments(self):
#         parser = argparse.ArgumentParser(description='Start the Team. Runs the players and the coach.')

#         parser.add_argument('-t', '--team-name',
#                             help='Team name to display')

#         parser.add_argument('-o', '--out',
#                             help='Output type(values->[std, textfile]). std for print on standard stream, unum for print to seperated files.')

#         parser.add_argument('-H', '--host',
#                             help='Server IP address')

#         parser.add_argument('-p', '--player-port',
#                             help='Server Player port')

#         parser.add_argument('-P', '--coach-port',
#                             help='Server Coach port')

#         parser.add_argument('--trainer-port',
#                             help='Server Trainer port')

#         parser.add_argument('-g', '--goalie',
#                             help='Server Trainer port',
#                             action='store_true')
        
#         parser.add_argument( '--keeper-count',
#                             help = "Number of keepers.")
        
#         parser.add_argument( '--taker-count',
#                             help = "Number of takers.")
    

#         args = parser.parse_args()

#         if args.team_name:
#             team_config.TEAM_NAME = args.team_name

#         if args.out:
#             team_config.OUT = team_config.OUT_OPTION(args.out)

#         if args.host:
#             team_config.HOST = args.host

#         if args.player_port:
#             team_config.PLAYER_PORT = args.player_port

#         if args.coach_port:
#             team_config.COACH_PORT = args.coach_port

#         if args.trainer_port:
#             team_config.TRAINER_PORT = args.trainer_port

#         if args.goalie:
#             self._goalie = True


#     def init_impl(self, goalie: bool) -> bool:
#         pass

#     def handle_start(self) -> bool:
#         pass

#     def run(self):
#         pass

#     def handle_exit(self):
#         pass

