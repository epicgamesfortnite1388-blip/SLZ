# SLZ ERP — developer shortcuts. Run from the erp/ directory.
.DEFAULT_GOAL := help
COMPOSE := docker compose
BACKEND := $(COMPOSE) exec backend

.PHONY: help up down build logs migrate makemigrations seed test test-backend \
        lint format shell createsuperuser frontend-install frontend-test

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
	awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

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

shell: ## Django shell
	$(BACKEND) python manage.py shell

createsuperuser: ## Create a Django superuser
	$(BACKEND) python manage.py createsuperuser

frontend-install: ## Install frontend deps
	cd frontend && npm install

frontend-test: ## Run frontend tests
	cd frontend && npm run test
