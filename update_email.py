import sqlite3
from pathlib import Path

OLD_EMAIL = "grace.olori@outlook.com"
NEW_EMAIL = "golori84@gmail.com"

DB_NAME = Path(__file__).resolve().parent / "tracker.db"

with sqlite3.connect(DB_NAME) as conn:
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE users
        SET email = ?
        WHERE email = ?
    """, (NEW_EMAIL, OLD_EMAIL))

    conn.commit()

    print("✅ Email updated successfully")
