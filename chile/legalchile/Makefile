.PHONY: help setup run stop logs test lint migrate createsuperuser shell fe-add-component deploy-staging deploy-prod

COMPOSE = docker compose
BACKEND = $(COMPOSE) exec backend
FRONTEND = $(COMPOSE) exec frontend

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

setup: ## Build containers and install dependencies
	cp -n .env.example .env 2>/dev/null || true
	$(COMPOSE) build
	docker compose up -d db && sleep 3 && $(BACKEND) python manage.py migrate
	@echo "\n✓ Setup complete. Run 'make run' to start."

run: ## Start all services
	$(COMPOSE) up

run-d: ## Start all services (detached)
	$(COMPOSE) up -d

stop: ## Stop all services
	$(COMPOSE) down

logs: ## Tail service logs
	$(COMPOSE) logs -f

test: ## Run all tests
	$(BACKEND) python manage.py test
	$(FRONTEND) npm test -- --run

lint: ## Run linters
	$(BACKEND) ruff check .
	$(BACKEND) black --check .
	$(FRONTEND) npm run lint

format: ## Auto-format code
	$(BACKEND) ruff check --fix .
	$(BACKEND) black .
	$(FRONTEND) npm run format

migrate: ## Run Django migrations
	$(BACKEND) python manage.py migrate

makemigrations: ## Create new migrations
	$(BACKEND) python manage.py makemigrations

createsuperuser: ## Create Django superuser
	$(BACKEND) python manage.py createsuperuser

shell: ## Django shell
	$(BACKEND) python manage.py shell

fe-add-component: ## Add a shadcn/ui component (usage: make fe-add-component name=button)
	$(FRONTEND) npx shadcn-ui@latest add $(name)

deploy-staging: ## Deploy to staging
	@bash scripts/deploy-staging.sh

deploy-prod: ## Deploy to production
	@bash scripts/deploy-prod.sh
