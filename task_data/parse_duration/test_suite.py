import unittest

from solution import parse_duration


class ParseDurationTests(unittest.TestCase):
    def test_single_units(self):
        self.assertEqual(parse_duration("45s"), 45)
        self.assertEqual(parse_duration("2m"), 120)
        self.assertEqual(parse_duration("3h"), 10800)
        self.assertEqual(parse_duration("1d"), 86400)

    def test_combined(self):
        self.assertEqual(parse_duration("1h30m"), 5400)
        self.assertEqual(parse_duration("1d2h3m4s"), 93784)

    def test_whitespace_between_components(self):
        self.assertEqual(parse_duration("1h 30m"), 5400)
        self.assertEqual(parse_duration("2D 4H"), 2 * 86400 + 4 * 3600)

    def test_surrounding_whitespace(self):
        self.assertEqual(parse_duration("  10m  "), 600)

    def test_case_insensitive(self):
        self.assertEqual(parse_duration("1H30M"), 5400)

    def test_bare_integer_is_seconds(self):
        self.assertEqual(parse_duration("90"), 90)
        self.assertEqual(parse_duration("0"), 0)

    def test_zero_with_unit(self):
        self.assertEqual(parse_duration("0s"), 0)

    def test_returns_int(self):
        self.assertIsInstance(parse_duration("5m"), int)

    def test_empty_and_blank_rejected(self):
        for bad in ("", "   "):
            with self.assertRaises(ValueError):
                parse_duration(bad)

    def test_unknown_unit_rejected(self):
        with self.assertRaises(ValueError):
            parse_duration("1x")

    def test_missing_number_rejected(self):
        with self.assertRaises(ValueError):
            parse_duration("h")

    def test_negative_and_fractional_rejected(self):
        for bad in ("-5s", "1.5h"):
            with self.assertRaises(ValueError):
                parse_duration(bad)

    def test_wrong_order_rejected(self):
        with self.assertRaises(ValueError):
            parse_duration("30m1h")

    def test_repeated_unit_rejected(self):
        with self.assertRaises(ValueError):
            parse_duration("1h1h")

    def test_trailing_number_without_unit_rejected(self):
        with self.assertRaises(ValueError):
            parse_duration("1h30")

    def test_garbage_rejected(self):
        for bad in ("abc", "1h 30m x"):
            with self.assertRaises(ValueError):
                parse_duration(bad)


if __name__ == "__main__":
    unittest.main()
