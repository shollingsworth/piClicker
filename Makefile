# comlex Makefile example here: https://github.com/ansible/ansible/blob/devel/Makefile

.DEFAULT_GOAL := default
unexport PYTHONDONTWRITEBYTECODE
SETUP=setup.py
PYTHON=python2
NAME=piClicker
VERSION=$(shell cat VERSION)
GIT_BRANCH=$(shell git rev-parse --abbrev-ref HEAD | sed 's/\//_/g')
MYID=$(shell id -u)
ifeq ($(MYID),0)
	SUDO=
else
	SUDO=sudo
endif

.PHONY: default
default: python

.PHONY:
python:
	@echo $(VERSION)
	find -type f -name '*.pyc' -delete
	$(PYTHON) setup.py sdist

help:
	$(PYTHON) setup.py --help

help-cmds:
	$(PYTHON) setup.py --help-commands

help-rpm:
	$(PYTHON) setup.py bdist_rpm --help

.PHONY: deb
deb: clean python
	$(PYTHON) setup.py --command-packages=stdeb.command bdist_deb

.PHONY: rpm
rpm: clean python
	cp -f setup.cfg.rpm setup.cfg
	$(PYTHON) setup.py bdist --format=rpm
	rm -f setup.cfg

.PHONY: uninstall
uninstall:
	$(SUDO) pip uninstall -y $(NAME)

.PHONY: lint
lint:
	# Use https://github.com/nvie/vim-flake8 if you want to incorporate into vim
	find src/ bin/ -type f -name '*.py' -not -name '__init__.py' | xargs flake8
	# ignore non-used includes in __init__.py files
	find src/ bin/ -type f -name '__init__.py' | xargs flake8 --ignore F401

.PHONY: install
install: python
	$(SUDO) pip install $(shell find dist/ -type f -name '*.gz' | sort | tail -1)

.PHONY: reinstall
reinstall: clean uninstall install

.PHONY: venv
venv: clean python
	mkdir -p venv/
	rm -rf venv/
	virtualenv venv
	( \
		bash -c " \
		source venv/bin/activate; \
		pip install --upgrade $(shell find dist/ -type f -name '*.gz' | sort | tail -1); \
		" \
	)
	@echo Don\'t Forget to source venv/bin/activate

.PHONY: clean
clean:
	#make sure these exist so we dont run into errors on mac
	mkdir -p dist/ build/ deb_dist/
	>setup.cfg
	rm -rf dist/ build/ deb_dist/ src/cudaPyOps.egg-info setup.cfg
