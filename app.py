from datetime import date
from email.message import EmailMessage
import logging
import os
from pathlib import Path
import sqlite3
import smtplib

from flask import Flask, flash, redirect, render_template, request, url_for


app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DB_PATH = BASE_DIR / "tracker.db"
DEFAULT_LOG_PATH = BASE_DIR / "app.log"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587


def load_env_file():
    env_path = BASE_DIR / ".env"
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ[key] = value


load_env_file()
app.secret_key = os.getenv("FLASK_SECRET_KEY", "personal-tracker-dev")


def get_db_path():
    db_path = Path(os.getenv("TRACKER_DB_PATH", str(DEFAULT_DB_PATH)))
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return db_path


def get_log_path():
    log_path = Path(os.getenv("TRACKER_LOG_PATH", str(DEFAULT_LOG_PATH)))
    log_path.parent.mkdir(parents=True, exist_ok=True)
    return log_path


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler(get_log_path(), encoding="utf-8"),
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger(__name__)


def get_connection():
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    return conn


def format_activity_block(activity):
    lines = [line.strip() for line in activity.splitlines() if line.strip()]
    return "\n".join(f"- {line}" for line in lines)


def init_db():
    with sqlite3.connect(get_db_path()) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS daily_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                activity TEXT NOT NULL,
                status TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id),
                UNIQUE (user_id, date)
            )
            """
        )
        conn.commit()


def send_log_notification(user_name, user_email, activity, today):
    if os.getenv("TRACKER_DISABLE_EMAIL") == "1":
        logger.info("Email skipped because TRACKER_DISABLE_EMAIL=1 for user=%s", user_email)
        return "skipped"

    sender_email = os.getenv("TRACKER_SENDER_EMAIL", "").strip()
    sender_password = os.getenv("TRACKER_SENDER_PASSWORD", "").strip()
    partner_email = os.getenv("TRACKER_PARTNER_EMAIL", "").strip()

    if not sender_email or not sender_password or not partner_email:
        logger.warning(
            "Email settings missing sender_email=%s partner_email=%s password_present=%s",
            bool(sender_email),
            bool(partner_email),
            bool(sender_password),
        )
        return "missing_config"

    if user_email.strip().lower() == sender_email.lower():
        recipient_email = partner_email
    elif user_email.strip().lower() == partner_email.lower():
        recipient_email = sender_email
    else:
        recipient_email = partner_email

    message_body = f"""
Hi,

{user_name} just completed their daily check-in for {today}.

Here's what they logged:
--------------------------------
{activity}
--------------------------------

