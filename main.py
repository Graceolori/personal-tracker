import sqlite3
from pathlib import Path

name = "Emuobo"
email = "golori84@gmail.com"

DB_NAME = Path(__file__).resolve().parent / "tracker.db"

with sqlite3.connect(DB_NAME) as conn:
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id FROM users WHERE email = ?",
        (email,),
    )
    existing_user = cursor.fetchone()

    if existing_user:
        print("User already exists")
    else:
        cursor.execute(
            "INSERT INTO users (name, email) VALUES (?, ?)",
            (name, email),
        )
        conn.commit()
        print("User added")
