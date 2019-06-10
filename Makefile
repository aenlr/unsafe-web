VENV = venv

.PHONY: venv

all:
	@echo "What do you want?"

venv:
	python3 -m venv $(VENV)

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

clean:
	rm -rf build dist .eggs .pytest_cache test*.db sessions.db *.log
	find . -name __pycache__ -delete

reallyclean: clean cleandb

distclean: reallyclean rmenv
	rm -rf *.egg-info
