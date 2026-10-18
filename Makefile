.PHONY: help lint lint-python lint-ansible lint-syntax lint-ruff lint-black lint-isort format tox bundle bundle-clean

PYTHON ?= python3
PYTHON_SOURCES := install.py plugins docs/conf.py
ANSIBLE_SOURCES := playbooks roles tasks meta
BUNDLE_NAME ?= fp-NGFW-SMC-ansible

help:
	@printf '%s\n' \
	  'lint          Run all Python and Ansible lint checks' \
	  'lint-python   Run all Python lint checks' \
	  'lint-ansible  Run Ansible lint with the production profile' \
	  'format        Apply Ruff, Black, and isort formatting' \
	  'tox           Run isolated lint environments' \
	  'bundle        Build tar.gz, Base64, and ZIP source bundles' \
	  'bundle-clean  Remove generated source bundles'

lint: lint-python lint-ansible

lint-python: lint-syntax lint-ruff lint-black lint-isort

lint-ansible:
	ansible-lint $(ANSIBLE_SOURCES)

lint-syntax:
	$(PYTHON) -m compileall -q $(PYTHON_SOURCES)

lint-ruff:
	ruff check $(PYTHON_SOURCES)

lint-black:
	black --check --diff $(PYTHON_SOURCES)

lint-isort:
	isort --check-only --diff $(PYTHON_SOURCES)

format:
	ruff check --fix $(PYTHON_SOURCES)
	black $(PYTHON_SOURCES)
	isort $(PYTHON_SOURCES)

tox:
	tox

bundle: bundle-clean
	tar \
	  --exclude-vcs \
	  --exclude='.tox' \
	  --exclude='.venv' \
	  --exclude='venv' \
	  --exclude='__pycache__' \
	  --exclude='*.pyc' \
	  --exclude='build' \
	  --exclude='dist' \
	  --exclude='$(BUNDLE_NAME).tar.gz' \
	  --exclude='$(BUNDLE_NAME).tar.gz.b64.txt' \
	  --exclude='$(BUNDLE_NAME).zip' \
	  -czf $(BUNDLE_NAME).tar.gz .
	gzip -t $(BUNDLE_NAME).tar.gz
	base64 -w 0 $(BUNDLE_NAME).tar.gz > $(BUNDLE_NAME).tar.gz.b64.txt
	zip -qr $(BUNDLE_NAME).zip . \
	  -x '.git/*' '.tox/*' '.venv/*' 'venv/*' '*/__pycache__/*' '*.pyc' \
	     'build/*' 'dist/*' '$(BUNDLE_NAME).tar.gz' \
	     '$(BUNDLE_NAME).tar.gz.b64.txt' '$(BUNDLE_NAME).zip'

bundle-clean:
	rm -f $(BUNDLE_NAME).tar.gz $(BUNDLE_NAME).tar.gz.b64.txt $(BUNDLE_NAME).zip
