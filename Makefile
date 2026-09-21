PYTHON ?= python3
DX ?= dx
PORT ?= 8080
BASE_PATH ?=
AUTHOR_EXPORT ?=
CONTENT_DIR ?= content/enterprise
VERSION ?=

.PHONY: help content regenerate-content check build serve serve-existing learner author import-author release release-build

help:
	@echo "Tutorialz commands:"
	@echo "  make author                         Open the web authoring studio in development mode"
	@echo "  make learner                        Open the learner in development mode"
	@echo "  make serve [PORT=8080]              Build and serve learner + author locally"
	@echo "  make serve-existing [PORT=8080]     Serve the existing dist/ without rebuilding"
	@echo "  make import-author AUTHOR_EXPORT=... Install a studio ZIP into content/enterprise"
	@echo "  make check                          Validate content and run required checks"
	@echo "  make regenerate-content             Replace bundled questions from generator sources"
	@echo "  make build [BASE_PATH=tutorialz]    Build both production web apps into dist/"
	@echo "  make release [VERSION=0.4.0]        Check, build, commit, tag, and push a release"

content:
	$(PYTHON) scripts/question_bank.py

regenerate-content:
	$(PYTHON) scripts/enterprise-content.py
	$(PYTHON) scripts/question_bank.py

check: content
	$(PYTHON) -m unittest discover -s tests -p '*_test.py'
	cargo test -p tutorialz-core --locked
	cargo run -p tutorialz-core --locked -- content/catalog.json
	cargo run -p tutorialz-core --locked -- content/enterprise/catalog.json
	cargo check --workspace --target wasm32-unknown-unknown --locked
	npm test

build: content
	SITE_BASE_PATH="$(BASE_PATH)" DX="$(DX)" $(PYTHON) scripts/build-web.py

serve: build
	@echo "Learner: http://127.0.0.1:$(PORT)/"
	@echo "Author:  http://127.0.0.1:$(PORT)/author/"
	$(PYTHON) -m http.server $(PORT) --bind 127.0.0.1 --directory dist

serve-existing:
	@test -f dist/index.html || { echo "dist/ is missing; run 'make build' first." >&2; exit 1; }
	@echo "Learner: http://127.0.0.1:$(PORT)/"
	@echo "Author:  http://127.0.0.1:$(PORT)/author/"
	$(PYTHON) -m http.server $(PORT) --bind 127.0.0.1 --directory dist

learner:
	$(DX) serve --web --package tutorialz-learner

author:
	$(DX) serve --web --package tutorialz-author

import-author:
	@test -n "$(AUTHOR_EXPORT)" || { echo "Usage: make import-author AUTHOR_EXPORT=/path/to/tutorialz-content.zip" >&2; exit 2; }
	$(PYTHON) scripts/install-author-export.py "$(AUTHOR_EXPORT)" "$(CONTENT_DIR)"
	cargo run -p tutorialz-core --locked -- "$(CONTENT_DIR)/catalog.json"
	$(PYTHON) scripts/question_bank.py "$(CONTENT_DIR)/catalog.json" --report "$(CONTENT_DIR)/coverage.json"

release-build: check build

release:
	$(PYTHON) scripts/release.py $(if $(VERSION),--version "$(VERSION)",)
