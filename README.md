# Dashboard Review Portal

A FastAPI and vanilla-JavaScript dashboard-review demo.

## Local setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export JWT_SECRET_KEY="replace-with-a-long-random-secret"
export ADMIN_SETUP_KEY="replace-with-a-random-first-admin-key"
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8001
```

Open `http://127.0.0.1:8001/`.

## Roles

- Viewer: view dashboards and leave ratings/comments.
- Analyst: create dashboards and 24-hour share links.
- Admin: manage dashboards, sections, users, and admin invitations.

Public registration creates viewers only. The first admin is created through `Create first admin` and the server `ADMIN_SETUP_KEY`. Existing admins can generate one-time admin invitation links under Manage users.

## Email integration

The demo does not send email. For production:

- Configure a mail provider such as Resend, SendGrid, AWS SES, or SMTP.
- In password-reset request, generate the token and send `https://your-domain/reset-password/<token>` through that provider.
- In admin-invitation creation, send `https://your-domain/admin/invite/<token>`.
- Store provider credentials only in environment variables or a secret manager.
- Never return a reset or invitation token to an unknown user in production.

## Tests

```bash
pytest -q
```

## Docker

```bash
cp .env.example .env
docker compose up --build
```

## Database

The local demo uses SQLite and stores data in `dashboard_review.db`.

For production:

- Set `DATABASE_URL` to PostgreSQL.
- Use Alembic migrations instead of startup schema patches.
- Back up PostgreSQL regularly.
- For SQLite Docker deployments, back up `/app/data/dashboard_review.db` and keep the Docker volume.

## Production deployment

Deploy with Uvicorn behind HTTPS, set unique `JWT_SECRET_KEY` and `ADMIN_SETUP_KEY`, restrict CORS to the real domain, and use a managed PostgreSQL database.
# Dashboard-Review-Portal-
