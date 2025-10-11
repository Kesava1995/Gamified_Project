import sqlite3

print("--- Listing Users ---")
try:
    conn = sqlite3.connect('mydatabase.db')
    cursor = conn.cursor()

    for row in cursor.execute("SELECT id, username FROM users"):
        print(f"ID: {row[0]}, Username: {row[1]}")

    conn.close()
except Exception as e:
    print(f"An error occurred: {e}")