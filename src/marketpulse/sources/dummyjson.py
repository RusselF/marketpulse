import logging
from decimal import Decimal

from marketpulse.http_client import make_client
from marketpulse.models import Product

log = logging.getLogger(__name__)

SOURCE = "dummyjson"
BASE_URL = "https://dummyjson.com"


def _to_product(p: dict) -> Product:
    price = p.get("price")
    return Product(
        source=SOURCE,
        external_id=str(p["id"]),
        title=p["title"],
        price=Decimal(str(price)) if price is not None else None,
        category=p.get("category"),
        raw=p,
    )


def fetch_products(page_size: int = 30) -> list[Product]:
    products: list[Product] = []
    skip = 0
    with make_client(BASE_URL) as client:
        while True:
            resp = client.get("/products", params={"limit": page_size, "skip": skip})
            resp.raise_for_status()
            data = resp.json()
            batch = data["products"]
            products.extend(_to_product(p) for p in batch)
            log.info("dummyjson skip=%d got=%d total=%d", skip, len(batch), data["total"])
            skip += page_size
            if not batch or skip >= data["total"]:
                break
    return products