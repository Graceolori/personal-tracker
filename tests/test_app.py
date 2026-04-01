import importlib
import os
import sys
from pathlib import Path


def load_app_module(tmp_path):
    db_path = tmp_path / "tracker.db"
    log_path = tmp_path / "app.log"

    os.environ["TRACKER_DB_PATH"] = str(db_path)
    os.environ["TRACKER_LOG_PATH"] = str(log_path)
    os.environ["TRACKER_DISABLE_EMAIL"] = "1"
    os.environ["FLASK_SECRET_KEY"] = "test-secret"

    if "app" in sys.modules:
        module = importlib.reload(sys.modules["app"])
    else:
        module = importlib.import_module("app")

    module.init_db()
    return module


def test_health_endpoint(tmp_path):
    module = load_app_module(tmp_path)
    client = module.app.test_client()

    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_add_user_and_log_day(tmp_path):
    module = load_app_module(tmp_path)
    client = module.app.test_client()

    add_user_response = client.post(
        "/add-user",
        data={"name": "Emuobo", "email": "golori84@gmail.com"},
        follow_redirects=True,
    )

    assert add_user_response.status_code == 200
    assert b"User added successfully." in add_user_response.data

    with module.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE email = ?", ("golori84@gmail.com",))
        user = cursor.fetchone()

    assert user is not None

    log_response = client.post(
        "/log-day",
        data={"user_id": str(user["id"]), "activity": "Prayed\nWent to work"},
        follow_redirects=True,
    )

    assert log_response.status_code == 200
    assert b"Email notification skipped for this run." in log_response.data

    with module.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT activity FROM daily_logs WHERE user_id = ?", (user["id"],))
        saved_log = cursor.fetchone()

    assert saved_log is not None
    assert saved_log["activity"] == "- Prayed\n- Went to work"
