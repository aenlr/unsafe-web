VENV = venv

.PHONY: venv

all:
	@echo "What do you want?"

venv:
	python3 -m venv $(VENV)

rmenv:
	rm -rf $(VENV)

dev: develop
	pip install -e .[dev]

initdb:
	$(VENV)/bin/unsafe-initdb

cleandb:
	rm -rf *.db

build develop install sdist bdist check:
	python setup.py $@

test:
	pytest

clean:
	rm -rf build dist .eggs .pytest_cache *-test.db sessions.db *.log
	find . -name __pycache__ -delete

reallyclean: clean cleandb

distclean: reallyclean rmenv
	rm -rf *.egg-info
