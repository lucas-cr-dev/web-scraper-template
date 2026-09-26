from scraper.parsers import parse_books, parse_quotes


def test_parse_quotes(fixture_html):
    items, nxt = parse_quotes(fixture_html("quotes_page1.html"), "https://quotes.toscrape.com/")
    assert len(items) == 2
    assert items[0]["author"] == "Albert Einstein"
    assert items[0]["text"].startswith("The world")
    assert items[0]["tags"] == "change,thinking"
    assert nxt == "https://quotes.toscrape.com/page/2/"


def test_parse_quotes_last_page(fixture_html):
    items, nxt = parse_quotes(fixture_html("quotes_page2.html"), "https://quotes.toscrape.com/page/2/")
    assert len(items) == 1
    assert items[0]["tags"] == ""
    assert nxt is None


def test_parse_books(fixture_html):
    items, nxt = parse_books(fixture_html("books_page1.html"), "https://books.toscrape.com/")
    assert [b["title"] for b in items] == ["A Light in the Attic", "Tipping the Velvet"]
    assert items[0]["price"] == 51.77
    assert items[0]["currency"] == "£"
    assert items[0]["rating"] == 3 and items[1]["rating"] == 1
    assert items[0]["in_stock"] is True and items[1]["in_stock"] is False
    assert items[0]["url"] == "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html"
    assert nxt == "https://books.toscrape.com/catalogue/page-2.html"
