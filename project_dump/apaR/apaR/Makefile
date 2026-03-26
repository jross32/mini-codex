.PHONY: install install-frontend install-backend dev dev-frontend dev-backend lint-frontend typecheck-frontend db-upgrade db-migrate db-revision

install: install-backend install-frontend ## Install backend and frontend deps

install-frontend:
	cd frontend && npm install

install-backend:
	cd backend && python -m venv .venv && .venv/Scripts/python -m pip install -r requirements.txt

dev: ## Run backend and frontend in parallel (requires two shells)
	@echo "Start backend: make dev-backend"; \
	echo "Start frontend: make dev-frontend"

dev-frontend:
	cd frontend && npm run dev -- --host

dev-backend:
	cd backend && FLASK_ENV=development CORS_ALLOW_ORIGIN=http://localhost:5173 flask --app app.main run --debug --host=$${API_HOST:-127.0.0.1} --port=$${API_PORT:-5000}

lint-frontend:
	cd frontend && npm run lint

typecheck-frontend:
	cd frontend && npm run build -- --ssr

db-upgrade:
	cd backend && alembic upgrade head

db-migrate:
	cd backend && python -m flask --app app.main migrate

db-revision:
	cd backend && alembic revision --autogenerate -m "auto"
