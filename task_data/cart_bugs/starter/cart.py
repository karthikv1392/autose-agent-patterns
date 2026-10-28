from pricing import add_tax, apply_discount


class Cart:
    def __init__(self, items=[]):
        self.items = items

    def add(self, name, price_cents, qty=1):
        self.items.append({"name": name, "price": price_cents, "qty": qty})

    def remove(self, name):
        for item in self.items:
            if item["name"] == name:
                self.items.remove(item)

    def subtotal(self):
        return sum(i["price"] * i["qty"] for i in self.items)

    def total(self, discount_pct=0, tax_pct=0):
        discounted = apply_discount(self.subtotal(), discount_pct)
        return add_tax(discounted, tax_pct)
