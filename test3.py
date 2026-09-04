import sqlite3

def get_users():
    conn = sqlite3.connect("users.db")

    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users")

    users = cursor.fetchall()

    process_users(users)

    conn.close()

    return users