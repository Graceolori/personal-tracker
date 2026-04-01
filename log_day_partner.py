import sqlite3
import smtplib
import os
from pathlib import Path
from datetime import date
from email.message import EmailMessage

DB_NAME = Path(__file__).resolve().parent / "tracker.db"

# Partner is logging today
USER_EMAIL = "martinsfm3000@gmail.com"
PARTNER_EMAIL = "golori84@gmail.com"

# Gmail SMTP (sender)
SENDER_EMAIL = "martinsfm3000@gmail.com"
EMAIL_PASSWORD = os.getenv("TRACKER_FEMI_EMAIL_PASSWORD")
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
DISABLE_EMAIL = os.getenv("TRACKER_DISABLE_EMAIL") == "1"


def get_activity():
    print("Daily Check-in")
    print("Type what you achieved today. Press ENTER twice when done.\n")

    lines = []
    while True:
        line = input()
        if line.strip() == "":
            break
        lines.append(f"- {line.strip()}")

    activity = "\n".join(lines).strip()
    if not activity:
        print("You must enter something.")
        raise SystemExit(1)

    return activity


def save_log(activity):
    today = date.today().isoformat()

    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, name FROM users WHERE email = ?",
            (USER_EMAIL,),
        )
        user = cursor.fetchone()

        if not user:
            print("User not found in database.")
            raise SystemExit(1)

        user_id, user_name = user

        cursor.execute(
            """
            SELECT id, activity
            FROM daily_logs
            WHERE user_id = ? AND date = ?
            """,
            (user_id, today),
        )
        existing_log = cursor.fetchone()

        if existing_log:
            log_id, old_activity = existing_log
            updated_activity = f"{old_activity}\n{activity}".strip()
            cursor.execute(
                """
                UPDATE daily_logs
                SET activity = ?, status = ?
                WHERE id = ?
                """,
                (updated_activity, "completed", log_id),
            )
            action = "updated"
            saved_activity = updated_activity
        else:
            cursor.execute(
                """
                INSERT INTO daily_logs (user_id, date, activity, status)
                VALUES (?, ?, ?, ?)
                """,
                (user_id, today, activity, "completed"),
            )
            action = "created"
            saved_activity = activity

        conn.commit()

    return today, user_name, action, saved_activity


def send_notification(user_name, today, activity):
    if DISABLE_EMAIL:
        print("Email sending skipped for test run")
        return False

    if not EMAIL_PASSWORD:
        print("Missing environment variable: TRACKER_FEMI_EMAIL_PASSWORD")
        raise SystemExit(1)

    message_body = f"""
Hi,

{user_name} just completed their daily check-in for {today}.

Here's what they logged:
--------------------------------
{activity}
--------------------------------
"""

    msg = EmailMessage()
    msg["From"] = SENDER_EMAIL
    msg["To"] = PARTNER_EMAIL
    msg["Subject"] = f"Daily Check-in ({user_name})"
    msg.set_content(message_body)

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SENDER_EMAIL, EMAIL_PASSWORD)
        server.send_message(msg)

    return True


activity = get_activity()
today, user_name, action, saved_activity = save_log(activity)
print(f"Daily log {action}")
email_sent = send_notification(user_name, today, saved_activity)
if email_sent:
    print("Notification email sent")
