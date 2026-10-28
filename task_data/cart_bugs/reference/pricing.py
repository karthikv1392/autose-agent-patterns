def _check(pct):
    if not 0 <= pct <= 100:
        raise ValueError("percentage must be between 0 and 100")


def apply_discount(amount_cents, pct):
    _check(pct)
    return amount_cents - (amount_cents * pct + 50) // 100


def add_tax(amount_cents, pct):
    _check(pct)
    return amount_cents + (amount_cents * pct + 50) // 100
