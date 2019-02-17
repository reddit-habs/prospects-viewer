import enum
import json
import logging
import pickle
from pathlib import Path

import attr
import click

from . import generate_pool, generate_progress
from .scrape import Scraper
from .storage import Storage

logging.basicConfig(level=logging.DEBUG)


class AttrsJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if attr.has(o.__class__):
            return attr.asdict(o)
        elif isinstance(o, enum.Enum):
            return o.name
        else:
            super().default(o)


@click.group()
def cli():
    pass


@cli.command(help="generate a full report on a team's prospects")
@click.argument("url", required=False)
@click.option("--pickle", "pickle_path", default=None, help="Path to pickle dump")
@click.option("--json", "json_path", default=None, help="Path to json dump")
@click.option("-u", "--use-pickle", "use_pickle", default=None, help="Use saved pickle")
def pool(url, pickle_path, json_path, use_pickle):
    if use_pickle is not None:
        players = pickle.loads(Path(use_pickle).read_bytes())
    else:
        if url is None:
            print("Error: missing url")
            exit()
        scraper = Scraper()
        players = scraper.parse_depth_chart(url)

    if pickle_path:
        Path(pickle_path).write_bytes(pickle.dumps(players))

    if json_path:
        Path(json_path).write_text(AttrsJSONEncoder(indent=2).encode(players))

    print(generate_pool.render(players))


@cli.command(help="generate a progress report on players")
@click.option("--links", "links", required=True, help="path to a file with elite prospects URLs separated by a line")
@click.option("--prev", "prev", help="path to last week's saved state")
def progress(links, prev=None):
    lines = filter(None, map(str.strip, Path(links).read_text().split("\n")))
    scraper = Scraper()
    storage = Storage()

    players_then = None
    prev = storage.get(prev)
    if prev is not None:
        day, players_then = prev
        print("Using data from", day)
    else:
        print("No previous data available")

    players_now = {}
    for line in lines:
        player = scraper.parse_player(line)
        players_now[line] = player
    storage.save(players_now)
    print(generate_progress.render(players_now, players_then))


if __name__ == "__main__":
    cli(prog_name="prospects")
