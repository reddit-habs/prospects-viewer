import gzip
import logging
import pickle
import random
import re
import sys
import time

import requests
from bs4 import BeautifulSoup

from .dto import GoalieStats, Info, Position, SkaterStats, Team

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
log.addHandler(logging.StreamHandler(sys.stdout))


RE_PLAYER_PATTERN = re.compile(r"(.+)\s*\(([^\)]+)\)")


class ThrottledHttpClient:

    def __init__(self, use_cache=False):
        self._use_cache = use_cache
        self._req_cache = {}
        if use_cache:
            self._read_cache()
        self._sess = requests.Session()
        self._sess.headers.update(
            {'user-agent': 'Mozilla/5.0 (Windows NT 6.3; Win64; x64; rv:60.0) Gecko/20100101 Firefox/60.0'})
        self._wait_until = time.monotonic()

    def _read_cache(self):
        try:
            with gzip.open('request.cache.gz', 'rb') as f:
                self._req_cache = pickle.load(f)
        except FileNotFoundError:
            pass

    def _write_cache(self):
        with gzip.open('request.cache.gz', 'wb') as f:
            pickle.dump(self._req_cache, f)

    def get(self, url, *args, **kwargs):
        cached_text = self._req_cache.get(url.lower())
        if self._use_cache and cached_text is not None:
            log.debug("loading url from cache %s", url)
            return cached_text

        log.debug("loading url from website %s", url)
        sleep_for = max(0, self._wait_until - time.monotonic())
        time.sleep(sleep_for)
        response = self._sess.get(url, *args, **kwargs)
        text = response.text

        if self._use_cache:
            log.debug("caching url %s", url)
            self._req_cache[url.lower()] = text
            self._write_cache()

        # set the clock delay until next request
        self._wait_until = time.monotonic() + random.uniform(3, 5)
        return text


client = ThrottledHttpClient(use_cache=True)


def create_dom(html):
    return BeautifulSoup(html, 'html.parser')


def get_element_text(elem):
    if elem is None:
        return ''
    return ''.join(elem.stripped_strings)


def get_td_class_text(row, cls):
    return get_element_text(row.find('td', class_=cls))


def get_td_class_int(row, cls):
    return int(get_td_class_text(row, cls))


def parse_player_string(player_str):
    match = RE_PLAYER_PATTERN.match(player_str)
    name = match.group(1)
    positions_str = match.group(2)
    positions = [Position.from_str(pos) for pos in positions_str.split("/")]
    return name, positions


def parse_skaters(skaters_table):
    rows = skaters_table.find('tbody').find_all('tr')
    last_player = None
    players = []
    for row in rows:
        teams = []

        player_str = get_td_class_text(row, 'player')
        team_name = get_td_class_text(row, 'team')
        league_name = get_td_class_text(row, 'league')

        if team_name and league_name:
            teams.append(Team(team_name, league_name))

        if not player_str:
            last_player.teams.extend(teams)
        else:
            name, positions = parse_player_string(player_str)

            log.info("processing skater %s", name)

            info_url = row.find('td', class_="player").find('a')['href']
            info = parse_info(info_url)

            games = get_td_class_int(row, 'gp')
            goals = get_td_class_int(row, 'g')
            assists = get_td_class_int(row, 'a')
            plus_minus = get_td_class_int(row, 'pm')

            last_player = SkaterStats(name=name, positions=positions, teams=teams, games=games,
                                      goals=goals, assists=assists, plus_minus=plus_minus,
                                      info=info)
            players.append(last_player)
    return players


def parse_goalies(goalies_table):
    rows = goalies_table.find('tbody').find_all('tr', class_=None)
    players = []
    for row in rows:
        name = get_td_class_text(row, 'player')
        log.info("processing goalie %s", name)

        info_url = row.find('td', class_="player").find('a')['href']
        info = parse_info(info_url)

        team_name = get_td_class_text(row, 'team')
        league_name = get_td_class_text(row, 'league')
        games = get_td_class_int(row, 'gp')
        goal_average = get_td_class_text(row, 'gaa')
        save_percent = get_td_class_text(row, 'svp')

        goalie = GoalieStats(name=name, teams=[Team(team_name, league_name)], positions=[Position.GOALIE],
                             games=games, info=info, goal_average=goal_average, save_percent=save_percent)
        players.append(goalie)
    return players


def parse_data_col(row):
    label, data = row.find_all('div')
    return get_element_text(data)


def parse_info(url):
    doc = create_dom(client.get(url))
    info_table = doc.find('div', class_='table-view')
    table_div, extra_div = info_table.find_all('div', recursive=False)
    left_side, right_side = table_div.find_all('div', recursive=False)

    sections = extra_div.find_all('li')
    draft = None
    for section in sections:
        first, second, *_rest = section.find_all('div')
        if 'drafted' in get_element_text(first).lower():
            draft = get_element_text(second)
            break

    rows = left_side.find_all('li')
    birthday = parse_data_col(rows[0])
    age = parse_data_col(rows[1])
    birthplace = parse_data_col(rows[2])
    nation = parse_data_col(rows[3])

    rows = right_side.find_all('li')
    height = parse_data_col(rows[1])
    weight = parse_data_col(rows[2])
    shoots = parse_data_col(rows[3])

    return Info(birthday=birthday, age=age, nation=nation, birthplace=birthplace,
                shoots=shoots, height=height, weight=weight, url=url, draft=draft)


def parse_players(url):
    doc = create_dom(client.get(url))
    skaters_table, goalies_table = doc.find_all('table', class_='in-the-system')
    skaters = parse_skaters(skaters_table)
    goalies = parse_goalies(goalies_table)
    return skaters, goalies


__all__ = ['parse_players']
