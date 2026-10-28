import sqlite3
import unittest

from orders_db import get_orders, latest_order


def make_conn():
    conn = sqlite3.connect(":memory:")
    conn.execute(
        "CREATE TABLE orders (id INTEGER PRIMARY KEY, user_id INTEGER, status TEXT, "
        "total_cents INTEGER, created_at TEXT)"
    )
    conn.executemany(
        "INSERT INTO orders VALUES (?, ?, ?, ?, ?)",
        [
            (1, 1, "paid", 1000, "2024-01-05"),
            (2, 1, "pending", 500, "2024-03-01"),   # newest, but inserted second
            (3, 1, "paid", 700, "2024-02-01"),
            (4, 2, "paid", 900, "2024-01-20"),
        ],
    )
    return conn


class GetOrdersTests(unittest.TestCase):
    def setUp(self):
        self.conn = make_conn()

    def test_returns_all_orders_for_user_as_tuples(self):
        rows = get_orders(self.conn, 1)
        self.assertEqual(sorted(r[0] for r in rows), [1, 2, 3])
        self.assertTrue(all(isinstance(r, tuple) and len(r) == 5 for r in rows))

    def test_status_filter(self):
        rows = get_orders(self.conn, 1, "paid")
        self.assertEqual(sorted(r[0] for r in rows), [1, 3])

    def test_status_injection_is_neutralised(self):
        self.assertEqual(get_orders(self.conn, 1, "paid' OR '1'='1"), [])

    def test_user_id_injection_is_neutralised(self):
        self.assertEqual(get_orders(self.conn, "1 OR 1=1"), [])

    def test_apostrophe_in_status_does_not_crash(self):
        self.assertEqual(get_orders(self.conn, 1, "o'neil"), [])

    def test_unknown_user(self):
        self.assertEqual(get_orders(self.conn, 99), [])


class LatestOrderTests(unittest.TestCase):
    def setUp(self):
        self.conn = make_conn()

    def test_latest_is_by_created_at_not_insertion_order(self):
        self.assertEqual(latest_order(self.conn, 1)[0], 2)

    def test_user_without_orders_returns_none(self):
        self.assertIsNone(latest_order(self.conn, 99))

    def test_returns_tuple_shape(self):
        row = latest_order(self.conn, 2)
        self.assertEqual(row, (4, 2, "paid", 900, "2024-01-20"))


if __name__ == "__main__":
    unittest.main()
