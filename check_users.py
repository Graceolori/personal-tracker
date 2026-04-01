import sqlite3
from pathlib import Path

DB_NAME = Path(__file__).resolve().parent / "tracker.db"

with sqlite3.connect(DB_NAME) as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, email FROM users")
    users = cursor.fetchall()

print(users)
