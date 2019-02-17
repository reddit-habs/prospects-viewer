import pickle
import sqlite3
from datetime import date

_TABLES_SQL = """\
CREATE TABLE IF NOT EXISTS week (
    day TEXT PRIMARY KEY NOT NULL,
    data BLOB NOT NULL
) WITHOUT ROWID;
"""


def _fmt_date(dt):
    return dt.strftime("%Y-%m-%d")


class Storage:
    def __init__(self, path="progress.db"):
        self._con = sqlite3.connect(path)
        self._con.execute(_TABLES_SQL)
        self._con.commit()

    def get(self, day=None):
        if day is None:
            today = _fmt_date(date.today())
            cur = self._con.execute("SELECT day, data FROM week WHERE day != ? ORDER BY day DESC LIMIT 1", [today])
        else:
            if isinstance(day, date):
                day = _fmt_date(day)
            cur = self._con.execute("SELECT day, data FROM week WHERE day = ?", [day])
        row = cur.fetchone()
        if row is None:
            return None
        return row[0], pickle.loads(row[1])

    def save(self, obj, day=None):
        if day is None:
            day = date.today()
        if isinstance(day, date):
            day = _fmt_date(day)
        self._con.execute("INSERT INTO week (day, data) VALUES (?, ?)", (day, pickle.dumps(obj)))
        self._con.commit()
