from .dto import Position, Shoots
from .markdown import Document, Table, H2, Link


def render(data, age_cutoff=26.0):
    lw = []
    center = []
    rw = []
    lhd = []
    rhd = []
    goalie = [goalie for goalie in data['goalies'] if goalie.age_frac <= age_cutoff]

    for skater in data['skaters']:
        if any(stats.games >= 10 for stats in skater.stats) and skater.age_frac <= age_cutoff:
            if Position.DEFENSE in skater.positions:
                if skater.shoots == Shoots.LEFT:
                    lhd.append(skater)
                else:
                    rhd.append(skater)

            if Position.LEFT_WING in skater.positions or Position.WING in skater.positions:
                lw.append(skater)
            if Position.RIGHT_WING in skater.positions or Position.WING in skater.positions:
                rw.append(skater)
            if Position.CENTER in skater.positions:
                center.append(skater)

    def generate_skater_table(players):
        t = Table()
        t.add_columns("Player", "Age", "Height", "Weight", "League", "Games",
                      "Goals", "Assists", "Points", "PPG", "Drafted", "PT/82")
        for player in players:
            stats = player.get_skater_stats()
            t.add_row(Link(player.name, player.url),
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
                      player.get_points_translation() or "")
        return t

    def generate_goalie_table(goalies):
        t = Table()
        t.add_columns("Player", "Age", "Height", "Weight", "League", "Games", "GAA", "SV%", "Drafted")
        for player in goalies:
            stats = player.get_goalie_stats()
            t.add_row(Link(player.name, player.url),
                      player.age_frac,
                      player.height_imp,
                      player.weight_imp,
                      stats.league_name,
                      stats.games,
                      stats.goal_average,
                      stats.save_percent,
                      player.draft.short if player.draft is not None else "")
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
