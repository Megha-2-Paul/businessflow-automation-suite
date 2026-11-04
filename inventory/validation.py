"""Validation helpers for inventory quantities and product data."""
from decimal import Decimal, InvalidOperation
from typing import Any


class InventoryValidationError(ValueError):
    """Raised when inventory input is invalid."""


def positive_quantity(value: Any, field: str = "Quantity") -> Decimal:
    """Return a finite positive quantity with three decimal places."""
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise InventoryValidationError(f"{field} must be a valid number.") from exc
    if not amount.is_finite() or amount <= 0:
        raise InventoryValidationError(f"{field} must be greater than zero.")
    return amount.quantize(Decimal("0.001"))


def nonnegative_quantity(value: Any, field: str = "Quantity") -> Decimal:
    """Return a finite non-negative quantity with three decimal places."""
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise InventoryValidationError(f"{field} must be a valid number.") from exc
    if not amount.is_finite() or amount < 0:
        raise InventoryValidationError(f"{field} must be a finite, non-negative number.")
    return amount.quantize(Decimal("0.001"))
