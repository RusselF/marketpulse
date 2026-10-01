from dataclasses import replace
from decimal import ROUND_HALF_UP, Decimal

from marketpulse.models import Product

CENT = Decimal("0.01")


def transform(p: Product) -> Product:
    title = " ".join((p.title or "").split())  # rapikan spasi berlebih
    category = (p.category or "").strip().lower() or None
    price = p.price.quantize(CENT, rounding=ROUND_HALF_UP) if p.price is not None else None
    return replace(p, title=title, category=category, price=price)