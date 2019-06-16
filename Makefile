VENV = venv

all: help

venv:
	python3 -m venv $(VENV)
	$(VENV)/bin/pip install --upgrade pip

rmenv:
	rm -rf $(VENV)

db-init: venv
	$(VENV)/bin/unsafe-initdb

db-reset:
	$(VENV)/bin/unsafe-initdb --reset

db-clean:
	rm -rf *.db

bdist build check develop install sdist: venv
	$(VENV)/bin/python setup.py $@

# Install extras (se setup.cfg for aliases)
dev docs qa: venv
	$(VENV)/bin/python setup.py $@

test:
	$(VENV)/bin/pytest

coverage cov:
	$(VENV)/bin/pytest --cov

run run-dev:
	$(VENV)/bin/unsafe --reload development.ini

run-prod:
	$(VENV)/bin/unsafe production.ini

clean:
	rm -rf build .coverage dist .eggs .pytest_cache .ptype test*.db sessions.db *.log
	find . -name __pycache__ -delete

reallyclean: clean db-clean

distclean: reallyclean rmenv
	rm -rf *.egg-info


help:
	@echo "Setup:"
	@echo "  > make dev"
	@echo
	@echo "Run:"
	@echo "  > make run"
	@echo
	@echo "Setup targets:"
	@echo "  dev            install extras for development"
	@echo "  docs           install extras for documentation"
	@echo "  qa             install extras for quality assurance"
	@echo "  venv           create virtual environment and upgrade pip"
	@echo
	@echo "Test targets:"
	@echo "  cov, coverage  run unit tests with coverage"
	@echo "  test           run unit tests"
	@echo
	@echo "Database targets:"
	@echo "  db-clean       remove database files"
	@echo "  db-init        create and initialize database if it does not exist"
	@echo "  db-reset       recreate database from scratch"
	@echo
	@echo "Running:"
	@echo "  run, run-dev   run with development.ini (or make run)"
	@echo "  run-prod       run with production.ini"
	@echo
	@echo "Cleaning:"
	@echo "  clean          remove build files and temporary data"
	@echo "  reallyclean    clean + db-clean"
	@echo "  distclean      remove everything not part of the distribution"
	@echo "  rmenv          remove virtual environment"
	@echo
	@echo "Setuptools commands:"
	@echo "  bdist, build, check, develop, install, sdist"
