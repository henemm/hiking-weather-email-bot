.PHONY: test lint format clean setup run

# Python-Interpreter
PYTHON = python3
VENV = venv

# Entwicklungsumgebung einrichten
setup:
	$(PYTHON) -m venv $(VENV)
	. $(VENV)/bin/activate && pip install -r requirements.txt
	. $(VENV)/bin/activate && pip install -r requirements-dev.txt

# Tests ausführen
test:
	. $(VENV)/bin/activate && $(PYTHON) -m pytest tests/ -v

# Code-Formatierung prüfen
lint:
	. $(VENV)/bin/activate && flake8 wetter/ tests/
	. $(VENV)/bin/activate && mypy wetter/ tests/

# Code formatieren
format:
	. $(VENV)/bin/activate && black wetter/ tests/
	. $(VENV)/bin/activate && isort wetter/ tests/

# Aufräumen
clean:
	rm -rf __pycache__
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	find . -type d -name "__pycache__" -exec rm -r {} +

# Programm ausführen
run:
	. $(VENV)/bin/activate && $(PYTHON) main.py

# Tägliche Entwicklung
dev: format lint test

# Deployment vorbereiten
deploy: clean format lint test 