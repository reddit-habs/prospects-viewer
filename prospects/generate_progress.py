import re

from .dto import Position, Shoots
from .markdown import H1, H2, Document, Link, Table

SORT_ORDER_POS = ["C", "LW", "RW", "W", "F", "LD", "RD", "G"]


def sort_player_pos_name(p):
    player, pos, url = p
    return (SORT_ORDER_POS.index(pos), player.name)


def lookup_prev_stats(prev_data, url, stats_now):
    player = prev_data[url]
    s = [
        s
        for s in player.stats
        if s.season_end == stats_now.season_end
        and s.league_name == stats_now.league_name
        and s.team_name == stats_now.team_name
    ]
    if len(s) > 0:
        return s[0]
    else:
        return None


def get_player_name(player, stats):
    if stats.injured:
        return "{} \N{HOSPITAL}".format(player.name)
    else:
        return player.name


def get_team_name(team_name):
    return re.sub(r"“(\w+)”", r" (\1)", team_name)


def make_skater_table(skater_list, prev_data=None):
    skaters_table = Table()
    skaters_table.add_columns("Position", "Name", "Age", "Team", "League", "GP", "G", "A", "Pts", "PPG", "+/-", "Draft")

    for player, pos, url in skater_list:
        stats = [stats for stats in player.stats if stats.season_end == 2019 and not stats.tournament]
        for idx, srow in enumerate(stats):

            if prev_data is not None and url in prev_data:
                prev = lookup_prev_stats(prev_data, url, srow)
                if prev is not None:
                    srow = srow.substract(prev)

            if prev_data is not None and srow.points == 0:
                continue

            skaters_table.add_row(
                pos,
                Link(get_player_name(player, srow), player.url),
                "{:.1f}".format(player.age_frac),
                get_team_name(srow.team_name),
                srow.league_name,
                srow.games,
                srow.goals,
                srow.assists,
                srow.points,
                srow.points_per_game,
                srow.plus_minus,
                player.draft.short if player.draft else "-",
            )
    return skaters_table


def make_goalie_table(goalie_list):
    goalie_table = Table()
    goalie_table.add_columns("Position", "Name", "Age", "Team", "League", "GP", "SV%", "GAA", "Draft")

    for player, pos, url in goalie_list:
        stats = [stats for stats in player.stats if stats.season_end == 2019 and not stats.tournament]
        for idx, srow in enumerate(stats):
            if idx == 0:
                goalie_table.add_row(
                    pos,
                    get_player_name(player, srow),
                    "{:.1f}".format(player.age_frac),
                    get_team_name(srow.team_name),
                    srow.league_name,
                    srow.games,
                    srow.save_percent,
                    srow.goal_average,
                    player.draft.short if player.draft else "-",
                )
            else:
                goalie_table.add_row(
                    "-",
                    "-",
                    "-",
                    srow.league_name,
                    srow.games,
                    srow.save_percent,
                    srow.goal_average,
                    player.draft.short if player.draft else "-",
                )

    return goalie_table


def render(players_now, players_then):
    doc = Document()

    forwards_list = []
    defense_list = []
    goalie_list = []

    for url, player in players_now.items():
        if player.position == Position.DEFENSE:
            if player.shoots == Shoots.LEFT:
                defense_list.append((player, "LD", url))
            else:
                defense_list.append((player, "RD", url))
        elif player.position == Position.GOALIE:
            goalie_list.append((player, "G", url))
        else:
            forwards_list.append((player, player.position.to_str(), url))

    forwards_list.sort(key=sort_player_pos_name)
    defense_list.sort(key=sort_player_pos_name)
    goalie_list.sort(key=sort_player_pos_name)

    doc.add(H1("Stats this week"))

    doc.add(H2("Forwards"))
    doc.add(make_skater_table(forwards_list, players_then))

    doc.add(H2("Defensemen"))
    doc.add(make_skater_table(defense_list, players_then))

    doc.add(H1("Seasons totals"))

    doc.add(H2("Forwards"))
    doc.add(make_skater_table(forwards_list))

    doc.add(H2("Defensemen"))
    doc.add(make_skater_table(defense_list))

    doc.add(H2("Goalies"))
    doc.add(make_goalie_table(goalie_list))
    return doc.render()


__all__ = ["render"]
