"""Site parsers. Each parser returns (items, next_page_url_or_None).

Add a new site by writing a function with the same signature and
registering it in PARSERS.
"""

from __future__ import annotations

from typing import Callable
from urllib.parse import urljoin

from selectolax.parser import HTMLParser

Item = dict[str, object]
Parser = Callable[[str, str], tuple[list[Item], str | None]]

RATING_WORDS = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}


def _text(node) -> str:
    return node.text(strip=True) if node is not None else ""


def _next_link(tree: HTMLParser, base_url: str) -> str | None:
    nxt = tree.css_first("li.next > a")
    if nxt is None:
        return None
    href = nxt.attributes.get("href")
    return urljoin(base_url, href) if href else None


def parse_quotes(html: str, base_url: str) -> tuple[list[Item], str | None]:
    """https://quotes.toscrape.com"""
    tree = HTMLParser(html)
    items: list[Item] = []
    for q in tree.css("div.quote"):
        items.append(
            {
                "text": _text(q.css_first("span.text")).strip("\u201c\u201d\""),
                "author": _text(q.css_first("small.author")),
                "tags": ",".join(_text(t) for t in q.css("a.tag")),
            }
        )
    return items, _next_link(tree, base_url)


def parse_books(html: str, base_url: str) -> tuple[list[Item], str | None]:
    """https://books.toscrape.com"""
    tree = HTMLParser(html)
    items: list[Item] = []
    for b in tree.css("article.product_pod"):
        a = b.css_first("h3 > a")
        price_raw = _text(b.css_first("p.price_color"))
        digits = "".join(ch for ch in price_raw if ch.isdigit() or ch == ".")
        rating_node = b.css_first("p.star-rating")
        rating = 0
        if rating_node is not None:
            for cls in (rating_node.attributes.get("class") or "").split():
                rating = RATING_WORDS.get(cls, rating)
        items.append(
            {
                "title": (a.attributes.get("title") if a else "") or _text(a),
                "price": float(digits) if digits else None,
                "currency": price_raw[:1] if price_raw else "",
                "rating": rating,
                "in_stock": "in stock" in _text(b.css_first("p.availability")).lower(),
                "url": urljoin(base_url, a.attributes.get("href", "")) if a else "",
            }
        )
    return items, _next_link(tree, base_url)


PARSERS: dict[str, Parser] = {"quotes": parse_quotes, "books": parse_books}

DEFAULT_URLS = {
    "quotes": "https://quotes.toscrape.com/",
    "books": "https://books.toscrape.com/",
}
