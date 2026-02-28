.PHONY: help venv install sync dev run sudo-run clean lint format check test build publish

# Default target
help:
	@echo "Cloudflare Certificate Request Tool"
	@echo ""
	@echo "Available targets:"
	@echo "  venv                 - Create virtual environment"
	@echo "  install              - Install uv and sync dependencies (alias for venv)"
	@echo "  sync                 - Sync dependencies with uv"
	@echo "  dev                  - Install development dependencies"
	@echo "  run                  - Run the tool normally (using uv run)"
	@echo "  sudo-run             - Run the tool with sudo (use this for production certs)"
	@echo "  lint                 - Lint code with ruff"
	@echo "  format               - Format code with ruff"
	@echo "  check                - Run all checks (lint + format check)"
	@echo "  test                 - Run tests"
	@echo "  sbom                 - Generate SBOM (Software Bill of Materials)"
	@echo "  build                - Build source and wheel distributions"
	@echo "  publish              - Publish package to PyPI"
	@echo "  clean                - Remove virtual environment and cache files"
	@echo ""
	@echo "Usage examples:"
	@echo "  make run DOMAIN=example.com EMAIL=admin@example.com STAGING=1"
	@echo "  make sudo-run DOMAIN=example.com EMAIL=admin@example.com"

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

# Detect uv path to handle sudo environments where PATH is stripped
UV := $(shell command -v uv 2>/dev/null || which uv 2>/dev/null || echo uv)

# Run the tool normally (e.g. for staging/testing)
run:
	uv run python -m cloudflare_request_cert.main \
		$(if $(DOMAIN),-d $(DOMAIN)) \
		$(if $(EMAIL),-e $(EMAIL)) \
		$(if $(STAGING),--staging)

# Run the tool with sudo (required for Certbot locks in /var/log/letsencrypt)
# We use the virtual environment Python directly to avoid PATH issues with 'uv' under sudo
sudo-run:
	@if [ ! -f .venv/bin/python ]; then \
		echo "❌ Error: Virtual environment not found. Run 'make install' first."; \
		exit 1; \
	fi
	sudo ./.venv/bin/python -m cloudflare_request_cert.main \
		$(if $(DOMAIN),-d $(DOMAIN)) \
		$(if $(EMAIL),-e $(EMAIL)) \
		$(if $(STAGING),--staging)

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

# Generate SBOM
sbom:
	uv run cyclonedx-py environment --output-file bom.json

# Build package
build:
	uv build

# Publish package
publish: build
	uv publish

# Clean up
clean:
	rm -rf .venv/
	rm -rf .ruff_cache/
	rm -rf .pytest_cache/
	rm -rf __pycache__/
	rm -rf *.egg-info/
	rm -rf dist/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	@echo "Cleaned up cache and virtual environment"
