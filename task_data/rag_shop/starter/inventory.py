"""Stock tracking."""
from errors import OutOfStockError


class Inventory:
    """Tracks units on hand per SKU."""

    def __init__(self) -> None:
        self._stock: dict[str, int] = {}

    def add(self, sku: str, quantity: int) -> None:
        """Increase stock for a SKU."""
        self._stock[sku] = self._stock.get(sku, 0) + quantity

    def remove(self, sku: str, quantity: int) -> None:
        """Decrease stock; raises OutOfStockError when there is not enough."""
        if self._stock.get(sku, 0) < quantity:
            raise OutOfStockError(f"not enough {sku} in stock")
        self._stock[sku] -= quantity

    def units_on_hand(self, sku: str) -> int:
        """Current stock level for a SKU (0 if unknown)."""
        return self._stock.get(sku, 0)
