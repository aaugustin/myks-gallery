test:
	python -m django test --settings=gallery.test_settings

coverage:
	coverage erase
	coverage run -m django test --settings=gallery.test_settings
	coverage html

clean:
	rm -rf .coverage dist gallery.egg-info htmlcov

style:
	isort example gallery
	flake8 example gallery
