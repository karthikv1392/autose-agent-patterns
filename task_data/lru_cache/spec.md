Implement a class `LRUCache` in `solution.py`.

- `LRUCache(capacity)` — raise `ValueError` if `capacity` is not a positive integer.
- `get(key, default=None)` — return the value for `key`, or `default` if missing. A successful `get` marks the key as most recently used.
- `put(key, value)` — insert or update. Updating an existing key also marks it most recently used. If inserting a new key would exceed capacity, evict the **least** recently used key first.
- `len(cache)` returns the number of stored items.
- `key in cache` works and does **not** change recency.
- `keys()` returns a list of keys ordered from least recently used to most recently used.
- `get` and `put` should run in O(1) time (hint: `collections.OrderedDict`).
