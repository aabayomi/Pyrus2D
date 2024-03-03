# pylint: disable=unnecessary-pass

""" Keep-away environment as close as possible to a GYM environment."""

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
from keepaway.lib.rcsc.server_param import ServerParam
from keepaway.lib.rcsc.types import HETERO_DEFAULT, UNUM_UNKNOWN, GameModeType
from pyrusgeom.soccer_math import *
from pyrusgeom.geom_2d import *
from keepaway.lib.player import WorldModel
from typing import List
import numpy as np
import copy

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import timeit

from absl import logging


DEBUG = True


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
    def __init__(self):
        super().__init__()

    def reset(self):
        """Reset the environment and return initial observation."""

        self._episode_start = timeit.default_timer()
        self._cumulative_reward = 0
        self._step_count = 0
        self._observation = None

        self._teammates: list[PlayerObject] = []
        self._opponents: list[PlayerObject] = []
        self._unknown_players: list[PlayerObject] = []

        # while not self._retrieve_observation():
        #     self._env.step()  ##
        
        return True

    # def step(self, action):

    #     """Run one timestep of the environment's dynamics."""

    #     assert self._env.state != GameState.game_done, (
    #     'Cant call step() once episode finished (call reset() instead)')
    #     assert self._env.state == GameState.game_running, (
    #         'reset() must be called before step()')
        
    #     action = [
    #         football_action_set.named_action_from_action_set(self._action_set, a)
    #         for a in action
    #     ]
    #     self._step_count += 1

    #     debug = {}
    #     debug['action'] = action
    #     action_index = 0

    #     num_keepers = len(self._teammates)

    #     for i in range(num_keepers):
    #         self._teammates[i].set_action(action[action_index])
    #         action_index += 1





    def _retrieve_observation(self):
        """
        Retrieve observation from the environment.
        this implementations the 13 state variables from the paper Peter Stone 2005.
        """

        info = self._env.get_info()

        result = {}
        self._convert_players_observation(result)

        self._observation = result
        self._step = info.step

        return info.is_in_play

    def _convert_players_observation(self, result):
        ## same as playerStateVars

        """Convert players observation from list to dictionary."""

        SP = ServerParam.i()
        keepaway_length = SP.keepaway_length()
        keepaway_width = SP.keepaway_width()
        keepaway_field_center = Vector2D(0, 0)  # assumed to at (0,0)
        ball_position = self.ball().pos()

        closest_keeper_ball = self.teammates_from_ball()[0]

        state_vars = []

        ## keeper to center distance
        for p in self._teammates:
            if p.pos_valid():
                dist = (p.pos() - keepaway_field_center).r()
                state_vars.append(dist)

        ## taker to center distance
        for p in self._opponents:
            if p.pos_valid():
                dist = (p.pos() - keepaway_field_center).r()
                state_vars.append(dist)

        ## keeper to keeper distance
        for p in self._teammates_from_self:
            if p.pos_valid():
                dist = p.dist_from_self()
                state_vars.append(dist)

        ## keeper to taker distance
        for p in self._opponents_from_self:
            if p.pos_valid():
                dist = p.dist_from_self()
                state_vars.append(dist)

        ## minimum distance between keeper and takers without ball
        for k in self._teammates:
            min_dist = 10000
            for t in self._opponents:
                if k == closest_keeper_ball:
                    continue
                else:
                    if t.pos_valid() and k.pos_valid():
                        dist = (k.pos() - t.pos()).r()
                        if dist < min_dist:
                            min_dist = dist
            state_vars.append(min_dist)
            min_dist = 10000

        ## minimum angle between closest keeper with ball and keepers without ball
        for k in self._teammates:
            min_angle = 10000
            if k == closest_keeper_ball:
                continue
            else:
                if k.pos_valid() and closest_keeper_ball.pos_valid():
                    angle = (k.pos() - closest_keeper_ball.pos()).th()
                    if angle < min_angle:
                        min_angle = angle
            state_vars.append(min_angle)

        result["state_vars"] = np.array(state_vars, dtype=np.float32)

    def observation(self):
        """Returns the current observation of the game."""

        assert (
            self._env.state == GameState.game_running
            or self._env.state == GameState.game_done
        ), "reset() must be called before observation()"

        return copy.deepcopy(self._observation)
