import sqlite3

def get_user(user_id):
    conn = sqlite3.connect("users.db")

    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM users WHERE id = ?",
        (user_id,)
    )

    if user_id > 100:
        conn.close()

    return cursor.fetchone()