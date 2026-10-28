Implement `parse_duration(text: str) -> int` in `solution.py`. It converts a human-written duration into a total number of seconds.

Rules:
- Units are `d` (86400 s), `h` (3600 s), `m` (60 s) and `s` (1 s). Units are case-insensitive.
- Components may be written with or without whitespace between them: `"1h30m"`, `"1h 30m"`, `"2D 4H"`.
- A bare non-negative integer with no unit means seconds: `"90"` -> 90.
- Each unit may appear at most once, and units must appear in descending order (d, h, m, s). So `"30m1h"` and `"1h1h"` are invalid.
- Surrounding whitespace is ignored.
- Raise `ValueError` for anything malformed: empty or whitespace-only input, unknown units (`"1x"`), a missing number (`"h"`), negative or fractional numbers (`"-5s"`, `"1.5h"`), and a trailing number with no unit after a unit (`"1h30"`).
