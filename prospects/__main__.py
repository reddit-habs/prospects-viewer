from pathlib import Path
import json
import enum
import pickle

import attr

from .scrape import parse_players


class AttrsJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if attr.has(o.__class__):
            return attr.asdict(o)
        elif isinstance(o, enum.Enum):
            return o.name
        else:
            super().default(o)


skaters, goalies = parse_players('https://www.eliteprospects.com/team/64/montreal-canadiens/in-the-system')
data = dict(skaters=skaters, goalies=goalies)

Path('data.json').write_text(AttrsJSONEncoder(indent=2).encode(data))
Path('data.pickle').write_bytes(pickle.dumps(data))
