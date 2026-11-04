"""Unit tests for order input validation and decimal calculations."""
from decimal import Decimal

import pytest

from orders.validation import OrderValidationError, clean_line_items


def test_line_totals_use_decimal_arithmetic():
    lines = clean_line_items([
        {"description": "Service", "quantity": "1.5", "unit_price": "0.10"}
    ])
    assert lines[0]["amount"] == Decimal("0.15")


@pytest.mark.parametrize("qty", ["0", "-1", "NaN", "Infinity", "bad"])
def test_rejects_invalid_quantities(qty):
    with pytest.raises(OrderValidationError):
        clean_line_items([
            {"description": "Item", "quantity": qty, "unit_price": "1"}
        ])


def test_requires_description_and_lines():
    with pytest.raises(OrderValidationError, match="at least one"):
        clean_line_items([])
    with pytest.raises(OrderValidationError, match="description"):
        clean_line_items([
            {"description": " ", "quantity": "1", "unit_price": "1"}
        ])
