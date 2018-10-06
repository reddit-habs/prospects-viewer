from .dto import Position, Shoots
from .markdown import H2, Document, HorizontalRule, Table

SORT_ORDER_POS = ["C", "LW", "RW", "W", "F", "LD", "RD", "G"]


def sort_player_pos_name(p):
    player, pos, url = p
    return (SORT_ORDER_POS.index(pos), player.name)


def render(players_now, players_then):
    doc = Document()

    skater_list = []
    goalie_list = []

    for url, player in players_now.items():
        if player.position == Position.DEFENSE:
            if player.shoots == Shoots.LEFT:
                skater_list.append((player, "LD", url))
            else:
                skater_list.append((player, "RD", url))
        elif player.position == Position.GOALIE:
            goalie_list.append((player, "G", url))
        else:
            skater_list.append((player, player.position.to_str(), url))

    skater_list.sort(key=sort_player_pos_name)

    skaters_table = Table()
    skaters_table.add_columns("Position", "Name", "Age", "League", "GP", "G", "A", "Pts", "+/-", "Draft")

    for player, pos, url in skater_list:
        stats = [stats for stats in player.stats if stats.season_end == 2019 and not stats.tournament]
        for idx, srow in enumerate(stats):
            if idx == 0:
                skaters_table.add_row(
                    pos,
                    player.name,
                    "{:.1f}".format(player.age_frac),
                    srow.league_name,
                    srow.games,
                    srow.goals,
                    srow.assists,
                    srow.goals + srow.assists,
                    srow.plus_minus,
                    player.draft.short if player.draft else "-",
                )
            else:
                skaters_table.add_row(
                    "-",
                    "-",
                    "-",
                    srow.league_name,
                    srow.games,
                    srow.goals,
                    srow.assists,
                    srow.goals + srow.assists,
                    srow.plus_minus,
                    "-",
                )

    goalie_table = Table()
    goalie_table.add_columns("Position", "Name", "Age", "League", "GP", "SV%", "GAA", "Draft")

    for player, pos, url in goalie_list:
        stats = [stats for stats in player.stats if stats.season_end == 2019 and not stats.tournament]
        for idx, srow in enumerate(stats):
            if idx == 0:
                goalie_table.add_row(
                    pos,
                    player.name,
                    "{:.1f}".format(player.age_frac),
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

    doc.add(H2("Skaters"))
    doc.add(skaters_table)
    doc.add(HorizontalRule())
    doc.add(H2("Goalies"))
    doc.add(goalie_table)
    return doc.render()


__all__ = ["render"]
