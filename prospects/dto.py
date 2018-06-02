import enum
import re

import arrow
from attr import attrs, attrib


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


TRANSLATION_FACTOR = {
    'KHL': .75,
    'SHL': .60,
    'AHL': .50,
    'LIIGA': .45,
    'NLA': .45,
    'NCAA': .35,
    'OHL': .30,
    'WHL': .30,
    'QMJHL': .30,
}


@attrs(slots=True)
class Player:
    name = attrib()
    positions = attrib()

    birthday = attrib()
    age = attrib()
    nation = attrib()
    birthplace = attrib()

    shoots = attrib()
    height = attrib()
    weight = attrib()

    url = attrib()
    draft = attrib()

    stats = attrib(factory=list)

    height_imp = attrib(init=False)
    weight_imp = attrib(init=False)
    age_frac = attrib(init=False)

    def __attrs_post_init__(self):
        self.height_imp = self.height.split('/')[0].strip()
        self.weight_imp = self.weight.split('/')[0].strip()

        birthday = arrow.get(self.birthday, 'MMM DD, YYYY')
        delta = arrow.now() - birthday
        self.age_frac = round(delta.days / 365.242199, 1)

    def get_skater_stats(self):
        # merge stats by league
        # take league with most games played
        leagues = {}

        # merge stats by league
        for stats in self.stats:
            league = stats.league_name.upper()
            if league not in leagues:
                leagues[league] = SkaterStats(team_name=[stats.team_name],
                                              league_name=league,
                                              games=stats.games,
                                              goals=stats.goals,
                                              assists=stats.assists,
                                              plus_minus=stats.plus_minus)
            else:
                agg_stats = leagues[league]
                agg_stats.team_name.append(stats.team_name)
                agg_stats.games += stats.games
                agg_stats.goals += stats.goals
                agg_stats.assists += stats.assists
                agg_stats.plus_minus += stats.plus_minus

        # finalize team_name
        for stats in leagues.values():
            stats.team_name = ' / '.join(stats.team_name)

        # pick best league by games
        return max(leagues.values(), key=lambda stats: stats.games)

    def get_goalie_stats(self):
        return max(self.stats, key=lambda stats: stats.games)

    def get_points_translation(self):
        games = 0
        points = 0
        for stats in self.stats:
            league = stats.league_name.upper()
            factor = TRANSLATION_FACTOR.get(league)
            if factor is None:
                continue
            points += factor * stats.points
            games += stats.games
        if games == 0:
            return None
        else:
            return round(points / games * 82, 1)


@attrs(slots=True)
class Stats:
    team_name = attrib()
    league_name = attrib()
    games = attrib()


@attrs(slots=True)
class SkaterStats(Stats):
    goals = attrib()
    assists = attrib()
    plus_minus = attrib()

    points = attrib(init=False)
    points_per_game = attrib(init=False)

    def __attrs_post_init__(self):
        self.points = self.goals + self.assists
        self.points_per_game = round(self.points / self.games, 2)


@attrs(slots=True)
class GoalieStats(Stats):
    goal_average = attrib()
    save_percent = attrib()


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
