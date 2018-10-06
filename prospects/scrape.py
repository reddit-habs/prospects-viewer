import logging
import re

from bs4 import BeautifulSoup
from bs4.element import Tag

from .dto import Draft, GoalieStats, Player, Position, Shoots, SkaterStats
from .http import CachingClient

RE_PLAYER_PATTERN = re.compile(r"(.+)\s+\(([^\)]+)\)")
RE_SEASON_PATTERN = re.compile(r"(\d\d)\d\d\-(\d\d)")

logger = logging.getLogger(__name__)
client = CachingClient(delay=15)


def create_dom(html):
    return BeautifulSoup(html, "html.parser")


def get_element_text(elem):
    if elem is None:
        return ""
    if isinstance(elem, Tag):
        return "".join(elem.stripped_strings)
    else:
        return "".join((x.strip() for x in elem))


def get_td_class_text(row, cls):
    return get_element_text(row.find("td", class_=cls))


def get_td_class_int(row, cls, default=0):
    try:
        return int(get_td_class_text(row, cls))
    except ValueError:
        return default


def parse_player_string(player_str):
    match = RE_PLAYER_PATTERN.match(player_str)
    name = match.group(1)
    positions_str = match.group(2)
    positions = [Position.from_str(pos) for pos in re.split(r"[/\\]", positions_str)]
    return name, positions


def parse_season(season_str):
    match = RE_SEASON_PATTERN.match(season_str)
    centuries = match.group(1)
    decades = match.group(2)
    return int(centuries + decades)


def is_tournament(stats_row):
    return "team-continent-INT" in stats_row.get("class")


def parse_skater_stats(seasons, player):
    for row in seasons:
        season_str = get_td_class_text(row, "season")
        if season_str:
            last_season_end = parse_season(season_str)

        team_name = get_td_class_text(row, "team")
        league_name = get_td_class_text(row, "league")
        games = get_td_class_int(row, "gp")
        goals = get_td_class_int(row, "g")
        assists = get_td_class_int(row, "a")
        plus_minus = get_td_class_int(row, "pm")
        player.stats.append(
            SkaterStats(
                season_end=last_season_end,
                games=games,
                team_name=team_name,
                league_name=league_name,
                goals=goals,
                assists=assists,
                plus_minus=plus_minus,
                tournament=is_tournament(row),
            )
        )


def parse_goalie_stats(seasons, player):
    for row in seasons:
        season_str = get_td_class_text(row, "season")
        if season_str:
            last_season_end = parse_season(season_str)
        team_name = get_td_class_text(row, "team")
        league_name = get_td_class_text(row, "league")
        games = get_td_class_int(row, "gp")
        goal_average = get_td_class_text(row, "gaa")
        save_percent = get_td_class_text(row, "svp")
        player.stats.append(
            GoalieStats(
                season_end=last_season_end,
                games=games,
                team_name=team_name,
                league_name=league_name,
                goal_average=goal_average,
                save_percent=save_percent,
                tournament=is_tournament(row),
            )
        )


def parse_data_col(row):
    label, data = row.find_all("div")
    return get_element_text(data)


def pick_best_position(positions_str):
    positions = list(map(Position.from_str, positions_str.split("/")))
    if len(positions) == 1:
        return positions[0]
    else:
        if any((p == Position.CENTER for p in positions)):
            return Position.CENTER
        elif any((p == Position.GOALIE for p in positions)):
            return Position.GOALIE
        elif any((p == Position.DEFENSE for p in positions)):
            return Position.DEFENSE
        elif set(positions) == set([Position.LEFT_WING, Position.RIGHT_WING]):
            return Position.WING
        else:
            return Position.FORWARD


class Scraper:
    def __init__(self):
        self._client = CachingClient(delay=10)

    def parse_player(self, url, name=None, position=None):
        logger.info("Processing player at %s", url)

        doc = create_dom(self._client.get(url).text)
        info_table = doc.find("div", class_="table-view")
        table_div, extra_div = info_table.find_all("div", recursive=False)
        left_side, right_side = table_div.find_all("div", recursive=False)

        if name is None:
            name = get_element_text(doc.find(class_="plytitle").find_all(text=True, recursive=False))

        sections = extra_div.find_all("li")
        draft = None
        for section in sections:
            first, second, *_rest = section.find_all("div")
            if "drafted" in get_element_text(first).lower():
                draft = Draft.from_str(get_element_text(second))
                break
        scouting_report = get_element_text(doc.find("div", class_="dtl-txt"))

        rows = left_side.find_all("li")
        birthday = parse_data_col(rows[0])
        age = parse_data_col(rows[1])
        birthplace = parse_data_col(rows[2])
        nation = parse_data_col(rows[3])

        rows = right_side.find_all("li")
        height = parse_data_col(rows[1])
        weight = parse_data_col(rows[2])
        shoots = Shoots.from_str(parse_data_col(rows[3]))
        if position is None:
            positions_str = parse_data_col(rows[0])
            position = pick_best_position(positions_str)

        player = Player(
            name=name,
            position=position,
            birthday=birthday,
            age=age,
            nation=nation,
            birthplace=birthplace,
            shoots=shoots,
            height=height,
            weight=weight,
            url=url,
            draft=draft,
            scouting_report=scouting_report,
        )

        seasons = doc.find("table", class_="player-stats").find("tbody").find_all("tr")

        if Position.GOALIE != position:
            parse_skater_stats(seasons, player)
        else:
            parse_goalie_stats(seasons, player)

        return player

    def parse_depth_chart(self, url):
        doc = create_dom(self._client.get(url).text)

        table = doc.find("table", class_="depth-chart")
        rows = []
        for body in table.find_all("tbody"):
            for row in body.find_all("tr"):
                rows.append(row)

        players = []
        current_position = None
        for row in rows:
            if "title" in row.attrs.get("class", []):
                current_position = Position.from_str(get_element_text(row))
            else:
                player_str = get_element_text(row.find("td", class_="player"))
                name, _ = parse_player_string(player_str)
                url = row.find("a").attrs["href"]
                player = self.parse_player(url, name, current_position)
                players.append(player)

        return players


__all__ = ["Scraper"]
