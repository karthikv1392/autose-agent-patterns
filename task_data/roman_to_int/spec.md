Implement `roman_to_int(s: str) -> int` in `solution.py`.

Rules:
- Convert a Roman numeral to an integer in the range 1..3999.
- Input is case-insensitive and surrounding whitespace is ignored.
- Only **canonically formed** numerals are valid: `IIII`, `VX`, `IC`, `XM`, `VV`, `IIX` and `MMMM` must all raise `ValueError` (the only subtractive pairs allowed are IV, IX, XL, XC, CD and CM; a symbol may repeat at most three times in a row, and V, L and D never repeat).
- Raise `ValueError` for empty strings and for any character that is not a Roman numeral letter.
