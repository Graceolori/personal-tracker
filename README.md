# Personal Tracker

Personal Tracker is a lightweight Flask web application for recording daily check-ins between two people. It helps users log what they achieved during the day, keep a simple history of progress, and notify the other partner when a new update is submitted.

The goal of the app is to make accountability easy. Instead of sending scattered updates through chat, both users can store their daily progress in one shared place, review recent activity, and build a consistent check-in habit over time.

## What The App Does

- lets you create users with a name and email address
- allows a user to submit a daily activity log from the browser
- stores logs in SQLite so the history is easy to manage
- shows recent activity on the dashboard
- displays all submitted logs on a dedicated logs page
- sends an email notification to the other partner when a log is submitted
- writes application and email errors to a local log file for troubleshooting

## Why This Project Exists

The app is designed for simple personal accountability. It is useful for:

- partners keeping each other updated on daily goals
- friends checking in on habits or routines
- small personal productivity tracking without needing a large external platform
- learning how to build and ship a full Python project with Flask, SQLite, Docker, and GitHub Actions

## Main Workflow

1. Add users to the tracker.
2. Open the `Log Day` page and choose the user who is checking in.
3. Submit one or more completed activities.
4. Save the log to the database.
5. Notify the other partner by email when email delivery is enabled.
6. Review saved activity from the dashboard and logs page.

## Pages In The App

- `Dashboard`
  Shows user count, total logs, and the most recent activity.
- `Add User`
  Adds a new user to the tracker.
- `Log Day`
  Records a check-in for the selected user.
- `Users`
  Lists all registered users.
- `Logs`
  Shows the full history of stored daily logs.

## Tech Stack

- `Python`
- `Flask`
- `SQLite`
- `HTML/CSS`
- `Docker`
- `GitHub Actions`

## Project Structure

```text
personal_tracker/
  app.py
  cleanup.py
  requirements.txt
  Dockerfile
  docker-compose.yml
  templates/
  tests/
  .github/workflows/
```

## Local Configuration

The app reads configuration from a local `.env` file. Typical values include:

```env
TRACKER_SENDER_EMAIL=yourgmail@gmail.com
TRACKER_SENDER_PASSWORD=your-gmail-app-password
TRACKER_PARTNER_EMAIL=partner@example.com
TRACKER_DISABLE_EMAIL=0
FLASK_SECRET_KEY=replace-this-with-a-random-secret
```

Notes:

- `TRACKER_SENDER_PASSWORD` should be a Gmail App Password, not your normal password
- set `TRACKER_DISABLE_EMAIL=1` if you want to test logging without sending email

## Run Locally

```powershell
pip install -r requirements.txt
python app.py
```

The app runs on `http://127.0.0.1:5000`.

## Run With Docker

```powershell
docker compose up --build
```

The container stores SQLite data and logs in a Docker volume mounted at `/app/data`.

## Logging And Troubleshooting

- application logs are written to `app.log`
- email delivery issues are recorded there with timestamps
- the app exposes `GET /health` for health checks in Docker and CI/CD environments

## Testing

The project includes a small test suite for the Flask app:

```powershell
pytest -q
```

The tests cover:

- health endpoint availability
- adding a user
- saving a daily log
- storing activity in the expected format

## CI/CD And DevOps

The GitHub Actions workflow in `.github/workflows/ci-cd.yml` is designed to support a full delivery pipeline.

It currently:

- runs `pytest`
- scans Python code with `bandit`
- audits dependencies with `pip-audit`
- builds a Docker image
- pushes the image to Docker Hub on pushes to `main`
- scans the image with Trivy
- optionally deploys the container to a remote Docker host over SSH

## GitHub Secrets Required

Add these secrets in your GitHub repository under `Settings` -> `Secrets and variables` -> `Actions`:

- `DOCKERHUB_USERNAME`
- `DOCKERHUB_TOKEN`
- `FLASK_SECRET_KEY`
- `TRACKER_SENDER_EMAIL`
- `TRACKER_SENDER_PASSWORD`
- `TRACKER_PARTNER_EMAIL`
- `TRACKER_DISABLE_EMAIL`

Optional deploy secrets:

- `DEPLOY_HOST`
- `DEPLOY_USERNAME`
- `DEPLOY_SSH_KEY`

## Deployment Goal

This project is set up to be more than just a local Flask app. It is meant to demonstrate:

- building a small but useful productivity tool
- storing data with SQLite
- sending transactional email notifications
- containerizing a Python web app with Docker
- scanning and shipping code through GitHub Actions
- preparing an app for deployment through an automated pipeline

## Future Improvements

- add user authentication
- add edit and delete options for individual logs
- improve email reliability and delivery diagnostics
- support more than two accountability partners
- add charts or summaries for progress over time
