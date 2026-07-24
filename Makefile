.PHONY: help install lint fmt test check run clean

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  %-10s %s\n", $$1, $$2}'

install:  ## Install runtime + dev dependencies
	pip install -r requirements.txt
	pip install -e ".[dev]"

lint:  ## Run ruff linter
	ruff check backend tests

fmt:  ## Auto-fix lint issues where possible
	ruff check --fix backend tests

test:  ## Run the test suite
	pytest

check: lint test  ## Lint and test (what CI runs)

run:  ## Start the web demo on http://localhost:8000
	python run.py

clean:  ## Remove Python caches
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache .ruff_cache
