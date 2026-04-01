# Personal Tracker

Small Flask app for shared daily check-ins, backed by SQLite.

## Run Locally

```powershell
cd c:\Users\User\Documents\personal_tracker
pip install -r requirements.txt
python app.py
```

The app runs on `http://127.0.0.1:5000`.

## Run With Docker

```powershell
docker compose up --build
```

The container stores SQLite data and logs in a Docker volume mounted at `/app/data`.

## Push To GitHub And Docker Hub

1. Create a GitHub repository and push this project.
2. Create a Docker Hub repository named `personal-tracker`.
3. Add these GitHub Actions secrets in your repository settings:

- `DOCKERHUB_USERNAME`
- `DOCKERHUB_TOKEN`
- `FLASK_SECRET_KEY`
- `TRACKER_SENDER_EMAIL`
- `TRACKER_SENDER_PASSWORD`
- `TRACKER_PARTNER_EMAIL`
- `TRACKER_DISABLE_EMAIL`

Optional deploy secrets for automatic server deployment:

- `DEPLOY_HOST`
- `DEPLOY_USERNAME`
- `DEPLOY_SSH_KEY`

## CI/CD Workflow

The workflow in `.github/workflows/ci-cd.yml` does this:

- runs `pytest`
- scans Python code with `bandit`
- audits dependencies with `pip-audit`
- builds and pushes a Docker image to Docker Hub on pushes to `main`
- scans the pushed image with Trivy
- deploys the latest image to a Docker host over SSH when deploy secrets are configured

## Health Check

The app exposes `GET /health` for container and deployment checks.
