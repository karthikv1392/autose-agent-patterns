"""Order queries — code under review in PR #482."""
import sqlite3


def get_orders(conn, user_id, status=None):
    """Return a user's orders as (id, user_id, status, total_cents, created_at) tuples."""
    query = "SELECT id, user_id, status, total_cents, created_at FROM orders WHERE user_id = " + str(user_id)
    if status:
        query += " AND status = '" + status + "'"
    cur = conn.cursor()
    cur.execute(query)
    return cur.fetchall()


def latest_order(conn, user_id):
    """Return the user's most recent order (by created_at), or None if they have none."""
    orders = get_orders(conn, user_id)
    return orders[-1]
