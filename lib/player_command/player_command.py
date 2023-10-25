from enum import Enum, unique, auto

from pyrusgeom.angle_deg import AngleDeg
from pyrusgeom.vector_2d import Vector2D


@unique
class CommandType(Enum):
    # connection commands
    INIT = auto()  # ! < server connection command
    RECONNECT = auto()  # ! < server reconnection command
    BYE = auto()  # ! < server disconnection command

    # base commands
    MOVE = auto()
    DASH = auto()
    TURN = auto()
    KICK = auto()
    CATCH = auto()
    TACKLE = auto()
    NECK = auto()

    # support commands
    TURN_NECK = auto()
    CHANGE_FOCUS = auto()
    CHANGE_VIEW = auto()
    SAY = auto()
    POINTTO = auto()
    ATTENTIONTO = auto()

    # mode change commands
    CLANG = auto()
    EAR = auto()

    # other commands
    SENSE_BODY = auto()
    SCORE = auto()
    COMPRESSION = auto()

    # synch_mode command
    DONE = auto()

    ILLEGAL = auto()


class PlayerCommand:
    def type(self):
        pass

    def str(self):
        return ""

    # def name(self):
    #     pass


class PlayerInitCommand(PlayerCommand):
    def __init__(self, team_name: str, version: float = None, golie: bool = False):
        self._team_name = team_name
        self._version = version
        self._goalie = golie

    def str(self):
        return (
            f"(init {self._team_name}"
            + (f" (version {self._version})" if self._version >= 4 else "")
            + ("(goalie)" if self._goalie else "")
            + ")"
        )

    def type(self):
        return CommandType.INIT


class PlayerReconnectCommand(PlayerCommand):
    def __init__(self, team_name: str, unum: int):
        self._team_name = team_name
        self._unum = unum

    def str(self):
        return f"(reconnect {self._team_name} {self._unum})"

    def type(self):
        return CommandType.RECONNECT


class PlayerByeCommand:
    def __init__(self):
        pass

    def str(self):
        return "(bye)"

    def type(self):
        return CommandType.BYE


class PlayerMoveBallCommand(PlayerCommand):
    def __init__(self, pos: Vector2D, vel: Vector2D = None):
        super().__init__()
        self._pos = pos
        self._vel = vel

    def type(self):
        return CommandType.MOVE

    def str(self):
        if self._vel is None:
            return f"(move (ball) {self._pos.x()} {self._pos.y()})"
        return (
            f"(move (ball) {self._pos.x()} {self._pos.y()}"
            f" 0 {self._vel.x()} {self._vel.y()})"
        )


class PlayerMovePlayerCommand(PlayerCommand):
    def __init__(
        self,
        teamname: str,
        unum: int,
        pos: Vector2D,
        angle: float = None,
        vel: Vector2D = None,
    ):
        super().__init__()
        self._teamname = teamname.strip('"')
        self._unum = unum
        self._pos = pos
        self._angle = angle
        self._vel = vel

    def type(self):
        return PlayerCommand.Type.MOVE

    def str(self):
        if not self.check():
            return ""

        if self._angle is None:
            return (
                f"(move (player {self._teamname} {self._unum}) "
                f"{self._pos.x()} {self._pos.y()})"
            )
        else:
            if self._vel is None:
                return (
                    f"(move (player {self._teamname} {self._unum})"
                    f" {self._pos.x()} {self._pos.y()} {self._angle})"
                )
            else:
                return (
                    f"(move (player {self._teamname} {self._unum}) "
                    f"{self._pos.x():.2f} {self._pos.y():.2f} {self._angle:.2f}"
                    f" {self._vel.x():.2f} {self._vel.y():.2f})"
                )

    def check(self):
        if not 0 < self._unum < 12:
            log.os_log().error("Illegal uniform number")
            return False
        return True
