from decimal import Decimal
from pathlib import Path

from marketpulse.sources.books_toscrape import parse_listing

FIXTURE = Path(__file__).parent / "fixtures" / "books_page1.html"
PAGE_URL = "https://books.toscrape.com/"


def test_parse_first_page():
    items, next_url = parse_listing(FIXTURE.read_bytes(), PAGE_URL)

    assert len(items) == 20
    assert next_url == "https://books.toscrape.com/catalogue/page-2.html"

    first = items[0]
    assert first.source == "books_toscrape"
    assert first.external_id == "a-light-in-the-attic_1000"
    assert first.title == "A Light in the Attic"
    assert first.price == Decimal("51.77")
    assert first.raw["rating"] == 3


def test_missing_price_becomes_none():
    html = b"""
    <article class="product_pod">
      <h3><a href="catalogue/x_1/index.html" title="Buku Tanpa Harga">Buku Tanpa...</a></h3>
    </article>
    """
    items, next_url = parse_listing(html, PAGE_URL)

    assert len(items) == 1
    assert items[0].price is None
    assert items[0].raw["rating"] is None
    assert next_url is None


def test_card_without_title_link_is_skipped():
    html = b'<article class="product_pod"><p class="price_color">\xc2\xa310.00</p></article>'
    items, _ = parse_listing(html, PAGE_URL)

    assert items == []