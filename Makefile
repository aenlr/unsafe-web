VENV = venv

.PHONY: venv

all:
	@echo "What do you want?"

venv:
	python3 -m venv $(VENV)
	$(VENV)/bin/pip install --upgrade pip

rmenv:
	rm -rf $(VENV)

dev: develop
	$(VENV)/bin/pip install -e .[dev]

initdb:
	$(VENV)/bin/unsafe-initdb

cleandb:
	rm -rf *.db

build develop install sdist bdist check:
	$(VENV)/bin/python setup.py $@

test:
	$(VENV)/bin/pytest

coverage cov:
	$(VENV)/bin/pytest --cov

clean:
	rm -rf build .coverage dist .eggs .pytest_cache test*.db sessions.db *.log
	find . -name __pycache__ -delete

reallyclean: clean cleandb

distclean: reallyclean rmenv
	rm -rf *.egg-info
