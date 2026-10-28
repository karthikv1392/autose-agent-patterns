def order_summary(order):
    if order is None:
        return "No order"
    lines = []
    for sku, price, qty in order["items"]:
        lines.append("%s x%d @ %.2f" % (sku, qty, price))
    lines.append("TOTAL: %.2f" % order["total"])
    return "\n".join(lines)


def stock_report(inventory):
    rows = sorted(inventory.stock.items())
    return ", ".join("%s=%d" % (sku, qty) for sku, qty in rows)
