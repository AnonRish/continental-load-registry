"""Small HTTP helper for third-party (non-official) data publishers.

Official grid-operator downloads are fetched directly by their own sync scripts.
Third-party aggregators are different: this helper identifies the project in
the User-Agent and honours each publisher's robots.txt, so a scheduled job never
scrapes a path the publisher has asked automated clients to avoid.
"""
from __future__ import annotations

import json
import time
import urllib.robotparser
from functools import lru_cache
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

USER_AGENT = "continental-load-registry/3.0 (+https://github.com/AnonRish/continental-load-registry)"


class RobotsDisallowed(RuntimeError):
    """The publisher's robots.txt asks automated clients not to fetch this URL."""


@lru_cache(maxsize=None)
def _robots_for(origin: str) -> urllib.robotparser.RobotFileParser:
    parser = urllib.robotparser.RobotFileParser()
    req = Request(origin + "/robots.txt", headers={"User-Agent": USER_AGENT})
    try:
        with urlopen(req, timeout=20) as resp:
            parser.parse(resp.read().decode("utf-8", "replace").splitlines())
    except Exception:  # noqa: BLE001 - no readable robots.txt means no stated restriction
        parser.parse([])
    return parser


def robots_allows(url: str, user_agent: str = USER_AGENT) -> bool:
    parts = urlsplit(url)
    return _robots_for(f"{parts.scheme}://{parts.netloc}").can_fetch(user_agent, url)


def fetch_bytes(url: str, *, timeout: int = 60, retries: int = 3) -> bytes:
    if not robots_allows(url):
        raise RobotsDisallowed(f"{url} is disallowed by the publisher's robots.txt")
    last: Exception | None = None
    for attempt in range(retries):
        try:
            with urlopen(Request(url, headers={"User-Agent": USER_AGENT}), timeout=timeout) as resp:
                body = resp.read()
            if not body:
                raise RuntimeError(f"{url}: empty response")
            return body
        except Exception as exc:  # noqa: BLE001
            last = exc
            if attempt + 1 < retries:
                time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"{url}: {last}")


def fetch_json(url: str, **kwargs):
    return json.loads(fetch_bytes(url, **kwargs).decode("utf-8"))
