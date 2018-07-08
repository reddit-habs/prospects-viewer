from pathlib import Path
import json
import enum
import pickle
import logging

import attr
import click

from .scrape import parse_players
from . import generate

logging.basicConfig(level=logging.DEBUG)


class AttrsJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if attr.has(o.__class__):
            return attr.asdict(o)
        elif isinstance(o, enum.Enum):
            return o.name
        else:
            super().default(o)


@click.command()
@click.argument("url", required=False)
@click.option("--pickle", "pickle_path", default=None, help="Path to pickle dump")
@click.option("--json", "json_path", default=None, help="Path to json dump")
@click.option("-u", "--use-pickle", "use_pickle", default=None, help="Use saved pickle")
def main(url, pickle_path, json_path, use_pickle):
    if use_pickle is not None:
        players = pickle.loads(Path(use_pickle).read_bytes())
    else:
        if url is None:
            print("Error: missing url")
            exit()
        players = parse_players(url)

    if pickle_path:
        Path(pickle_path).write_bytes(pickle.dumps(players))

    if json_path:
        Path(json_path).write_text(AttrsJSONEncoder(indent=2).encode(players))

    print(generate.render(players))


if __name__ == "__main__":
    main()