Logged by: {user_email}
"""

    msg = EmailMessage()
    msg["From"] = sender_email
    msg["To"] = recipient_email
    msg["Subject"] = f"Daily Check-in ({user_name})"
    msg.set_content(message_body)

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
    except (smtplib.SMTPException, TimeoutError, OSError):
        logger.exception(
            "Email send failed sender=%s recipient=%s logged_by=%s user_name=%s",
            sender_email,
            recipient_email,
            user_email,
            user_name,
        )
        return "failed"

    logger.info(
        "Email sent sender=%s recipient=%s logged_by=%s user_name=%s",
        sender_email,
        recipient_email,
        user_email,
        user_name,
    )
    return "sent"


@app.route("/health")
def health():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()

    return {"status": "ok"}, 200


@app.route("/")
def index():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) AS count FROM users")
        user_count = cursor.fetchone()["count"]
        cursor.execute("SELECT COUNT(*) AS count FROM daily_logs")
        log_count = cursor.fetchone()["count"]
        cursor.execute(
            """
            SELECT daily_logs.date, daily_logs.activity, daily_logs.status, users.name
            FROM daily_logs
            JOIN users ON users.id = daily_logs.user_id
            ORDER BY daily_logs.date DESC, daily_logs.id DESC
            LIMIT 5
            """
        )
        recent_logs = cursor.fetchall()

    return render_template(
        "index.html",
        user_count=user_count,
        log_count=log_count,
        recent_logs=recent_logs,
    )


@app.route("/users")
def users():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, email FROM users ORDER BY name")
        all_users = cursor.fetchall()

    return render_template("users.html", users=all_users)


@app.route("/add-user", methods=["GET", "POST"])
def add_user():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()

        if not name or not email:
            flash("Name and email are required.")
            return render_template("add_user.html", name=name, email=email)

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
            existing_user = cursor.fetchone()

            if existing_user:
                flash("That email already exists.")
                return render_template("add_user.html", name=name, email=email)

            cursor.execute(
                "INSERT INTO users (name, email) VALUES (?, ?)",
                (name, email),
            )
            conn.commit()

        flash("User added successfully.")
        return redirect(url_for("users"))

    return render_template("add_user.html", name="", email="")


@app.route("/log-day", methods=["GET", "POST"])
def log_day():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, email FROM users ORDER BY name")
        all_users = cursor.fetchall()

        if request.method == "POST":
            user_id = request.form.get("user_id", "").strip()
            activity = request.form.get("activity", "").strip()
            today = date.today().isoformat()
            formatted_activity = format_activity_block(activity)

            if not user_id or not formatted_activity:
                flash("Please choose a user and enter an activity.")
                return render_template(
                    "log_day.html",
                    users=all_users,
                    selected_user_id=user_id,
                    activity=activity,
                )

            cursor.execute("SELECT id, name FROM users WHERE id = ?", (user_id,))
            user = cursor.fetchone()

            if not user:
                flash("Selected user was not found.")
                return render_template(
                    "log_day.html",
                    users=all_users,
                    selected_user_id=user_id,
                    activity=activity,
                )

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
                existing_activity = (existing_log["activity"] or "").strip()
                if formatted_activity == existing_activity or formatted_activity in existing_activity:
                    message = f"No changes made to today's log for {user['name']}."
                    saved_activity = existing_activity
                else:
                    updated_activity = f"{existing_activity}\n{formatted_activity}".strip()
                    cursor.execute(
                        """
                        UPDATE daily_logs
                        SET activity = ?, status = ?
                        WHERE id = ?
                        """,
                        (updated_activity, "completed", existing_log["id"]),
                    )
                    message = f"Updated today's log for {user['name']}."
                    saved_activity = updated_activity
            else:
                cursor.execute(
                    """
                    INSERT INTO daily_logs (user_id, date, activity, status)
                    VALUES (?, ?, ?, ?)
                    """,
                    (user_id, today, formatted_activity, "completed"),
                )
                message = f"Created today's log for {user['name']}."
                saved_activity = formatted_activity

            conn.commit()

            email_status = send_log_notification(
                user["name"],
                next(
                    (row["email"] for row in all_users if str(row["id"]) == str(user["id"])),
                    "",
                ),
                saved_activity,
                today,
            )

        else:
            return render_template(
                "log_day.html",
                users=all_users,
                selected_user_id="",
                activity="",
            )

    if email_status == "sent":
        flash(f"{message} Partner notification sent.")
    elif email_status == "skipped":
        flash(f"{message} Email notification skipped for this run.")
    elif email_status == "missing_config":
        flash(f"{message} Log saved, but email settings are missing.")
    elif email_status == "failed":
        flash(f"{message} Log saved, but the email could not be sent.")
    else:
        flash(message)
    return redirect(url_for("logs"))


@app.route("/logs")
def logs():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT daily_logs.id, daily_logs.date, daily_logs.activity, daily_logs.status,
                   users.name, users.email
            FROM daily_logs
            JOIN users ON users.id = daily_logs.user_id
            ORDER BY daily_logs.date DESC, daily_logs.id DESC
            """
        )
        all_logs = cursor.fetchall()

    return render_template("logs.html", logs=all_logs)


init_db()


if __name__ == "__main__":
    app.run(
        host=os.getenv("FLASK_HOST", "0.0.0.0"),
        port=int(os.getenv("FLASK_PORT", "5000")),
        debug=os.getenv("FLASK_DEBUG", "0") == "1",
    )
