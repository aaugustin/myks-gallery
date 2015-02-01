export PYTHONPATH:=.:$(PYTHONPATH)
export DJANGO_SETTINGS_MODULE:=gallery.test_settings

test:
	django-admin.py test gallery

coverage:
	coverage erase
	coverage run --branch --source=gallery `which django-admin.py` test gallery
	coverage html

clean:
	find . -name '*.pyc' -delete
	find . -name __pycache__ -delete
	rm -rf .coverage dist htmlcov MANIFEST
