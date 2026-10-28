"""Money helpers.

Convention: money is ALWAYS stored and passed around as an integer number of
cents. Floats are never used for currency. Convert to text only at the edges
with format_cents().
"""


def format_cents(cents: int) -> str:
    """Format integer cents as a decimal string without a currency symbol.

    Example: 1234 -> "12.34", 5 -> "0.05", -250 -> "-2.50".
    """
    sign = "-" if cents < 0 else ""
    cents = abs(cents)
    return f"{sign}{cents // 100}.{cents % 100:02d}"


def parse_cents(text: str) -> int:
    """Parse a decimal string such as "12.34" into integer cents."""
    whole, _, frac = text.partition(".")
    return int(whole) * 100 + int((frac + "00")[:2])
