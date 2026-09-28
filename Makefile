PYTHON ?= .venv/bin/python
export PYTHONPATH := src

.PHONY: format lint typecheck quality security test package

format:
	$(PYTHON) -m ruff format src tests
	$(PYTHON) -m ruff check --fix src tests

lint:
	$(PYTHON) -m ruff check src tests
	$(PYTHON) -m ruff format --check src tests

typecheck:
	$(PYTHON) -m mypy src

quality: lint typecheck

security:
	$(PYTHON) -m bandit -r src -c pyproject.toml
	$(PYTHON) -m pip_audit --skip-editable

test:
	$(PYTHON) -m pytest -q

package:
	$(PYTHON) -m build --sdist --wheel
