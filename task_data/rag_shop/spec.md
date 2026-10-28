Add a new module `reporting.py` to this codebase containing `order_to_csv(order) -> str`.

- The first line is the header: `sku,name,qty,unit_price,line_total`
- Then one row per order line, in order.
- The last row is `TOTAL,,,,<order total>`.
- Rows are joined with `"\n"`, with no trailing newline.
- Prices and totals must be formatted the way the rest of this project formats money (no currency symbol).
- If the order has no lines, raise the project's own validation error.

Reuse the existing models and helpers. Do not reimplement them.
