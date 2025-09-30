VENV := venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

.PHONY: help
help:
	@echo "Commands:"
	@echo "  dev    - Setup venv, install from pyproject.toml, run uvicorn (use this every time)"

.PHONY: dev
dev: $(VENV) install
	@echo "Starting server at http://localhost:8000..."
	$(PYTHON) -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

$(VENV):
	python3 -m venv $(VENV)
	@echo "Venv created at $(VENV)."

.PHONY: install
install: $(VENV)
	$(PIP) install -e .
	@echo "Installed from pyproject.toml (editable mode)."