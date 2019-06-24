import logging
import re
from datetime import datetime, timedelta

from bs4 import BeautifulSoup
from bs4.element import Tag

from .dto import Position, Shoots
from .models import Draft, StatLine, Player
from .http import CachingClient

RE_PLAYER_PATTERN = re.compile(r"(.+)\s+\(([^\)]+)\)")
RE_SEASON_PATTERN = re.compile(r"(\d\d\d\d)\-(\d\d)")

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
    begin = int(match.group(1))
    return begin, begin + 1


def try_parse(val, ctor):
    try:
        return ctor(val)
    except ValueError:
        return None


def is_tournament(stats_row):
    return "team-continent-INT" in stats_row.get("class")


def is_injured(stats_row):
    return len(stats_row.find_all("i", class_="fa-injured")) > 0


def parse_skater_stats(seasons, player):
    for row in seasons:
        season_str = get_td_class_text(row, "season")
        if season_str:
            season_begin, season_end = parse_season(season_str)

        if season_end > datetime.now().year:
            continue

        stats = StatLine()
        stats.season_begin = season_begin
        stats.season_end = season_end
        stats.team_name = get_td_class_text(row, "team")
        stats.league_name = get_td_class_text(row, "league")
        stats.games = get_td_class_int(row, "gp")
        stats.is_tournament = is_tournament(row)

        stats.goals = get_td_class_int(row, "g")
        stats.assists = get_td_class_int(row, "a")
        stats.plus_minus = get_td_class_int(row, "pm")

        player.stats.append(stats)


def parse_goalie_stats(seasons, player):
    for row in seasons:
        season_str = get_td_class_text(row, "season")
        if season_str:
            season_begin, season_end = parse_season(season_str)

        if season_end > datetime.now().year:
            continue

        stats = StatLine()
        stats.season_begin = season_begin
        stats.season_end = season_end
        stats.team_name = get_td_class_text(row, "team")
        stats.league_name = get_td_class_text(row, "league")
        stats.games = get_td_class_int(row, "gp")
        stats.is_tournament = is_tournament(row)

        stats.goal_average = try_parse(get_td_class_text(row, "gaa"), float)
        stats.save_percent = try_parse(get_td_class_text(row, "svp"), float)

        player.stats.append(stats)


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


def parse_birthday(text):
    return datetime.strptime(text, "%b %d, %Y").date()


RE_DRAFT_STR = re.compile(r"(\d{4}) round (\d+) #(\d+) overall by (.+)")


def draft_from_str(draft_str):
    match = RE_DRAFT_STR.match(draft_str)
    if not match:
        raise ValueError("invalid draft string")
    return Draft(year=int(match.group(1)), round=int(match.group(2)), overall=int(match.group(3)), team=match.group(4))


class Scraper:
    def __init__(self):
        self._client = CachingClient(cache_duration=timedelta(hours=24), delay=5)

    def parse_player(self, url, name=None, position=None):
        logger.info("Processing player at %s", url)

        doc = create_dom(self._client.get(url).text)
        info_table = doc.find("div", class_="table-view")
        table_div, extra_div = info_table.find_all("div", recursive=False)
        left_side, right_side = table_div.find_all("div", recursive=False)

        if name is None:
            name = get_element_text(doc.find(class_="plytitle").find_all(text=True, recursive=False))

        player = Player(name=name)

        sections = extra_div.find_all("li")

        for section in sections:
            first, second, *_rest = section.find_all("div")
            if "drafted" in get_element_text(first).lower():
                player.drafts.append(draft_from_str(get_element_text(second)))
        scouting_report = get_element_text(doc.find("div", class_="dtl-txt"))

        rows = left_side.find_all("li")

        player.birthday = parse_birthday(parse_data_col(rows[0]))
        player.birthplace = parse_data_col(rows[2])
        player.nation = parse_data_col(rows[3])

        rows = right_side.find_all("li")

        player.height = parse_data_col(rows[1])
        player.weight = parse_data_col(rows[2])
        player.shoots = Shoots.from_str(parse_data_col(rows[3]))
        if position is None:
            positions_str = parse_data_col(rows[0])
            position = pick_best_position(positions_str)
        player.position = position

        player.url = url
        player.scouting_report = scouting_report

        seasons = doc.find("table", class_="player-stats").find("tbody").find_all("tr")

        if Position.GOALIE != position:
            parse_skater_stats(seasons, player)
        else:
            parse_goalie_stats(seasons, player)

        return player

    def parse_depth_chart(self, db, url):
        doc = create_dom(self._client.get(url).text)

        table = doc.find("table", class_="depth-chart")
        rows = []
        for body in table.find_all("tbody"):
            for row in body.find_all("tr"):
                rows.append(row)

        players = []
        current_position = None

        with db.session() as sess:
            for row in rows:
                if "title" in row.attrs.get("class", []):
                    current_position = Position.from_str(get_element_text(row))
                else:
                    player_str = get_element_text(row.find("td", class_="player"))
                    name, _ = parse_player_string(player_str)
                    url = row.find("a").attrs["href"]
                    player = self.parse_player(url, name, current_position)
                    sess.merge(player)
                    sess.commit()

        return players


__all__ = ["Scraper"]
