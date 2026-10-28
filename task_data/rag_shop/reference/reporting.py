from errors import ValidationError
from money import format_cents


def order_to_csv(order):
    if not order.lines:
        raise ValidationError("cannot export an order with no lines")
    rows = ["sku,name,qty,unit_price,line_total"]
    for line in order.lines:
        p = line.product
        rows.append(
            f"{p.sku},{p.name},{line.quantity},"
            f"{format_cents(p.price_cents)},{format_cents(line.line_total_cents())}"
        )
    rows.append(f"TOTAL,,,,{format_cents(order.total_cents())}")
    return "\n".join(rows)
