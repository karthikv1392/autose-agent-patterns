import sqlite3

_COLUMNS = "id, user_id, status, total_cents, created_at"


def get_orders(conn, user_id, status=None):
    query = f"SELECT {_COLUMNS} FROM orders WHERE user_id = ?"
    params = [user_id]
    if status:
        query += " AND status = ?"
        params.append(status)
    return conn.execute(query, params).fetchall()


def latest_order(conn, user_id):
    return conn.execute(
        f"SELECT {_COLUMNS} FROM orders WHERE user_id = ? ORDER BY created_at DESC, id DESC LIMIT 1",
        (user_id,),
    ).fetchone()
