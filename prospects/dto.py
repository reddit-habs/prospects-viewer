import enum
import re

import arrow
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

    @property
    def points(self):
        return self.goals + self.assists

    @property
    def points_per_game(self):
        return self.points / self.games


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

    @property
    def height_imp(self):
        return self.height.split('/')[0].strip()

    @property
    def weight_imp(self):
        return self.weight.split('/')[0].strip()

    @property
    def age_frac(self):
        birthday = arrow.get(self.birthday, 'MMM DD, YYYY')
        delta = arrow.now() - birthday
        return round(delta.days / 365.242199, 1)


RE_DRAFT_STR = re.compile(r"(\d{4}) round (\d+) #(\d+) overall by (.+)")


@attrs(slots=True)
class Draft:
    year = attrib()
    round = attrib()
    overall = attrib()
    team = attrib()

    @classmethod
    def from_str(cls, draft_str):
        match = RE_DRAFT_STR.match(draft_str)
        if not match:
            raise ValueError("invalid draft string")
        return Draft(year=int(match.group(1)),
                     round=int(match.group(2)),
                     overall=int(match.group(3)),
                     team=match.group(4))

    @property
    def short(self):
        return "{} #{}".format(self.year, self.overall)
