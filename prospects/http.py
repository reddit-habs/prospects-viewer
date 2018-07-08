import gzip
import hashlib
import logging
import os
import pickle
import time
import random

import requests

logger = logging.getLogger(__name__)


class CachingClient:
    def __init__(self, *, base_path=".request-cache", delay=0.0, jitter=True):
        self._base_path = base_path
        self._session = requests.Session()
        self._session.headers.update(
            {
                "user-agent": "Mozilla/5.0 (Windows NT 6.3; Win64; x64; rv:60.0) Gecko/20100101 Firefox/60.0"
            }
        )
        self._delay = delay
        self._jitter = jitter
        self._wait_until = time.monotonic()

        os.makedirs(base_path, exist_ok=True)

    def get(self, url, params=None, **kwargs):
        req = requests.Request("GET", url, params, **kwargs)
        prepped = req.prepare()

        hasher = hashlib.sha1()
        hasher.update(prepped.url.encode())
        url_hash = hasher.hexdigest()

        complete_path = os.path.join(self._base_path, url_hash)
        try:
            with gzip.open(complete_path, "rb") as f:
                resp = pickle.load(f)
            logger.debug("loaded url from cache %s", prepped.url)
        except FileNotFoundError:

            sleep_for = max(0, self._wait_until - time.monotonic())
            time.sleep(sleep_for)

            resp = self._session.send(prepped)
            with gzip.open(complete_path, "wb") as f:
                pickle.dump(resp, f)

            delay = self._delay
            if self._jitter:
                offset = self._delay * 0.25
                delay += random.uniform(-offset, offset)

            logger.debug("delay of %.2f for next request", delay)
            self._wait_until = time.monotonic() + self._delay

            logger.debug("loaded url from web %s", prepped.url)

        return resp