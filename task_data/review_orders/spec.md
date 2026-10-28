**Pull request #482 — "Add order lookup helpers"**

Author's description: "Adds `get_orders` (all orders for a user, optionally filtered by status) and `latest_order` (the user's most recent order). Both are used by the new account page. Existing callers of `get_orders` unpack the rows as tuples `(id, user_id, status, total_cents, created_at)`, so please keep that shape."

Decide whether this PR can be merged. If not, produce a corrected version of `orders_db.py` that keeps the existing public behaviour and signatures.
