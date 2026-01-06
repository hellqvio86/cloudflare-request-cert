.PHONY: help venv install sync dev run clean lint format check test

# Default target
help:
	@echo "Cloudflare Certificate Request Tool"
	@echo ""
	@echo "Available targets:"
	@echo "  venv                 - Create virtual environment"
	@echo "  install              - Install uv and sync dependencies (alias for venv)"
	@echo "  sync                 - Sync dependencies with uv"
	@echo "  dev                  - Install development dependencies"
	@echo "  run                  - Run the certificate request tool"
	@echo "  lint                 - Lint code with ruff"
	@echo "  format               - Format code with ruff"
	@echo "  check                - Run all checks (lint + format check)"
	@echo "  test                 - Run tests"
	@echo "  clean                - Remove virtual environment and cache files"
	@echo ""
	@echo "Usage examples:"
	@echo "  make run DOMAIN=example.com EMAIL=admin@example.com"
	@echo "  make run DOMAIN=example.com EMAIL=admin@example.com STAGING=1"

# Create virtual environment and install dependencies
venv:
	@command -v uv >/dev/null 2>&1 || { \
		echo "Installing uv..."; \
		curl -LsSf https://astral.sh/uv/install.sh | sh; \
	}
	@echo "Creating virtual environment and syncing dependencies..."
	uv sync

# Alias for venv
install: venv

# Sync dependencies
sync:
	uv sync

# Install development dependencies
dev:
	uv sync --all-extras

# Run the tool
run:
ifndef DOMAIN
	@echo "Error: DOMAIN is required"
	@echo "Usage: make run DOMAIN=example.com EMAIL=admin@example.com"
	@exit 1
endif
ifndef EMAIL
	@echo "Error: EMAIL is required"
	@echo "Usage: make run DOMAIN=example.com EMAIL=admin@example.com"
	@exit 1
endif
	@if [ "$(STAGING)" = "1" ]; then \
		uv run python cloudflare_cert.py -d $(DOMAIN) -e $(EMAIL) --staging; \
	else \
		uv run python cloudflare_cert.py -d $(DOMAIN) -e $(EMAIL); \
	fi

# Lint with ruff
lint:
	uv run ruff check .

# Format code
format:
	uv run ruff format .

# Run all checks
check: lint
	uv run ruff format --check .

# Run tests
test:
	uv run pytest tests/ -v

# Clean up
clean:
	rm -rf .venv/
	rm -rf .ruff_cache/
	rm -rf .pytest_cache/
	rm -rf __pycache__/
	rm -rf *.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	@echo "Cleaned up cache and virtual environment"