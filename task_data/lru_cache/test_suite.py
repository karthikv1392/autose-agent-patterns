import unittest

from solution import LRUCache


class LRUCacheTests(unittest.TestCase):
    def test_basic_put_get(self):
        c = LRUCache(2)
        c.put("a", 1)
        self.assertEqual(c.get("a"), 1)
        self.assertIsNone(c.get("zzz"))
        self.assertEqual(c.get("zzz", 42), 42)

    def test_eviction_of_least_recently_used(self):
        c = LRUCache(2)
        c.put("a", 1)
        c.put("b", 2)
        c.put("c", 3)
        self.assertNotIn("a", c)
        self.assertEqual(c.keys(), ["b", "c"])

    def test_get_refreshes_recency(self):
        c = LRUCache(2)
        c.put("a", 1)
        c.put("b", 2)
        c.get("a")
        c.put("c", 3)
        self.assertIn("a", c)
        self.assertNotIn("b", c)

    def test_update_refreshes_recency_and_value(self):
        c = LRUCache(2)
        c.put("a", 1)
        c.put("b", 2)
        c.put("a", 10)
        c.put("c", 3)
        self.assertEqual(c.get("a"), 10)
        self.assertNotIn("b", c)

    def test_update_does_not_grow_or_evict(self):
        c = LRUCache(2)
        c.put("a", 1)
        c.put("b", 2)
        c.put("b", 3)
        self.assertEqual(len(c), 2)
        self.assertEqual(c.keys(), ["a", "b"])

    def test_contains_does_not_change_recency(self):
        c = LRUCache(2)
        c.put("a", 1)
        c.put("b", 2)
        self.assertIn("a", c)
        c.put("c", 3)
        self.assertNotIn("a", c)

    def test_keys_order(self):
        c = LRUCache(3)
        for k in "abc":
            c.put(k, 0)
        c.get("a")
        self.assertEqual(c.keys(), ["b", "c", "a"])

    def test_missing_get_does_not_change_state(self):
        c = LRUCache(2)
        c.put("a", 1)
        c.get("nope")
        self.assertEqual(len(c), 1)

    def test_falsy_values_are_stored(self):
        c = LRUCache(2)
        c.put("a", 0)
        c.put("b", None)
        self.assertEqual(c.get("a", "default"), 0)
        self.assertIn("b", c)

    def test_capacity_one(self):
        c = LRUCache(1)
        c.put("a", 1)
        c.put("b", 2)
        self.assertEqual(c.keys(), ["b"])

    def test_invalid_capacity(self):
        for bad in (0, -1, 1.5, "3", None):
            with self.assertRaises(ValueError, msg=repr(bad)):
                LRUCache(bad)


if __name__ == "__main__":
    unittest.main()
