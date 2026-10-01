from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class Product:
    source: str
    external_id: str
    title: str
    price: Decimal | None
    category: str | None
    raw: dict