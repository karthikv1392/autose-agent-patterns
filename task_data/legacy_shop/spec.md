Modernise this legacy codebase **without changing its behaviour**:

1. Add type hints to every function and method (all parameters and the return type).
2. Add a one-line docstring to every class, function and method.
3. Replace every `print(...)` call with logging through a module-level `logger = logging.getLogger(__name__)` (use `logger.info`, `logger.warning` or `logger.error` as appropriate).

The existing test suite must still pass afterwards.
