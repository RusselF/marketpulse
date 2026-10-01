from dataclasses import dataclass
from decimal import Decimal

from marketpulse.models import Product


@dataclass(frozen=True)
class Rejected:
    product: Product
    reason: str


def check(p: Product) -> str | None:
    if not (p.external_id or "").strip():
        return "external_id kosong"
    if not (p.title or "").strip():
        return "title kosong"
    if p.price is not None and p.price < Decimal("0"):
        return "price negatif"
    return None


def validate(products: list[Product]) -> tuple[list[Product], list[Rejected]]:
    valid: dict[tuple[str, str], Product] = {}
    rejected: list[Rejected] = []
    for p in products:
        reason = check(p)
        if reason:
            rejected.append(Rejected(p, reason))
            continue
        valid[(p.source, p.external_id)] = p  # duplikat dalam batch: yang terakhir menang
    return list(valid.values()), rejected