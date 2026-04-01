import sqlite3
from pathlib import Path

DB_NAME = Path(__file__).resolve().parent / "tracker.db"

with sqlite3.connect(DB_NAME) as conn:
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(daily_logs)")
    print(cursor.fetchall())
