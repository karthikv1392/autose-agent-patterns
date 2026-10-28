class Inventory:
    def __init__(self):
        self.stock = {}

    def add_stock(self, sku, qty):
        if qty <= 0:
            print("WARNING: ignoring non-positive quantity for", sku)
            return
        self.stock[sku] = self.stock.get(sku, 0) + qty
        print("Added %d of %s" % (qty, sku))

    def remove_stock(self, sku, qty):
        have = self.stock.get(sku, 0)
        if qty > have:
            print("ERROR: insufficient stock for", sku)
            return False
        self.stock[sku] = have - qty
        return True

    def stock_of(self, sku):
        return self.stock.get(sku, 0)
