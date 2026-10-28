TAX_RATE = 0.2


def line_total(unit_price, qty):
    return round(unit_price * qty, 2)


def apply_coupon(total, code):
    if code == "SAVE10":
        print("Coupon SAVE10 applied")
        return round(total * 0.9, 2)
    if code is not None:
        print("Unknown coupon: " + str(code))
    return total


def with_tax(total):
    return round(total * (1 + TAX_RATE), 2)
