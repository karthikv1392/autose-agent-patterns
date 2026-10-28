import unittest

from solution import merge_intervals


class MergeIntervalsTests(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(merge_intervals([]), [])

    def test_no_overlap(self):
        self.assertEqual(merge_intervals([(1, 2), (4, 5)]), [(1, 2), (4, 5)])

    def test_overlap(self):
        self.assertEqual(merge_intervals([(1, 3), (2, 6)]), [(1, 6)])

    def test_unsorted_input(self):
        self.assertEqual(merge_intervals([(8, 10), (1, 3), (2, 6), (15, 18)]), [(1, 6), (8, 10), (15, 18)])

    def test_touching_endpoints_merge(self):
        self.assertEqual(merge_intervals([(1, 2), (2, 3)]), [(1, 3)])

    def test_adjacent_but_not_touching_stay_separate(self):
        self.assertEqual(merge_intervals([(1, 2), (3, 4)]), [(1, 2), (3, 4)])

    def test_contained_interval(self):
        self.assertEqual(merge_intervals([(1, 10), (2, 3), (4, 5)]), [(1, 10)])

    def test_chain_merge(self):
        self.assertEqual(merge_intervals([(1, 4), (4, 5), (5, 9)]), [(1, 9)])

    def test_zero_length(self):
        self.assertEqual(merge_intervals([(5, 5)]), [(5, 5)])
        self.assertEqual(merge_intervals([(5, 5), (5, 7)]), [(5, 7)])

    def test_returns_tuples(self):
        result = merge_intervals([[1, 3], [2, 4]])
        self.assertEqual(result, [(1, 4)])
        self.assertTrue(all(isinstance(r, tuple) for r in result))

    def test_input_not_mutated(self):
        data = [(5, 6), (1, 2)]
        snapshot = list(data)
        merge_intervals(data)
        self.assertEqual(data, snapshot)

    def test_invalid_interval_rejected(self):
        with self.assertRaises(ValueError):
            merge_intervals([(3, 1)])
        with self.assertRaises(ValueError):
            merge_intervals([(1, 2), (9, 4)])


if __name__ == "__main__":
    unittest.main()
