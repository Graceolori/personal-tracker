import sqlite3
from pathlib import Path

DB_NAME = Path(__file__).resolve().parent / "tracker.db"

with sqlite3.connect(DB_NAME) as conn:
    cursor = conn.cursor()
    cursor.execute("DELETE FROM daily_logs")
    deleted_rows = cursor.rowcount
    conn.commit()

print(f"Deleted {deleted_rows} log(s) from daily_logs")
