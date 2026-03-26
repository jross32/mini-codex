# WhatAPC

Full-stack starter for the WhatAPC custom PC shop.

## Stack
- Backend: Flask, SQLAlchemy, SQLite (default), CORS
- Frontend: React + Vite + TailwindCSS

## Quick start
1) Backend
```bash
cd backend
python -m venv .venv && .venv\\Scripts\\activate
pip install -r requirements.txt
cp .env.example .env  # adjust CORS_ORIGINS / DATABASE_URL as needed
python app.py  # creates sqlite DB + seeds sample data; serves on http://localhost:5000
```

2) Frontend
```bash
cd frontend
npm install
cp .env.example .env  # point to your API if not localhost
npm run dev  # http://localhost:5173
```

- API base can be overridden with `VITE_API_BASE` in `frontend/.env` (defaults to `http://localhost:5000/api`).
- Ready-to-ship builds, FAQ, and custom quote form will use live API if available; otherwise fallback copy is shown.

## Deployment notes
- Replace SQLite URL via `DATABASE_URL` env for Postgres or MySQL.
- CORS origins can be restricted with `CORS_ORIGINS`.
- `python app.py` runs in debug; use a WSGI server (gunicorn/uwsgi) for production.

### Production (gunicorn + Postgres)
```bash
cd backend
python -m venv .venv && .venv\\Scripts\\activate
pip install -r requirements.txt
set DATABASE_URL=postgresql+psycopg2://user:pass@host:5432/whatapc
set CORS_ORIGINS=https://whatapc.com,https://www.whatapc.com
set PORT=5000
python -c "from app import init_db; init_db()"  # run once to create tables
gunicorn -b 0.0.0.0:5000 app:app
```

### Production (uWSGI sample)
`whatapc.ini`
```
[uwsgi]
module = app:app
master = true
processes = 4
http = :5000
env = DATABASE_URL=postgresql+psycopg2://user:pass@host:5432/whatapc
env = CORS_ORIGINS=https://whatapc.com,https://www.whatapc.com
```
Run with: `uwsgi --ini whatapc.ini`

Notes:
- Ensure your reverse proxy (nginx/ALB) forwards `X-Forwarded-*` if you need HTTPS detection.
- Keep `CORS_ORIGINS` to your real domains to avoid wildcard exposure.

## Connect your domain (recommended: single domain + /api proxy)
This project now supports production API calls at `/api` by default, so one domain can serve both frontend and backend.

1) DNS records (at your domain registrar)
- Create `A` record for `@` -> your server public IP.
- Create `A` record for `www` -> your server public IP.

2) Build frontend on server
```bash
cd /var/www/whatapc/frontend
cp .env.production.example .env.production
npm ci
npm run build
```

3) Configure backend service (gunicorn)
```bash
cd /var/www/whatapc/backend
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
sudo mkdir -p /etc/whatapc
sudo cp /var/www/whatapc/deploy/env/whatapc.env.example /etc/whatapc/whatapc.env
sudo nano /etc/whatapc/whatapc.env  # set DATABASE_URL and real domains
.venv/bin/python -c "from app import init_db; init_db()"
sudo cp /var/www/whatapc/deploy/systemd/whatapc-backend.service /etc/systemd/system/whatapc-backend.service
sudo systemctl daemon-reload
sudo systemctl enable --now whatapc-backend
```

4) Configure nginx for your domain
```bash
sudo cp /var/www/whatapc/deploy/nginx/whatapc.conf /etc/nginx/sites-available/whatapc.conf
sudo ln -s /etc/nginx/sites-available/whatapc.conf /etc/nginx/sites-enabled/whatapc.conf
sudo nginx -t
sudo systemctl reload nginx
```

5) TLS certificate (Let's Encrypt)
```bash
sudo apt-get update
sudo apt-get install -y certbot python3-certbot-nginx
sudo certbot --nginx -d whatapc.com -d www.whatapc.com
```

6) Verify
- `https://whatapc.com` serves frontend.
- `https://whatapc.com/api/health` returns `{"status":"ok"}`.
- Backend service is healthy: `sudo systemctl status whatapc-backend`.
