SHELL=bash
POETRY := poetry
SRC_DIR := dream_interpreter
TEST_DIR := tests
PYLINT_THRESHOLD := 8
PORT := 8000

# Default target
.DEFAULT_GOAL := help

.PHONY: help
help:
	@echo "Available targets:"
	@echo "  install    		- Install project dependencies using Poetry"
	@echo "  install-ci 		- Install project dependencies using Poetry in a CI environment"
	@echo "  test       		- Run tests using pytest"
	@echo "  test-coverage		- Run tests with coverage report"
	@echo "  lint       		- Run linter on Python files"
	@echo "  lint-ci    		- Run linter and fail if score is below $(PYLINT_THRESHOLD)"
	@echo "  fmt        		- Format Python files using Black and isort"
	@echo "  run        		- Start the FastAPI development server"
	@echo "  setup-nltk 		- Download required NLTK data"
	@echo "  clean      		- Clean up build artifacts and cache"

.PHONY: install
install:
	$(POETRY) install

.PHONY: install-ci
install-ci:
	$(POETRY) install --no-interaction --no-root

.PHONY: test
test:
	$(POETRY) run pytest

.PHONY: test-coverage
test-coverage:
	$(POETRY) run pytest --cov=$(SRC_DIR) --cov-report=xml:coverage.xml --cov-report=term-missing

.PHONY: lint
lint:
	$(POETRY) run pylint $(SRC_DIR) $(TEST_DIR)

.PHONY: lint-ci
lint-ci:
	$(POETRY) run pylint --fail-under=$(PYLINT_THRESHOLD) $(shell find $(SRC_DIR) -name "*.py")
	$(POETRY) run pylint --fail-under=$(PYLINT_THRESHOLD) $(shell find $(TEST_DIR) -name "*.py")

.PHONY: fmt
fmt:
	$(POETRY) run isort $(SRC_DIR) $(TEST_DIR)
	$(POETRY) run black $(SRC_DIR) $(TEST_DIR)

.PHONY: run
run:
	$(POETRY) run uvicorn $(SRC_DIR).main:app --reload --host 0.0.0.0 --port $(PORT)

.PHONY: setup-nltk
setup-nltk:
	$(POETRY) run python -c "import nltk; nltk.download('punkt', quiet=True)"
	$(POETRY) run python -c "import nltk; nltk.download('brown', quiet=True)"

.PHONY: clean
clean:
	rm -rf dist/
	rm -rf build/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete