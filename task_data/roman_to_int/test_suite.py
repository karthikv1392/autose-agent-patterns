import unittest

from solution import roman_to_int


class RomanTests(unittest.TestCase):
    def test_basic(self):
        for s, n in (("I", 1), ("V", 5), ("X", 10), ("L", 50), ("C", 100), ("D", 500), ("M", 1000)):
            self.assertEqual(roman_to_int(s), n)

    def test_additive(self):
        self.assertEqual(roman_to_int("III"), 3)
        self.assertEqual(roman_to_int("XVIII"), 18)
        self.assertEqual(roman_to_int("MMM"), 3000)

    def test_subtractive(self):
        for s, n in (("IV", 4), ("IX", 9), ("XL", 40), ("XC", 90), ("CD", 400), ("CM", 900)):
            self.assertEqual(roman_to_int(s), n)

    def test_complex(self):
        self.assertEqual(roman_to_int("MCMXCIV"), 1994)
        self.assertEqual(roman_to_int("MMMCMXCIX"), 3999)
        self.assertEqual(roman_to_int("MDCCCLXXXVIII"), 1888)

    def test_case_and_whitespace(self):
        self.assertEqual(roman_to_int(" mcmxciv "), 1994)

    def test_invalid_repetition(self):
        for bad in ("IIII", "VV", "XXXX", "MMMM", "LL"):
            with self.assertRaises(ValueError, msg=bad):
                roman_to_int(bad)

    def test_invalid_subtraction(self):
        for bad in ("VX", "IC", "XM", "IIX", "IL", "VIV"):
            with self.assertRaises(ValueError, msg=bad):
                roman_to_int(bad)

    def test_empty_and_garbage(self):
        for bad in ("", "  ", "ABC", "X1", "I V"):
            with self.assertRaises(ValueError, msg=bad):
                roman_to_int(bad)


if __name__ == "__main__":
    unittest.main()
