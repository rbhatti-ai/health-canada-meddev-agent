bootstrap:
	@echo ">>> Bootstrapping venv + dependencies"
	@if [ ! -x venv/bin/python ]; then python3 -m venv venv; fi
	@$(PIP) install --upgrade pip
	@if [ -f requirements.txt ]; then $(PIP) install -r requirements.txt; fi
	@$(PIP) install pytest

# =============================================================================
# Makefile — Health Canada MedDev Agent
# Dev automation for a regulated-grade platform
# =============================================================================
# Usage:
#   make help          Show all targets
#   make test          Run full test suite
#   make db-verify     Show current DB state (tables, RLS, policies)
#   make db-migrate    Apply all migrations to local Postgres
#   make snapshot      Generate project state snapshot
#   make lint          Run all linters
#   make checkpoint    Full verify + test + snapshot + commit
# =============================================================================

# Python interpreter (prefers ./venv if present)
PY ?= $(shell if [ -x venv/bin/python ]; then echo venv/bin/python; else echo python3; fi)
PIP ?= $(PY) -m pip

.PHONY: checkpoint clean daily help test test-api test-daily test-integration test-performance test-rag test-regulatory test-unit test-weekly weekly

	test-coverage lint lint-ruff lint-mypy lint-black \
	db-verify db-migrate snapshot checkpoint clean

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------
PYTHON     := python3
PYTEST     := $(PYTHON) -m pytest
VENV_ACT   := source venv/bin/activate &&
DB_USER    := meddev
DB_NAME    := meddev_agent
PSQL       := psql -U $(DB_USER) -d $(DB_NAME)
TZ_CMD     := TZ='America/Edmonton' date '+%Y-%m-%d %H:%M MST'
SNAPSHOT   := docs/PROJECT_STATE_SNAPSHOT.md

# -----------------------------------------------------------------------------
# Help
# -----------------------------------------------------------------------------
help: ## Show this help
	@echo "Health Canada MedDev Agent — Dev Targets"
	@echo "========================================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

# -----------------------------------------------------------------------------
# Testing
# -----------------------------------------------------------------------------
test: ## Run full test suite (122+ tests)
	$(VENV_ACT) $(PYTEST) -v --tb=short

test-unit: ## Run unit tests only
	$(VENV_ACT) $(PYTEST) tests/unit/ -v --tb=short

test-api: ## Run API endpoint tests
	$(VENV_ACT) $(PYTEST) tests/api/ -v --tb=short

test-coverage: ## Run tests with coverage report
	$(VENV_ACT) $(PYTEST) --cov=src --cov-report=term-missing --tb=short

# -----------------------------------------------------------------------------
# Linting
# -----------------------------------------------------------------------------
lint: lint-ruff lint-black ## Run all linters (except mypy — tech debt)

lint-ruff: ## Run ruff linter
	$(VENV_ACT) ruff check src/ tests/

lint-black: ## Check formatting with black
	$(VENV_ACT) black --check src/ tests/

lint-mypy: ## Run mypy (note: 34 pre-existing errors)
	$(VENV_ACT) mypy src/

# -----------------------------------------------------------------------------
# Database
# -----------------------------------------------------------------------------
db-verify: ## Show current DB state (tables, RLS, policies)
	@echo "=== Tables ==="
	@$(PSQL) -c "\dt public.*"
	@echo ""
	@echo "=== RLS State ==="
	@$(PSQL) -c "SELECT tablename, rowsecurity FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename;"
	@echo ""
	@echo "=== Policies ==="
	@$(PSQL) -c "SELECT tablename, policyname, cmd FROM pg_policies WHERE schemaname = 'public' ORDER BY tablename, policyname;"
	@echo ""
	@echo "=== Foreign Keys ==="
	@$(PSQL) -c "SELECT conrelid::regclass AS table_name, conname AS constraint_name, confrelid::regclass AS referenced_table FROM pg_constraint WHERE contype = 'f' AND connamespace = 'public'::regnamespace ORDER BY conrelid::regclass::text;"

db-migrate: ## Apply all migrations to local Postgres
	@echo "=== Applying base schema ==="
	$(PSQL) -f scripts/supabase_schema_v0.sql
	@echo ""
	@echo "=== Applying ai_runs + trace_links migration ==="
	$(PSQL) -f scripts/migrations/2026-02-06_ai_runs_and_trace_links.sql
	@echo ""
	@echo "=== Applying artifacts + attestations migration ==="
	$(PSQL) -f scripts/migrations/2026-02-06_artifacts_and_attestations.sql
	@echo ""
	@echo "=== Applying RLS policies migration ==="
	$(PSQL) -f scripts/migrations/2026-02-06_rls_policies_artifacts_attestations.sql
	@echo ""
	@echo "=== Migration complete. Verifying... ==="
	@$(MAKE) db-verify

snapshot: ## Generate project state snapshot as Markdown
	@$(VENV_ACT) $(PYTHON) scripts/snapshot.py

# -----------------------------------------------------------------------------
# Checkpoint (full verify cycle)
# -----------------------------------------------------------------------------
checkpoint: ## Full: test + db-verify + snapshot (run before commits)
	@echo "══════════════════════════════════════════════"
	@echo "  PROJECT CHECKPOINT"
	@echo "  $$(TZ='America/Edmonton' date '+%Y-%m-%d %H:%M MST')"
	@echo "══════════════════════════════════════════════"
	@echo ""
	@echo ">>> Running full test suite..."
	@$(MAKE) test
	@echo ""
	@echo ">>> Verifying database state..."
	@$(MAKE) db-verify
	@echo ""
	@echo ">>> Generating snapshot..."
	@$(MAKE) snapshot
	@echo ""
	@echo "Checkpoint complete at $$(TZ='America/Edmonton' date '+%Y-%m-%d %H:%M MST')"

# -----------------------------------------------------------------------------
# Clean
# -----------------------------------------------------------------------------
clean: ## Remove caches and temp files
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	rm -f *.bak src/**/*.bak tests/**/*.bak

# Friendly aliases (so you only remember "daily" and "weekly")
# -----------------------------------------------------------------------------
# Test shortcuts (managed)
# -----------------------------------------------------------------------------

# Friendly aliases (so you only remember "daily" and "weekly")
daily: test-daily
weekly: test-weekly

# Fast sweep (most often)
test-daily:
	$(PY) -m pytest tests/unit tests/api -q --durations=10

# Weekly depth (RAG + regulatory + integration)
test-weekly: test-rag test-regulatory test-integration

test-rag:
	$(PY) -m pytest tests/rag -q

test-regulatory:
	$(PY) -m pytest tests/regulatory -q

# Integration often needs services; bring up docker compose if present, and always tear down.
test-integration:
	@set -e; \
	if [ -f docker-compose.yml ]; then docker compose up -d; fi; \
	trap 'if [ -f docker-compose.yml ]; then docker compose down -v; fi' EXIT; \
	$(PY) -m pytest tests/integration -q

test-performance:
	$(PY) -m pytest tests/performance -q
