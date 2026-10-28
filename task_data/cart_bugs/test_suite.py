import unittest

from cart import Cart
from pricing import add_tax, apply_discount


class PricingTests(unittest.TestCase):
    def test_discount_rounds_half_up(self):
        self.assertEqual(apply_discount(999, 15), 849)   # 149.85 off -> 150
        self.assertEqual(apply_discount(50, 1), 49)      # 0.5 off -> 1

    def test_discount_edges(self):
        self.assertEqual(apply_discount(1000, 0), 1000)
        self.assertEqual(apply_discount(1000, 100), 0)

    def test_tax_rounds_half_up_and_returns_int(self):
        result = add_tax(849, 8)                          # 67.92 -> 68
        self.assertEqual(result, 917)
        self.assertIsInstance(result, int)

    def test_percentages_validated(self):
        for bad in (-1, 101):
            with self.assertRaises(ValueError):
                apply_discount(100, bad)
            with self.assertRaises(ValueError):
                add_tax(100, bad)


class CartTests(unittest.TestCase):
    def test_carts_are_independent(self):
        a, b = Cart(), Cart()
        a.add("pen", 150)
        self.assertEqual(b.items, [])

    def test_subtotal(self):
        c = Cart()
        c.add("pen", 150, 2)
        c.add("book", 999)
        self.assertEqual(c.subtotal(), 1299)

    def test_remove_all_matching_items(self):
        c = Cart()
        c.add("pen", 150)
        c.add("pen", 150)
        c.add("pen", 150)
        c.add("book", 999)
        c.remove("pen")
        self.assertEqual([i["name"] for i in c.items], ["book"])

    def test_total_with_discount_and_tax(self):
        c = Cart()
        c.add("book", 999)
        self.assertEqual(c.total(discount_pct=15, tax_pct=8), 917)

    def test_total_without_adjustments(self):
        c = Cart()
        c.add("pen", 150, 2)
        self.assertEqual(c.total(), 300)
        self.assertIsInstance(c.total(), int)


if __name__ == "__main__":
    unittest.main()
