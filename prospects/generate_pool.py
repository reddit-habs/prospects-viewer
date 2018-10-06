from .dto import Position, Shoots, SkaterStats
from .markdown import Document, Table, H2, Link


def filter_player_func(player):
    stats = filter_stats(player)
    main_stats = max(stats, key=lambda s: s.games)
    return main_stats.league_name != "NHL"


def filter_player(players):
    return list(filter(filter_player_func, players))


def filter_stats(player, year=2018):
    return [stats for stats in player.stats if stats.season_end == year]


def get_skater_stats(skater):
    # merge stats by league
    # take league with most games played
    leagues = {}

    # merge stats by league
    for stats in filter_stats(skater):
        league = stats.league_name.upper()
        if league not in leagues:
            leagues[league] = SkaterStats(
                season_end=2018,
                team_name=[stats.team_name],
                league_name=league,
                games=stats.games,
                goals=stats.goals,
                assists=stats.assists,
                plus_minus=stats.plus_minus,
            )
        else:
            agg_stats = leagues[league]
            agg_stats.team_name.append(stats.team_name)
            agg_stats.games += stats.games
            agg_stats.goals += stats.goals
            agg_stats.assists += stats.assists
            agg_stats.plus_minus += stats.plus_minus

    # finalize team_name
    for stats in leagues.values():
        stats.team_name = " / ".join(stats.team_name)

    # pick best league by games
    return max(leagues.values(), key=lambda stats: stats.games)


def get_goalie_stats(goalie):
    return max(filter_stats(goalie), key=lambda stats: stats.games)


# https://twitter.com/robvollmannhl/status/866477120360402944
TRANSLATION_FACTOR = {
    "KHL": .74,
    "SHL": .58,
    "ALLSVENSKAN": .50,  # weaker end of the SHL
    "AHL": .47,
    "LIIGA": .43,
    "NLA": .43,
    "NCAA": .38,  # estimate based on conference average NCHC > H-EST > BIG-10 > ECAC
    "OHL": .30,
    "WHL": .29,
    "QMJHL": .25,
}


def get_points_translation(player):
    games = 0
    points = 0
    for stats in filter_stats(player):
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


def render(players):
    players = filter_player(players)

    lw = []
    center = []
    rw = []
    lhd = []
    rhd = []
    goalie = []

    for player in players:
        if Position.DEFENSE == player.position:
            if player.shoots == Shoots.LEFT:
                lhd.append(player)
            else:
                rhd.append(player)
        elif Position.LEFT_WING == player.position:
            lw.append(player)
        elif Position.RIGHT_WING == player.position:
            rw.append(player)
        elif Position.CENTER == player.position:
            center.append(player)
        elif Position.GOALIE == player.position:
            goalie.append(player)

    def generate_skater_table(players):
        t = Table()
        t.add_columns(
            "Player",
            "Age",
            "Height",
            "Weight",
            "League",
            "Games",
            "Goals",
            "Assists",
            "Points",
            "PPG",
            "Drafted",
            "PT/82",
        )
        for player in players:
            stats = get_skater_stats(player)
            t.add_row(
                Link(player.name, player.url),
                player.age_frac,
                player.height_imp,
                player.weight_imp,
                stats.league_name,
                stats.games,
                stats.goals,
                stats.assists,
                stats.points,
                stats.points_per_game,
                player.draft.short if player.draft is not None else "",
                get_points_translation(player) or "",
            )
        return t

    def generate_goalie_table(goalies):
        t = Table()
        t.add_columns(
            "Player",
            "Age",
            "Height",
            "Weight",
            "League",
            "Games",
            "GAA",
            "SV%",
            "Drafted",
        )
        for player in goalies:
            stats = get_goalie_stats(player)
            t.add_row(
                Link(player.name, player.url),
                player.age_frac,
                player.height_imp,
                player.weight_imp,
                stats.league_name,
                stats.games,
                stats.goal_average,
                stats.save_percent,
                player.draft.short if player.draft is not None else "",
            )
        return t

    doc = Document()

    doc.add(H2("Left wingers"))
    doc.add(generate_skater_table(lw))

    doc.add(H2("Centers"))
    doc.add(generate_skater_table(center))

    doc.add(H2("Right wingers"))
    doc.add(generate_skater_table(rw))

    doc.add(H2("Left-handed defensemen"))
    doc.add(generate_skater_table(lhd))

    doc.add(H2("Right-handed defensemen"))
    doc.add(generate_skater_table(rhd))

    doc.add(H2("Goaltenders"))
    doc.add(generate_goalie_table(goalie))

    return doc.render()


__all__ = ["render"]
