from decimal import Decimal

from marketpulse.models import Product
from marketpulse.validation import validate


def prod(external_id="1", title="Buku", price="10.00"):
    return Product("s", external_id, title, Decimal(price) if price is not None else None, None, {})


def test_rejects_bad_rows_with_reason():
    valid, rejected = validate([prod(), prod("2", title=" "), prod("3", price="-1")])
    assert [p.external_id for p in valid] == ["1"]
    assert {r.reason for r in rejected} == {"title kosong", "price negatif"}


def test_missing_price_is_allowed():
    valid, rejected = validate([prod(price=None)])
    assert len(valid) == 1 and rejected == []


def test_duplicate_in_batch_keeps_last():
    valid, _ = validate([prod("1", price="5.00"), prod("1", price="7.00")])
    assert len(valid) == 1 and valid[0].price == Decimal("7.00")