VENV = venv

.PHONY: venv

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

build develop install sdist bdist check test:
	python setup.py $@

clean:
	rm -rf build dist .eggs .pytest_cache *-test.db sessions.db *.log
	find . -name __pycache__ -delete

reallyclean: clean cleandb

distclean: reallyclean rmenv
	rm -rf *.egg-info
