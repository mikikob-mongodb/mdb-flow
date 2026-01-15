.PHONY: help setup verify reset-demo seed-demo test clean dev-setup run run-evals db-init db-verify demo-verify start-app install

# Default target
.DEFAULT_GOAL := help

# Python interpreter
PYTHON := python3
VENV := venv
VENV_PYTHON := $(VENV)/bin/python
VENV_PIP := $(VENV)/bin/pip

##@ General

help: ## Display this help message
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

##@ Setup & Installation

install: ## Install dependencies (creates venv if needed)
	@if [ ! -d "$(VENV)" ]; then \
		echo "Creating virtual environment..."; \
		$(PYTHON) -m venv $(VENV); \
	fi
	@echo "Installing dependencies..."
	@$(VENV_PIP) install -r requirements.txt
	@echo "✅ Dependencies installed"

setup: install ## Complete first-time setup (install + init DB + seed data)
	@echo "Running first-time setup..."
	@$(VENV_PYTHON) scripts/setup/setup.py

dev-setup: install ## Setup for development (install + init DB, no demo data)
	@echo "Running development setup..."
	@$(VENV_PYTHON) scripts/setup/setup.py --skip-seed

##@ Database

db-init: ## Initialize database (collections + indexes)
	@echo "Initializing database..."
	@$(VENV_PYTHON) scripts/setup/init_db.py

db-verify: ## Verify database setup
	@echo "Verifying database..."
	@$(VENV_PYTHON) scripts/setup/init_db.py --verify

##@ Demo & Data

reset-demo: ## Reset demo data (teardown + seed + verify)
	@echo "Resetting demo data..."
	@$(VENV_PYTHON) scripts/demo/reset_demo.py

seed-demo: ## Seed demo data (idempotent)
	@echo "Seeding demo data..."
	@$(VENV_PYTHON) scripts/demo/seed_demo_data.py

demo-verify: ## Verify demo data exists
	@echo "Verifying demo data..."
	@$(VENV_PYTHON) scripts/demo/seed_demo_data.py --verify

##@ Verification & Testing

verify: ## Verify complete setup (environment, DB, APIs)
	@echo "Verifying setup..."
	@$(VENV_PYTHON) scripts/setup/verify_setup.py

verify-quick: ## Quick verification (skip API tests)
	@echo "Quick verification..."
	@$(VENV_PYTHON) scripts/setup/verify_setup.py --quick

test: ## Run test suite
	@echo "Running tests..."
	@$(VENV_PYTHON) -m pytest tests/ -v

test-unit: ## Run unit tests only
	@echo "Running unit tests..."
	@$(VENV_PYTHON) -m pytest tests/unit/ -v

test-integration: ## Run integration tests only
	@echo "Running integration tests..."
	@$(VENV_PYTHON) -m pytest tests/integration/ -v

##@ Running Applications

run: start-app ## Start main Streamlit app (alias for start-app)

start-app: ## Start main Streamlit chat interface
	@echo "Starting Flow Companion..."
	@$(VENV_PYTHON) -m streamlit run ui/streamlit_app.py --server.port 8501

run-evals: ## Start evals comparison app
	@echo "Starting Evals app..."
	@$(VENV_PYTHON) -m streamlit run evals_app.py --server.port 8502

##@ Cleanup & Maintenance

clean: ## Remove build artifacts and caches
	@echo "Cleaning artifacts..."
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type f -name "*.pyo" -delete 2>/dev/null || true
	@echo "✅ Artifacts cleaned"

clean-all: clean ## Remove everything including venv
	@echo "Removing virtual environment..."
	@rm -rf $(VENV)
	@echo "✅ Complete cleanup done"

db-cleanup: ## Run database cleanup script
	@echo "Running database cleanup..."
	@$(VENV_PYTHON) scripts/maintenance/cleanup_database.py --full

##@ Development

dev-test-memory: ## Test memory system (development)
	@echo "Testing memory system..."
	@$(VENV_PYTHON) scripts/dev/test_memory_system.py

dev-debug-agent: ## Run agent debugger
	@echo "Running agent debugger..."
	@$(VENV_PYTHON) scripts/dev/debug/debug_agent.py

##@ Quick Workflows

demo-prep: reset-demo verify ## Prepare for demo (reset + verify)
	@echo "✅ Demo ready!"

first-run: install setup verify start-app ## Complete first-run workflow

quick-start: install db-init seed-demo start-app ## Quick start (skip full setup)

fresh-start: clean-all install setup ## Fresh installation from scratch
