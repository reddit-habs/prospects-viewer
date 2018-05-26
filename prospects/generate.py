from .dto import Position
from .markdown import Document, Table, H2, Link


def render(data):
    lw = []
    center = []
    rw = []
    lhd = []
    rhd = []
    goalie = data['goalies']

    for skater in data['skaters']:
        if skater.games >= 10:
            if Position.DEFENSE in skater.positions:
                if skater.info.shoots == 'L':
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
                      "Goals", "Assists", "Points", "PPG", "Drafted")
        for player in players:
            leagues = '/'.join(set(team.league for team in player.teams))
            t.add_row(Link(player.name, player.info.url),
                      player.info.age_frac,
                      player.info.height_imp,
                      player.info.weight_imp,
                      leagues,
                      player.games,
                      player.goals,
                      player.assists,
                      player.points,
                      str(round(player.points_per_game, 2)),
                      player.info.draft.short if player.info.draft is not None else "")
        return t

    def generate_goalie_table(goalies):
        t = Table()
        t.add_columns("Player", "Age", "Height", "Weight", "League", "Games", "GAA", "SV%", "Drafted")
        for player in goalies:
            leagues = '/'.join(set(team.league for team in player.teams))
            t.add_row(Link(player.name, player.info.url),
                      player.info.age_frac,
                      player.info.height_imp,
                      player.info.weight_imp,
                      leagues,
                      player.games,
                      player.goal_average,
                      player.save_percent,
                      player.info.draft.short if player.info.draft is not None else "")
        return t

    doc = Document()

    doc.add(H2("Left winger"))
    doc.add(generate_skater_table(lw))

    doc.add(H2("Centers"))
    doc.add(generate_skater_table(center))

    doc.add(H2("Right winger"))
    doc.add(generate_skater_table(rw))

    doc.add(H2("Left-handed defensemen"))
    doc.add(generate_skater_table(lhd))

    doc.add(H2("Right-handed defensemen"))
    doc.add(generate_skater_table(rhd))

    doc.add(H2("Goaltenders"))
    doc.add(generate_goalie_table(goalie))

    return doc.render()
