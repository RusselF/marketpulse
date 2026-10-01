from decimal import Decimal

from marketpulse.models import Product
from marketpulse.transform import transform


def test_normalizes_title_category_price():
    p = Product("s", "1", "  Buku   Bagus ", Decimal("10.005"), " Fiction ", {})
    out = transform(p)
    assert out.title == "Buku Bagus"
    assert out.category == "fiction"
    assert out.price == Decimal("10.01")


def test_empty_category_becomes_none_and_missing_price_stays_none():
    out = transform(Product("s", "1", "x", None, "  ", {}))
    assert out.category is None
    assert out.price is None