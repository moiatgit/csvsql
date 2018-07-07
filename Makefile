.PHONY: init test dist install twine_upload

HELP_FUN = \
         %help; \
         while(<>) { push @{$$help{$$2 // 'options'}}, [$$1, $$3] if /^(\w+)\s*:.*\#\#(?:@(\w+))?\s(.*)$$/ }; \
         print "usage: make [target]\n\n"; \
     for (keys %help) { \
         print "$$_:\n"; $$sep = " " x (20 - length $$_->[0]); \
         print "  $$_->[0]$$sep$$_->[1]\n" for @{$$help{$$_}}; \
         print "\n"; }     

help:           ##@miscellaneous Show this help.
	@perl -e '$(HELP_FUN)' $(MAKEFILE_LIST)

init:			##@miscellaneous pip install requirements
	pip install -r requirements.txt

test:			##@miscellaneous perform all unit tests
	pytest

dist:			##@miscellaneous generate distribution version
	python3 setup.py sdist bdist_wheel

twine_upload:	##@miscellaneous upload current version on test.pypi.org (requires interaction)
	twine upload --repository-url https://test.pypi.org/legacy/ dist/*

install:		##@miscellaneous install current version from test.pypi.org
	pip install -U --index-url https://test.pypi.org/simple/ csvsql

