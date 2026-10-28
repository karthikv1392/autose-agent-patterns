import unittest

from pager import page_count, page_window, paginate


class PageCountTests(unittest.TestCase):
    def test_exact_and_partial(self):
        self.assertEqual(page_count(20, 10), 2)
        self.assertEqual(page_count(21, 10), 3)
        self.assertEqual(page_count(1, 10), 1)

    def test_empty_has_one_page(self):
        self.assertEqual(page_count(0, 10), 1)


class PaginateTests(unittest.TestCase):
    def setUp(self):
        self.items = list(range(1, 24))   # 23 items

    def test_first_page(self):
        self.assertEqual(paginate(self.items, 1, 10), list(range(1, 11)))

    def test_last_partial_page(self):
        self.assertEqual(paginate(self.items, 3, 10), [21, 22, 23])

    def test_out_of_range_page_is_empty(self):
        self.assertEqual(paginate(self.items, 4, 10), [])

    def test_invalid_arguments(self):
        with self.assertRaises(ValueError):
            paginate(self.items, 0, 10)
        with self.assertRaises(ValueError):
            paginate(self.items, 1, 0)


class PageWindowTests(unittest.TestCase):
    def test_start_edge(self):
        self.assertEqual(page_window(1, 10), [1, 2, 3, 4, 5])
        self.assertEqual(page_window(3, 10), [1, 2, 3, 4, 5])

    def test_middle(self):
        self.assertEqual(page_window(5, 10), [3, 4, 5, 6, 7])

    def test_end_edge(self):
        self.assertEqual(page_window(10, 10), [6, 7, 8, 9, 10])
        self.assertEqual(page_window(9, 10), [6, 7, 8, 9, 10])

    def test_fewer_pages_than_window(self):
        self.assertEqual(page_window(2, 3), [1, 2, 3])
        self.assertEqual(page_window(1, 1), [1])

    def test_custom_size(self):
        self.assertEqual(page_window(4, 10, size=3), [3, 4, 5])


if __name__ == "__main__":
    unittest.main()
