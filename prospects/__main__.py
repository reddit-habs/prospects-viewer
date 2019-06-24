import logging

import click

from prospects.scrape import Scraper
from prospects.sqlite import SqliteDB
from prospects.models import Base
from prospects.generate import generate_draft

logging.basicConfig(level=logging.DEBUG)


@click.group()
def cli():
    pass


@cli.command(help="scrape info from the depth chart of a team")
@click.argument("url", required=True)
def scrape(url):
    db = SqliteDB("players.db", Base.metadata)
    scraper = Scraper()
    scraper.parse_depth_chart(db, url)


@cli.command(help="scrape info from the depth chart of a team")
@click.argument("year", type=int, required=True)
def draft(year):
    db = SqliteDB("players.db", Base.metadata)
    generate_draft(db, year)


if __name__ == "__main__":
    cli(prog_name="prospects")
