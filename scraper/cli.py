"""Command line interface.

Examples:
    python -m scraper quotes -o output/quotes.csv
    python -m scraper books --max-pages 3 -o output/books.xlsx --delay 1.5
"""

from __future__ import annotations

import argparse
import logging
import os
import sys

from dotenv import load_dotenv

from .client import ClientConfig, Fetcher
from .core import crawl
from .exporters import export
from .parsers import DEFAULT_URLS, PARSERS


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="scraper", description="Polite paginated scraper (CSV/Excel/JSON)")
    p.add_argument("site", choices=sorted(PARSERS), help="which parser to use")
    p.add_argument("-o", "--output", default=None, help="output file (.csv/.xlsx/.json)")
    p.add_argument("--url", default=None, help="start URL (defaults to the site's home page)")
    p.add_argument("--max-pages", type=int, default=None)
    p.add_argument("--max-items", type=int, default=None)
    p.add_argument("--delay", type=float, default=None, help="seconds between requests")
    p.add_argument("--retries", type=int, default=None)
    p.add_argument("--timeout", type=float, default=None)
    p.add_argument("--proxy", default=None)
    p.add_argument("-v", "--verbose", action="store_true")
    return p


def config_from(args: argparse.Namespace) -> ClientConfig:
    env = os.environ
    return ClientConfig(
        user_agent=env.get("SCRAPER_USER_AGENT") or ClientConfig.user_agent,
        delay=args.delay if args.delay is not None else float(env.get("SCRAPER_DELAY", 1.0)),
        max_retries=args.retries if args.retries is not None else int(env.get("SCRAPER_MAX_RETRIES", 3)),
        timeout=args.timeout if args.timeout is not None else float(env.get("SCRAPER_TIMEOUT", 15)),
        proxy=args.proxy or env.get("SCRAPER_PROXY") or None,
    )


def main(argv: list[str] | None = None, fetcher: Fetcher | None = None) -> int:
    load_dotenv()
    args = build_parser().parse_args(argv)
    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    output = args.output or f"output/{args.site}.csv"
    start = args.url or DEFAULT_URLS[args.site]
    own = fetcher is None
    fetcher = fetcher or Fetcher(config_from(args))
    try:
        rows = list(crawl(fetcher, PARSERS[args.site], start, args.max_pages, args.max_items))
    finally:
        if own:
            fetcher.close()
    path = export(rows, output)
    print(f"saved {len(rows)} rows -> {path}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
