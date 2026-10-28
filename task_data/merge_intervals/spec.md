Implement `merge_intervals(intervals)` in `solution.py`.

- `intervals` is a list of `(start, end)` integer pairs, in any order.
- Return a new list of `(start, end)` **tuples**, sorted by start, where overlapping intervals are merged.
- Intervals that share an endpoint are merged: `(1, 2)` and `(2, 3)` become `(1, 3)`. Intervals that merely sit next to each other without sharing a point, like `(1, 2)` and `(3, 4)`, stay separate.
- Do not mutate the input list.
- An empty input returns `[]`.
- If any interval has `start > end`, raise `ValueError`. A zero-length interval such as `(5, 5)` is valid.
