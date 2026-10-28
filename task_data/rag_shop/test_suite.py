import unittest

from errors import ValidationError
from models import Order, OrderLine, Product
from reporting import order_to_csv


class OrderToCsvTests(unittest.TestCase):
    def test_full_report(self):
        order = Order(
            "A-100",
            [
                OrderLine(Product("SKU1", "Widget", 250), 2),
                OrderLine(Product("SKU2", "Gadget", 1999), 1),
            ],
        )
        expected = "\n".join(
            [
                "sku,name,qty,unit_price,line_total",
                "SKU1,Widget,2,2.50,5.00",
                "SKU2,Gadget,1,19.99,19.99",
                "TOTAL,,,,24.99",
            ]
        )
        self.assertEqual(order_to_csv(order), expected)

    def test_small_amounts_keep_two_decimals(self):
        order = Order("A-101", [OrderLine(Product("S", "Gum", 5), 3)])
        self.assertEqual(order_to_csv(order).splitlines()[1], "S,Gum,3,0.05,0.15")

    def test_no_trailing_newline(self):
        order = Order("A-102", [OrderLine(Product("S", "Gum", 100), 1)])
        self.assertFalse(order_to_csv(order).endswith("\n"))

    def test_empty_order_raises_project_validation_error(self):
        with self.assertRaises(ValidationError):
            order_to_csv(Order("A-103"))


if __name__ == "__main__":
    unittest.main()
