from sqlalchemy import func
from sqlalchemy.sql import and_

from prospects.markdown import Document, Table, List
from prospects.models import Player, Draft, StatLine


def generate_draft(db, year):
    with db.session() as sess:
        players = (
            sess.query(Player)
            .filter(sess.query(Draft).filter(and_(Draft.year == year, Draft.player_id == Player.id)).exists())
            .order_by(sess.query(func.min(Draft.overall)).filter(Draft.player_id == Player.id))
        )

        doc = Document()

        for player in players:
            drafts = list(sorted(player.drafts, key=lambda d: d.year))
            doc.add(List(items=["{} #{}".format(player.name, drafts[0].overall)]))

            t = Table()
            t.add_columns("Name", "Age", "Birthday", "Nation", "Position", "Shoots", "Height", "Weight")
            t.add_row(
                player.name,
                player.age,
                player.birthday,
                player.nation,
                player.position,
                player.shoots,
                player.height,
                player.weight,
            )
            doc.add(t)

            stats = player.stats.filter(StatLine.season_end == year).order_by(StatLine.is_tournament)

            t = Table()
            t.add_columns("Tournament", "Team Name", "League Name", "GP", "Goals", "Assists", "Points", "+/-")

            for stat in stats:
                t.add_row(
                    "\u2611" if stat.is_tournament else "\u2610",
                    stat.team_name,
                    stat.league_name,
                    stat.games,
                    stat.goals,
                    stat.assists,
                    stat.points,
                    stat.plus_minus,
                )

            doc.add(t)

        print(doc.render())
