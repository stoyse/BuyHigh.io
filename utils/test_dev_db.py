import os
from database.handler.postgres.postgres_db_handler import get_db_connection, add_analytics

import psycopg2.extras

def get_all_developers():
    add_analytics(None, "get_all_developers", "test_dev_db")
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    try:
        cur.execute("SELECT * FROM developers ORDER BY id")
        developers = [dict(row) for row in cur.fetchall()]
        return developers
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    devs = get_all_developers()
    print("Developers:")
    for dev in devs:
        print(dev)