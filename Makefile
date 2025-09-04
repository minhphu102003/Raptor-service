# Makefile for RAPTOR Service

# Variables
COMPOSE_DEV = docker-compose.yml
COMPOSE_PROD = docker-compose.prod.yml

# Default target
.PHONY: help
help: ## Show this help
	@echo "Usage: make [target]"
	@echo ""
	@echo "Available targets:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

.PHONY: setup
setup: ## Setup the project (copy .env.example to .env)
	cp .env.example .env

.PHONY: dev
dev: ## Start development environment
	docker-compose -f $(COMPOSE_DEV) up --build

.PHONY: dev-detached
dev-detached: ## Start development environment in detached mode
	docker-compose -f $(COMPOSE_DEV) up --build -d

.PHONY: stop
stop: ## Stop development environment
	docker-compose -f $(COMPOSE_DEV) down

.PHONY: prod
prod: ## Start production environment
	docker-compose -f $(COMPOSE_PROD) up --build

.PHONY: prod-detached
prod-detached: ## Start production environment in detached mode
	docker-compose -f $(COMPOSE_PROD) up --build -d

.PHONY: prod-stop
prod-stop: ## Stop production environment
	docker-compose -f $(COMPOSE_PROD) down

.PHONY: logs
logs: ## Show logs for development environment
	docker-compose -f $(COMPOSE_DEV) logs -f

.PHONY: logs-api
logs-api: ## Show logs for API service
	docker-compose -f $(COMPOSE_DEV) logs -f api

.PHONY: logs-web
logs-web: ## Show logs for web service
	docker-compose -f $(COMPOSE_DEV) logs -f web

.PHONY: test
test: ## Run tests in Docker
	docker-compose -f $(COMPOSE_DEV) run api pytest

.PHONY: shell-api
shell-api: ## Open shell in API container
	docker-compose -f $(COMPOSE_DEV) exec api sh

.PHONY: shell-web
shell-web: ## Open shell in web container
	docker-compose -f $(COMPOSE_DEV) exec web sh

.PHONY: build-api
build-api: ## Build API Docker image
	docker build --target dev -t raptor-api .

.PHONY: build-web
build-web: ## Build web Docker image
	docker build -t raptor-web ./frontend

.PHONY: clean
clean: ## Remove Docker containers, networks, and volumes
	docker-compose -f $(COMPOSE_DEV) down -v
	docker-compose -f $(COMPOSE_PROD) down -v

.PHONY: ps
ps: ## Show running containers
	docker-compose -f $(COMPOSE_DEV) ps
