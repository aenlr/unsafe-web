build develop install sdist bdist check test:
	python setup.py $@

clean:
	python setup.py clean
	rm -rf build dist .pytest_cache *.egg* *-test.db sessions.db access.log
