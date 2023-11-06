## Duplicate of world_model_keepaway.py

from turtle import pos
from lib.action.intercept_table import InterceptTable
from lib.debug.debug import log
from lib.player.localizer import Localizer
from lib.messenger.messenger import Messenger
from lib.messenger.messenger_memory import MessengerMemory
from lib.player.object_player import *
from lib.player.object_ball import *
from lib.parser.parser_message_fullstate_world import FullStateWorldMessageParser
from lib.player.object_self import SelfObject
from lib.player.sensor.body_sensor import SenseBodyParser
from lib.player.sensor.visual_sensor import SeeParser
from lib.player.view_area import ViewArea
from lib.player_command.player_command_support import PlayerAttentiontoCommand
from lib.rcsc.game_mode import GameMode
from lib.rcsc.game_time import GameTime
from lib.rcsc.types import HETERO_DEFAULT, UNUM_UNKNOWN, GameModeType
from pyrusgeom.soccer_math import *
from lib.player import WorldModel
from typing import List


DEBUG =True


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from lib.player.action_effector import ActionEffector
    

def player_accuracy_value(p: PlayerObject):
    value: int = 0
    if p.goalie():
        value += -1000
    elif p.unum() == UNUM_UNKNOWN:
        value += 1000
    value += p.pos_count() + p.ghost_count() * 10
    return value

def player_count_value(p: PlayerObject):
    return p.pos_count() + p.ghost_count() * 10

def player_valid_check(p: PlayerObject):
    return p.pos_valid()

class WorldModelKeepaway(WorldModel):
   
   ## TODO: Implement number of features for tile-coding. 
   ## 1. step
   ## 2. reset
   ## 3. close

   ### observation
   ## 1. action space
   ## 2. observation space
   ## 3. reward range 


   def __init__(self):
        super().__init__()

   ### Implementation for High-level WM keepaway functions
   ##TODO: Maybe put this in a separate file

#    def is_ball_in_field(self):
#        """
#        returns True if position is in the field
#        """
#        return self.ball().pos_valid()
   

   
       

       
       

    

    



