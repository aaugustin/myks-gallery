export PYTHONPATH:=.:$(PYTHONPATH)
export DJANGO_SETTINGS_MODULE:=gallery.test_settings

test:
	django-admin test gallery

coverage:
	coverage erase
	coverage run --branch --source=gallery `which django-admin` test gallery
	coverage html

clean:
	find gallery -name '*.pyc' -delete
	find gallery -name __pycache__ -delete
	rm -rf .coverage *.egg-info build dist htmlcov MANIFEST
