from pathlib import Path
import json
import enum
import pickle

import attr
import click

from .scrape import parse_players
from . import generate


class AttrsJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if attr.has(o.__class__):
            return attr.asdict(o)
        elif isinstance(o, enum.Enum):
            return o.name
        else:
            super().default(o)


@click.command()
@click.argument('url', required=False)
@click.option('--pickle', 'pickle_path', default=None, help="Path to pickle dump")
@click.option('--json', 'json_path', default=None, help="Path to json dump")
@click.option('-u', '--use-pickle', 'use_pickle', default=None, help="Use saved pickle")
def main(url, pickle_path, json_path, use_pickle):
    if use_pickle is not None:
        data = pickle.loads(Path(use_pickle).read_bytes())
    else:
        if url is None:
            print("Error: missing url")
            exit()
        skaters, goalies = parse_players(url)
        data = dict(skaters=skaters, goalies=goalies)

    if pickle_path:
        Path(pickle_path).write_bytes(pickle.dumps(data))

    if json_path:
        Path(json_path).write_text(AttrsJSONEncoder(indent=2).encode(data))

    print(generate.render(data))


if __name__ == '__main__':
    main()
