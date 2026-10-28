"""Exception hierarchy for the shop package."""


class ShopError(Exception):
    """Base class for every error raised deliberately by this package."""


class ValidationError(ShopError):
    """Raised when input data fails business-rule validation."""


class OutOfStockError(ShopError):
    """Raised when an inventory removal exceeds the units on hand."""
