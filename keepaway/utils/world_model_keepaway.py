## Duplicate of world_model_keepaway.py

from turtle import pos
from keepaway.lib.action.intercept_table import InterceptTable
from keepaway.lib.debug.debug import log
from keepaway.lib.player.localizer import Localizer
from keepaway.lib.messenger.messenger import Messenger
from keepaway.lib.messenger.messenger_memory import MessengerMemory
from keepaway.lib.player.object_player import *
from keepaway.lib.player.object_ball import *
from keepaway.lib.parser.parser_message_fullstate_world import FullStateWorldMessageParser
from keepaway.lib.player.object_self import SelfObject
from keepaway.lib.player.sensor.body_sensor import SenseBodyParser
from keepaway.lib.player.sensor.visual_sensor import SeeParser
from keepaway.lib.player.view_area import ViewArea
from keepaway.lib.player_command.player_command_support import PlayerAttentiontoCommand
from keepaway.lib.rcsc.game_mode import GameMode
from keepaway.lib.rcsc.game_time import GameTime
from keepaway.lib.rcsc.types import HETERO_DEFAULT, UNUM_UNKNOWN, GameModeType
from pyrusgeom.soccer_math import *
from keepaway.lib.player import WorldModel
from typing import List


DEBUG =True


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from keepaway.lib.player.action_effector import ActionEffector
    

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
   