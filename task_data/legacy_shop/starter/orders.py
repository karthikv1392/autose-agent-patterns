from pricing import apply_coupon, line_total, with_tax


def place_order(inventory, items, coupon=None):
    # items: list of (sku, unit_price, qty)
    for sku, price, qty in items:
        if inventory.stock_of(sku) < qty:
            print("Cannot place order: %s out of stock" % sku)
            return None
    subtotal = 0
    for sku, price, qty in items:
        inventory.remove_stock(sku, qty)
        subtotal += line_total(price, qty)
    total = with_tax(apply_coupon(subtotal, coupon))
    print("Order placed, total=%.2f" % total)
    return {"items": items, "subtotal": subtotal, "total": total}
