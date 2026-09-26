"""Pagination loop that ties the fetcher and a parser together."""

from __future__ import annotations

import logging
from typing import Iterator

from .client import Fetcher
from .parsers import Item, Parser

log = logging.getLogger(__name__)


def crawl(
    fetcher: Fetcher,
    parser: Parser,
    start_url: str,
    max_pages: int | None = None,
    max_items: int | None = None,
) -> Iterator[Item]:
    """Follow "next" links, yielding items until exhausted or a limit is hit."""
    url: str | None = start_url
    pages = 0
    count = 0
    seen: set[str] = set()
    while url and url not in seen:
        if max_pages is not None and pages >= max_pages:
            break
        seen.add(url)
        log.info("fetching page %d: %s", pages + 1, url)
        resp = fetcher.get(url)
        items, url = parser(resp.text, str(resp.url))
        pages += 1
        for item in items:
            yield item
            count += 1
            if max_items is not None and count >= max_items:
                return
