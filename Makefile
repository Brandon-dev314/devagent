

.PHONY: help up down build logs test lint clean

help: ## Muestra esta ayuda
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

# ── Docker ───────────────────────────────────────────────
up: ## Levanta todos los servicios
	docker compose up -d

up-build: ## Levanta todos los servicios reconstruyendo imágenes
	docker compose up -d --build

down: ## Apaga todos los servicios
	docker compose down

down-clean: ## Apaga todo Y borra volúmenes (⚠️ borra datos)
	docker compose down -v

logs: ## Muestra logs en tiempo real
	docker compose logs -f

logs-api: ## Muestra logs solo de la API
	docker compose logs -f api

ps: ## Muestra estado de los servicios
	docker compose ps


dev: ## Levanta solo la API en modo desarrollo (sin Docker)
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

test: ## Corre los tests
	cd backend && python -m pytest tests/ -v

test-cov: ## Corre tests con reporte de cobertura
	cd backend && python -m pytest tests/ -v --cov=app --cov-report=html

lint: ## Corre linters (ruff)
	cd backend && ruff check app/ tests/

format: ## Formatea código automáticamente
	cd backend && ruff format app/ tests/

clean: ## Limpia archivos temporales
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true

db-shell: ## Abre una shell de PostgreSQL
	docker compose exec postgres psql -U devagent -d devagent

redis-shell: 
	docker compose exec redis redis-cli