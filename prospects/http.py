import gzip
import hashlib
import logging
import pickle
import random
import sqlite3
import time
from datetime import datetime, timedelta

import requests

logger = logging.getLogger(__name__)

_TABLES_SQL = """\
CREATE TABLE IF NOT EXISTS requests (
    identity TEXT PRIMARY KEY NOT NULL,
    content BLOB NOT NULL,
    timestamp REAL NOT NULL
) WITHOUT ROWID;
"""


class CachingClient:
    def __init__(self, *, path=".request-cache.db", cache_duration=timedelta(days=1), delay=0.0, jitter=True):
        self._db = sqlite3.connect(path)
        self._db.execute(_TABLES_SQL)
        self._db.commit()
        self._session = requests.Session()
        self._session.headers.update(
            {"user-agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:67.0) Gecko/20100101 Firefox/67.0"}
        )
        self._cache_duration = cache_duration
        self._delay = delay
        self._jitter = jitter
        self._wait_until = time.monotonic()

    def _compute_identity(self, prepped):
        hasher = hashlib.sha1()
        hasher.update(prepped.url.encode())
        for header in sorted(prepped.headers.keys()):
            hasher.update(header.lower())
            hasher.update(prepped.headers[header])
        return hasher.hexdigest()

    def get(self, url, params=None, **kwargs):
        req = requests.Request("GET", url, params, **kwargs)
        prepped = req.prepare()
        identity = self._compute_identity(prepped)
        cutoff = (datetime.utcnow() - self._cache_duration).timestamp()

        cur = self._db.execute("SELECT content FROM requests WHERE identity = ? AND timestamp > ?", (identity, cutoff))
        res = cur.fetchone()
        if res is not None:
            logger.debug("loaded url from cache %s", prepped.url)

            return pickle.loads(gzip.decompress(res[0]))
        else:
            logger.debug("fetching document %s", prepped.url)

            sleep_for = max(0, self._wait_until - time.monotonic())
            time.sleep(sleep_for)

            resp = self._session.send(prepped)

            delay = self._delay
            if self._jitter:
                offset = self._delay * 0.25
                delay += random.uniform(-offset, offset)

            logger.debug("delay of %.2f for next request", delay)
            self._wait_until = time.monotonic() + self._delay

            resp.raise_for_status()
            self._db.execute(
                "INSERT OR REPLACE INTO requests (identity, content, timestamp) VALUES (?, ?, ?)",
                (identity, gzip.compress(pickle.dumps(resp)), datetime.utcnow().timestamp()),
            )
            self._db.commit()
            return resp
