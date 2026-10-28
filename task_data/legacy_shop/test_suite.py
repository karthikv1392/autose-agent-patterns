import unittest

from inventory import Inventory
from orders import place_order
from pricing import apply_coupon, line_total, with_tax
from reports import order_summary, stock_report


class InventoryTests(unittest.TestCase):
    def test_add_and_remove(self):
        inv = Inventory()
        inv.add_stock("A", 5)
        self.assertTrue(inv.remove_stock("A", 2))
        self.assertEqual(inv.stock_of("A"), 3)

    def test_non_positive_add_ignored(self):
        inv = Inventory()
        inv.add_stock("A", 0)
        self.assertEqual(inv.stock_of("A"), 0)

    def test_over_removal_rejected(self):
        inv = Inventory()
        inv.add_stock("A", 1)
        self.assertFalse(inv.remove_stock("A", 2))
        self.assertEqual(inv.stock_of("A"), 1)


class PricingTests(unittest.TestCase):
    def test_line_total(self):
        self.assertEqual(line_total(2.5, 3), 7.5)

    def test_coupon(self):
        self.assertEqual(apply_coupon(20.0, "SAVE10"), 18.0)
        self.assertEqual(apply_coupon(20.0, "BOGUS"), 20.0)
        self.assertEqual(apply_coupon(20.0, None), 20.0)

    def test_tax(self):
        self.assertEqual(with_tax(20.0), 24.0)


class OrderTests(unittest.TestCase):
    def setUp(self):
        self.inv = Inventory()
        self.inv.add_stock("A", 5)
        self.inv.add_stock("B", 5)

    def test_place_order(self):
        order = place_order(self.inv, [("A", 10.0, 2)])
        self.assertEqual(order["subtotal"], 20.0)
        self.assertEqual(order["total"], 24.0)
        self.assertEqual(self.inv.stock_of("A"), 3)

    def test_place_order_with_coupon(self):
        order = place_order(self.inv, [("A", 10.0, 2)], coupon="SAVE10")
        self.assertEqual(order["total"], 21.6)

    def test_out_of_stock_leaves_inventory_untouched(self):
        self.assertIsNone(place_order(self.inv, [("A", 10.0, 1), ("B", 1.0, 99)]))
        self.assertEqual(self.inv.stock_of("A"), 5)


class ReportTests(unittest.TestCase):
    def test_order_summary(self):
        inv = Inventory()
        inv.add_stock("A", 5)
        order = place_order(inv, [("A", 10.0, 2)])
        self.assertEqual(order_summary(order), "A x2 @ 10.00\nTOTAL: 24.00")
        self.assertEqual(order_summary(None), "No order")

    def test_stock_report(self):
        inv = Inventory()
        inv.add_stock("B", 5)
        inv.add_stock("A", 3)
        self.assertEqual(stock_report(inv), "A=3, B=5")


if __name__ == "__main__":
    unittest.main()
