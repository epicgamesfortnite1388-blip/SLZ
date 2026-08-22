# SLZ ERP — developer shortcuts. Run from the erp/ directory.
#
# Two execution modes:
#   make <target>          → runs inside the Docker Compose stack (needs Docker)
#   make *-local variants  → run directly on the host (Python venv / node_modules)
.DEFAULT_GOAL := help
COMPOSE := docker compose
BACKEND := $(COMPOSE) exec backend

.PHONY: help up down build logs migrate makemigrations migrations-check seed \
        test test-backend lint format verify shell createsuperuser \
        frontend-install frontend-test frontend-typecheck frontend-lint \
        frontend-build test-backend-local migrations-check-local verify-local \
        test-frontend-local

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
	awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-24s\033[0m %s\n", $$1, $$2}'

up: ## Start the full stack (build if needed)
	$(COMPOSE) up --build

down: ## Stop the stack
	$(COMPOSE) down

build: ## Build all images
	$(COMPOSE) build

logs: ## Tail backend logs
	$(COMPOSE) logs -f backend

migrate: ## Apply DB migrations
	$(BACKEND) python manage.py migrate

makemigrations: ## Generate migrations
	$(BACKEND) python manage.py makemigrations

migrations-check: ## Fail if model changes lack committed migrations
	$(BACKEND) python manage.py makemigrations --check --dry-run --noinput

seed: ## Seed platform RBAC (permissions + admin role)
	$(BACKEND) python manage.py seed_rbac

test: test-backend frontend-test ## Run all tests

test-backend: ## Run the backend test suite (SQLite, no external services)
	$(BACKEND) python manage.py test --settings=config.settings.test --noinput

lint: ## Lint backend (flake8) and check formatting
	$(BACKEND) flake8 apps config
	$(BACKEND) black --check apps config
	$(BACKEND) isort --check-only apps config

format: ## Auto-format backend
	$(BACKEND) black apps config
	$(BACKEND) isort apps config

verify: migrations-check test lint ## Full CI-equivalent verification (Docker)

shell: ## Django shell
	$(BACKEND) python manage.py shell

createsuperuser: ## Create a Django superuser
	$(BACKEND) python manage.py createsuperuser

frontend-install: ## Install frontend deps (locked; matches CI)
	cd frontend && npm ci

frontend-test: ## Run frontend tests
	cd frontend && npm run test

frontend-typecheck: ## Typecheck the frontend
	cd frontend && npm run typecheck

frontend-lint: ## Lint the frontend
	cd frontend && npm run lint

frontend-build: ## Production build of the frontend
	cd frontend && npm run build

# --- Local (host) variants: no Docker required -----------------------------

test-backend-local: ## Run backend tests on the host (venv with dev requirements)
	cd backend && python manage.py test --settings=config.settings.test --noinput

migrations-check-local: ## Migration drift check on the host
	cd backend && python manage.py makemigrations --check --dry-run --noinput

lint-local: ## Backend lint + format checks on the host
	cd backend && flake8 apps config && black --check apps config && isort --check-only apps config

verify-local: migrations-check-local lint-local test-backend-local frontend-typecheck frontend-lint frontend-test frontend-build ## CI-equivalent verification without Docker

test-frontend-local: frontend-test ## Alias for frontend tests on the host
