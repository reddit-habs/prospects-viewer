import enum

from attr import attrs, attrib


@attrs(slots=True)
class Team:
    name = attrib()
    league = attrib()


class Position(enum.Enum):
    CENTER = 1
    LEFT_WING = 2
    RIGHT_WING = 3
    WING = 4
    DEFENSE = 5
    GOALIE = 6

    @classmethod
    def from_str(cls, pos):
        pos = pos.lower()
        try:
            return STR_TO_PLAYER_POSITION[pos]
        except KeyError:
            raise ValueError("unknown position string: " + pos)


STR_TO_PLAYER_POSITION = dict(c=Position.CENTER, w=Position.WING, lw=Position.LEFT_WING,
                              rw=Position.RIGHT_WING, d=Position.DEFENSE, g=Position.GOALIE)


@attrs(slots=True)
class Stats:
    name = attrib()
    teams = attrib()
    positions = attrib()
    games = attrib()
    info = attrib()


@attrs(slots=True)
class SkaterStats(Stats):
    goals = attrib()
    assists = attrib()
    plus_minus = attrib()


@attrs(slots=True)
class GoalieStats(Stats):
    goal_average = attrib()
    save_percent = attrib()


class Shoots(enum.Enum):
    LEFT = 1
    RIGHT = 2


@attrs(slots=True)
class Info:
    birthday = attrib()
    age = attrib()
    nation = attrib()
    birthplace = attrib()

    shoots = attrib()
    height = attrib()
    weight = attrib()

    url = attrib()
    draft = attrib()
