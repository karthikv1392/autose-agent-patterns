"""Core domain models for the shop."""
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Product:
    """A sellable item. price_cents is the unit price in integer cents."""

    sku: str
    name: str
    price_cents: int


@dataclass(frozen=True)
class OrderLine:
    """One product and a quantity within an order."""

    product: Product
    quantity: int

    def line_total_cents(self) -> int:
        """Unit price multiplied by quantity, in cents."""
        return self.product.price_cents * self.quantity


@dataclass
class Order:
    """A customer order made up of lines (see OrderLine)."""

    order_id: str
    lines: list[OrderLine] = field(default_factory=list)

    def total_cents(self) -> int:
        """Sum of all line totals, in cents."""
        return sum(line.line_total_cents() for line in self.lines)
