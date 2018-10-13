import enum
import re

from attr import attrib, attrs

import arrow


class Position(enum.Enum):
    CENTER = 1
    LEFT_WING = 2
    RIGHT_WING = 3
    WING = 4
    DEFENSE = 5
    GOALIE = 6
    FORWARD = 7

    @classmethod
    def from_str(cls, pos):
        pos = pos.lower()
        try:
            return STR_TO_PLAYER_POSITION[pos]
        except KeyError:
            raise ValueError("unknown position string: " + pos)

    def to_str(self):
        for key, val in STR_TO_PLAYER_POSITION.items():
            if self == val:
                return key.upper()
        raise ValueError


STR_TO_PLAYER_POSITION = dict(
    c=Position.CENTER,
    w=Position.WING,
    f=Position.FORWARD,
    lw=Position.LEFT_WING,
    rw=Position.RIGHT_WING,
    d=Position.DEFENSE,
    g=Position.GOALIE,
)


class Shoots(enum.Enum):
    LEFT = 1
    RIGHT = 2

    @classmethod
    def from_str(cls, shoots):
        shoots = shoots.lower()
        if shoots == "l":
            return Shoots.LEFT
        elif shoots == "r":
            return Shoots.RIGHT
        else:
            raise ValueError("unknown shoots string: " + shoots)


@attrs(slots=True, kw_only=True)
class Player:
    name = attrib()
    position = attrib()

    birthday = attrib()
    age = attrib()
    nation = attrib()
    birthplace = attrib()

    shoots = attrib()
    height = attrib()
    weight = attrib()

    url = attrib()
    draft = attrib()
    scouting_report = attrib()

    stats = attrib(factory=list)

    height_imp = attrib(init=False)
    weight_imp = attrib(init=False)
    age_frac = attrib(init=False)

    def __attrs_post_init__(self):
        self.height_imp = self.height.split("/")[0].strip()
        self.weight_imp = self.weight.split("/")[0].strip()

        birthday = arrow.get(self.birthday, "MMM DD, YYYY")
        delta = arrow.now() - birthday
        self.age_frac = round(delta.days / 365.242199, 1)


@attrs(slots=True, kw_only=True)
class Stats:
    season_end = attrib()  # year that represents when the season ended
    team_name = attrib()
    league_name = attrib()
    games = attrib()
    tournament = attrib(default=False)
    injured = attrib(default=False)


@attrs(slots=True, kw_only=True)
class SkaterStats(Stats):
    goals = attrib()
    assists = attrib()
    plus_minus = attrib()

    @property
    def points(self):
        return self.goals + self.assists

    @property
    def points_per_game(self):
        if self.games == 0:
            return 0
        else:
            return round(self.points / self.games, 2)

    def substract(self, other):
        return SkaterStats(
            season_end=self.season_end,
            team_name=self.team_name,
            league_name=self.league_name,
            tournament=self.tournament,
            injured=self.injured,
            games=self.games - other.games,
            goals=self.goals - other.goals,
            assists=self.assists - other.assists,
            plus_minus=self.plus_minus - other.plus_minus,
        )


@attrs(slots=True, kw_only=True)
class GoalieStats(Stats):
    goal_average = attrib()
    save_percent = attrib()


RE_DRAFT_STR = re.compile(r"(\d{4}) round (\d+) #(\d+) overall by (.+)")


@attrs(slots=True, kw_only=True)
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
        return Draft(
            year=int(match.group(1)), round=int(match.group(2)), overall=int(match.group(3)), team=match.group(4)
        )

    @property
    def short(self):
        return "{} #{}".format(self.year, self.overall)
