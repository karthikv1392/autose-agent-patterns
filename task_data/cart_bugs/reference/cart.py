from pricing import add_tax, apply_discount


class Cart:
    def __init__(self, items=None):
        self.items = list(items) if items else []

    def add(self, name, price_cents, qty=1):
        self.items.append({"name": name, "price": price_cents, "qty": qty})

    def remove(self, name):
        self.items = [i for i in self.items if i["name"] != name]

    def subtotal(self):
        return sum(i["price"] * i["qty"] for i in self.items)

    def total(self, discount_pct=0, tax_pct=0):
        return add_tax(apply_discount(self.subtotal(), discount_pct), tax_pct)
