# TEG Web App Monorepo

Welcome to the TEG Web App repository. This project is configured as a monorepo, housing both the frontend application and the backend service.

## Structure

- `/frontend` - The Next.js frontend application.
- `/backend` - The Django backend API and services.

## Getting Started

Each directory operates independently. For setup instructions, script commands, and configuration, please refer to the respective documentation in each directory:

* [Frontend README](./frontend/README.md)
* [Backend README](./backend/README.md)

## Development Workflow

1. Navigate to the `frontend/` directory to run the Next.js development server (`npm run dev`).
2. Navigate to the `backend/` directory in a separate terminal to run the Django server (`python manage.py runserver`).

Alternatively, run both from the repo root with `./start.sh` (spawns Django on `:8000` and Next.js on `:3000`).

## Production server

Prod is two long-running processes (Next.js + gunicorn) fronted by nginx. The recommended path on the VPS is via the provided systemd units; the manual commands below mirror what those units do.

### 1. Environment variables (backend)

Copy `backend/.env.example` to `backend/.env` and fill in real values. `backend/core/settings.py` reads:

| Variable | Meaning |
|---|---|
| `SECRET_KEY` | Long random string. Required in prod — falls back to an insecure dev key otherwise. |
| `DEBUG` | Must be `False` in prod. |
| `ALLOWED_HOSTS` | Comma-separated hostnames (e.g. `tesisfar.elevaiti.com`). |
| `CSRF_TRUSTED_ORIGINS` | Comma-separated origins with scheme (e.g. `https://tesisfar.elevaiti.com`). |
| `CORS_ALLOWED_ORIGINS` | Same format as `CSRF_TRUSTED_ORIGINS`. Defaults to `http://localhost:3000` if unset. |
| `SECURE_COOKIES` | Set to `True` only after TLS is live — otherwise login cookies break over HTTP. |

### 2. Backend — migrate, collect static, run gunicorn

From the repo root, with the project virtualenv at `./.venv/`:

```bash
source .venv/bin/activate
pip install -r backend/requirements.txt

set -a; source backend/.env; set +a

python backend/manage.py migrate
python backend/manage.py collectstatic --noinput

cd backend
gunicorn core.wsgi:application --bind 127.0.0.1:8000 --workers 3
```

`gunicorn==23.0.0` is pinned in `backend/requirements.txt`. `core.wsgi:application` is the WSGI entry point defined in `backend/core/wsgi.py`. `collectstatic` writes to `backend/staticfiles/` (gitignored).

### 3. Frontend — build and start Next.js

```bash
cd frontend
npm ci
npm run build     # next build --turbopack
npm start         # next start, listens on PORT (default 3000)
```

Override the port with `PORT=3100 npm start` if you need a non-default bind.

### 4. Reverse proxy

`deploy/nginx.conf` is a ready-to-use vhost for `tesisfar.elevaiti.com` that routes:

- `/api/`, `/media/`, `/static/` → `127.0.0.1:8000` (Django)
- `/` → `127.0.0.1:3000` (Next.js)

Install:

```bash
sudo cp deploy/nginx.conf /etc/nginx/sites-available/teg-web
sudo ln -s /etc/nginx/sites-available/teg-web /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
# Once DNS is pointing:
sudo certbot --nginx -d tesisfar.elevaiti.com
```

### 5. systemd wrapper (recommended)

`deploy/teg-ctl.sh` is a thin wrapper over the `teg-backend` and `teg-frontend` systemd units. Once the units are installed, everyday ops look like:

```bash
sudo deploy/teg-ctl.sh start           # start backend + frontend
sudo deploy/teg-ctl.sh stop
sudo deploy/teg-ctl.sh restart         # or: restart backend | restart frontend
sudo deploy/teg-ctl.sh status          # unit state + listening ports
sudo deploy/teg-ctl.sh logs            # follow combined journalctl
sudo deploy/teg-ctl.sh rebuild         # npm run build + restart frontend
sudo deploy/teg-ctl.sh migrate         # migrate + collectstatic + restart backend
```

The units bind backend on `:8100` and frontend on `:3100` (see the port constants in `deploy/teg-ctl.sh`); adjust `deploy/nginx.conf` to match if you use these ports.
