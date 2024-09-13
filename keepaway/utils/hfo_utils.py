
from pyrusgeom.geom_2d import *
from keepaway.lib.action.turn_to_ball import TurnToBall
from keepaway.lib.rcsc.server_param import ServerParam

from keepaway.utils.hfo_actions import *
from keepaway.utils.tools import Tools
from pyrusgeom.soccer_math import *
from pyrusgeom.vector_2d import Vector2D
from pyrusgeom.geom_2d import *
from keepaway.lib.debug.debug import log
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from keepaway.lib.player.world_model import WorldModel
    from keepaway.lib.player.object_player import PlayerObject


class OffenseAgent:
    """Offense agent."""

    @staticmethod
    def offense_with_ball(
        wm: "WorldModel", agent: "PlayerAgent", actions, last_action_time
    ):
        """
            This method implements the keeper with ball.
           
            
            Args:
                wm: WorldModel
                agent: PlayerAgent
                actions: list
                last_action_time: float
        """

        action = actions[wm.self().unum() - 1]
        OffenseAgent.interpret_offensive_action(wm, agent, action)


    
    @staticmethod
    def interpret_offensive_action(wm: "WorldModel", agent, action):
        """
            This method interprets the keeper action.
            Args:
                wm: WorldModel
                agent: PlayerAgent
                action: int
        """

        # if action == 0:
        #     # return HoldBall().execute(agent)
        #     return 
        # else:
        #     k = wm.teammates_from_ball()
        #     if len(k) > 0:
        #         for tm in k:
        #             if tm.unum() == action:
        #                 temp_pos = tm.pos()
        #                 return agent.do_kick_to(tm, 1.5)
        # return

class DefenseAgent:
    """Defense agent."""

    @staticmethod
    def defense_with_ball(
        wm: "WorldModel", agent: "PlayerAgent", actions, last_action_time
    ):
        """
            This method implements the keeper with ball.
           
            
            Args:
                wm: WorldModel
                agent: PlayerAgent
                actions: list
                last_action_time: float
        """

        action = actions[wm.self().unum() - 1]
        DefenseAgent.interpret_defensive_action(wm, agent, action)

    @staticmethod
    def interpret_defensive_action(wm: "WorldModel", agent, action):
        """
            This method interprets the keeper action.
            Args:
                wm: WorldModel
                agent: PlayerAgent
                action: int
        """

        if action == 0:
            return do_random_defense_action(state, hfo_env)
        elif action == 1:
            return do_defense_action(state_vec=state, hfo_env=hfo_env,
                          num_opponents=numOpponents, num_teammates=numTeammates,
                          old_ball_pos_x=old_ball_pos_x, old_ball_pos_y=old_ball_pos_y,
                          num_times_overall=num_times_overall,
                          num_times_kickable=num_times_kickable,
                          misc_tracked=misc_tracked)