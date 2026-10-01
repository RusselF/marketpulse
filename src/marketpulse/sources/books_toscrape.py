import logging
import re
import time
from decimal import Decimal
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from marketpulse.http_client import make_client
from marketpulse.models import Product

log = logging.getLogger(__name__)

SOURCE = "books_toscrape"
START_URL = "https://books.toscrape.com/"
RATINGS = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}


def _parse_price(text: str) -> Decimal | None:
    cleaned = re.sub(r"[^\d.]", "", text)  # "£51.77" -> "51.77"
    return Decimal(cleaned) if cleaned else None


def parse_listing(html: bytes, page_url: str) -> tuple[list[Product], str | None]:
    """Parse satu halaman listing. Fungsi murni: tanpa network, mudah dites."""
    soup = BeautifulSoup(html, "html.parser")
    products: list[Product] = []

    for card in soup.select("article.product_pod"):
        link = card.select_one("h3 a")
        if link is None:
            log.warning("card tanpa link judul di %s, dilewati", page_url)
            continue

        detail_url = urljoin(page_url, link["href"])
        price_el = card.select_one("p.price_color")
        rating_el = card.select_one("p.star-rating")
        avail_el = card.select_one("p.availability")

        rating = None
        if rating_el is not None:
            rating = next((RATINGS[c] for c in rating_el.get("class", []) if c in RATINGS), None)

        products.append(
            Product(
                source=SOURCE,
                external_id=detail_url.rstrip("/").split("/")[-2],  # contoh: a-light-in-the-attic_1000
                title=link["title"],  # teks link terpotong ("A Light in the ..."), atribut title lengkap
                price=_parse_price(price_el.get_text(strip=True)) if price_el else None,
                category=None,  # tidak ada di halaman listing
                raw={
                    "url": detail_url,
                    "rating": rating,
                    "availability": avail_el.get_text(strip=True) if avail_el else None,
                },
            )
        )

    next_link = soup.select_one("li.next > a")
    next_url = urljoin(page_url, next_link["href"]) if next_link else None
    return products, next_url


def fetch_products(max_pages: int | None = None) -> list[Product]:
    products: list[Product] = []
    url: str | None = START_URL
    page = 0
    with make_client() as client:
        while url and (max_pages is None or page < max_pages):
            resp = client.get(url)
            resp.raise_for_status()
            items, url = parse_listing(resp.content, str(resp.url))
            products.extend(items)
            page += 1
            log.info("books_toscrape page=%d got=%d total=%d", page, len(items), len(products))
            time.sleep(0.3)  # sementara; rate limiting yang benar di Phase 4
    return products