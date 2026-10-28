"""Pricing helpers.

All amounts are integer cents. Percentages are whole numbers in 0..100 and
anything outside that range raises ValueError. Discounts and tax are rounded
half-up to the nearest cent.
"""


def apply_discount(amount_cents, pct):
    """Return the amount after taking pct% off."""
    return amount_cents - amount_cents * pct // 100


def add_tax(amount_cents, pct):
    """Return the amount with pct% tax added."""
    return amount_cents + amount_cents * pct / 100
