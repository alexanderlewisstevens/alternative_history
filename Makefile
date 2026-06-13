PYTHON ?= python3
VENV ?= .venv
VENV_PYTHON := $(VENV)/bin/python
VENV_STAMP := $(VENV)/.requirements.stamp
CONFIG ?= data/extraction-sources.yml
SOURCE_ID ?= norton-theory-criticism
SOURCE_PDF ?= epdf.pub_the-norton-anthology-of-theory-and-criticism-5ea806ce63784.pdf
SLICED_DIR ?= Norton_Anthology_Sliced_Author
PAGE_RECORDS_DIR ?= work/page-records/$(SOURCE_ID)
AUTHOR_DRAFTS_DIR ?= generated/authors/$(SOURCE_ID)
LAYOUT_DIR ?= work/layout/$(SOURCE_ID)
CLASSIFICATION_DIR ?= work/classification/$(SOURCE_ID)
REVIEW_DIR ?= work/review/$(SOURCE_ID)
PROMPTS_DIR ?= work/prompts/$(SOURCE_ID)
AUDIT_DIR ?= work/audit/$(SOURCE_ID)
PAGES ?=
LIMIT ?=
AGENT_COMMAND ?=
PAGE_AGENT_BACKEND ?= codex
PILOT_PAGES ?= 71-82
PILOT_AGENT_COMMAND ?= $(VENV_PYTHON) scripts/codex_page_agent.py --backend $(PAGE_AGENT_BACKEND)
SERVE_ADDR ?= 127.0.0.1:8000

COMMON_ARGS := --config $(CONFIG) --source-id $(SOURCE_ID)
PAGE_ARGS := $(if $(PAGES),--pages $(PAGES),)
LIMIT_ARGS := $(if $(LIMIT),--limit $(LIMIT),)
SELECT_ARGS := $(PAGE_ARGS) $(LIMIT_ARGS)
AGENT_ARGS := $(if $(AGENT_COMMAND),--agent-command "$(AGENT_COMMAND)",)

.PHONY: setup slice validate-fixtures extract-layout classify-pages generate-page-records validate-page-records assemble-authors validate-authors update-site update-workspace update-workspace-constellations update-workspace-thinkers update-workspace-notes update-workspace-passages build smoke-site browser-smoke-site install-browser audit ci pilot pilot-api serve clean-extraction clean-generated

$(VENV_STAMP): requirements.txt
	$(PYTHON) -m venv $(VENV)
	$(VENV_PYTHON) -m pip install --upgrade pip
	$(VENV_PYTHON) -m pip install -r requirements.txt
	touch $(VENV_STAMP)

setup: $(VENV_STAMP)

slice: setup
	$(VENV_PYTHON) scripts/slice_pdf_pages.py --input $(SOURCE_PDF) --output $(SLICED_DIR) --force $(PAGE_ARGS)

validate-fixtures: setup
	$(VENV_PYTHON) scripts/run_fixture_checks.py

extract-layout: setup
	$(VENV_PYTHON) scripts/extract_layout.py $(COMMON_ARGS) $(SELECT_ARGS)

classify-pages: setup extract-layout
	$(VENV_PYTHON) scripts/classify_pages.py $(COMMON_ARGS) $(SELECT_ARGS)

generate-page-records: setup classify-pages
	$(VENV_PYTHON) scripts/generate_page_records.py $(COMMON_ARGS) $(SELECT_ARGS) $(AGENT_ARGS)

validate-page-records: setup
	$(VENV_PYTHON) scripts/validate_records.py $(PAGE_RECORDS_DIR) --strict --type page_record

assemble-authors: setup
	$(VENV_PYTHON) scripts/assemble_authors.py $(COMMON_ARGS) $(SELECT_ARGS) --clean

validate-authors: setup
	$(VENV_PYTHON) scripts/validate_records.py $(AUTHOR_DRAFTS_DIR) --strict --type author_file

update-workspace: setup
	$(VENV_PYTHON) scripts/update_workspace_constellations.py $(COMMON_ARGS)
	$(VENV_PYTHON) scripts/update_workspace_passage_notes.py $(COMMON_ARGS) --clean
	$(VENV_PYTHON) scripts/update_workspace_thinker_notes.py $(COMMON_ARGS) --clean
	$(VENV_PYTHON) scripts/update_workspace_map.py $(COMMON_ARGS)
	$(VENV_PYTHON) scripts/update_workspace_text_notes.py $(COMMON_ARGS) --clean

update-workspace-constellations: setup
	$(VENV_PYTHON) scripts/update_workspace_constellations.py $(COMMON_ARGS)

update-workspace-thinkers: setup
	$(VENV_PYTHON) scripts/update_workspace_thinker_notes.py $(COMMON_ARGS) --clean

update-workspace-notes: setup
	$(VENV_PYTHON) scripts/update_workspace_text_notes.py $(COMMON_ARGS) --clean

update-workspace-passages: setup
	$(VENV_PYTHON) scripts/update_workspace_passage_notes.py $(COMMON_ARGS) --clean

update-site: setup
	$(VENV_PYTHON) scripts/update_extraction_status_page.py $(COMMON_ARGS)
	$(VENV_PYTHON) scripts/update_review_dashboard_page.py $(COMMON_ARGS)
	$(VENV_PYTHON) scripts/update_workspace_constellations.py $(COMMON_ARGS)
	$(VENV_PYTHON) scripts/update_workspace_passage_notes.py $(COMMON_ARGS) --clean
	$(VENV_PYTHON) scripts/update_workspace_thinker_notes.py $(COMMON_ARGS) --clean
	$(VENV_PYTHON) scripts/update_workspace_map.py $(COMMON_ARGS)
	$(VENV_PYTHON) scripts/update_workspace_text_notes.py $(COMMON_ARGS) --clean

build: setup update-site
	$(VENV_PYTHON) -m mkdocs build --strict

smoke-site: build
	$(VENV_PYTHON) scripts/smoke_site.py --site-dir site

install-browser: setup
	$(VENV_PYTHON) -m playwright install chromium

browser-smoke-site: build
	$(VENV_PYTHON) scripts/browser_smoke_site.py --site-dir site

serve: setup update-site
	$(VENV_PYTHON) -m mkdocs serve --dev-addr $(SERVE_ADDR)

audit: setup validate-fixtures
	$(VENV_PYTHON) scripts/audit_pipeline.py $(COMMON_ARGS) --strict

ci: setup validate-fixtures
	$(VENV_PYTHON) -m compileall -q scripts
	$(VENV_PYTHON) -m mkdocs build --strict
	@if [ -f "$(SOURCE_PDF)" ]; then \
		$(MAKE) audit SOURCE_ID=$(SOURCE_ID); \
	else \
		echo "Skipping restricted-source audit because $(SOURCE_PDF) is not present."; \
	fi

pilot: setup
	$(MAKE) clean-extraction SOURCE_ID=$(SOURCE_ID)
	$(MAKE) generate-page-records SOURCE_ID=$(SOURCE_ID) PAGES=$(PILOT_PAGES) AGENT_COMMAND='$(PILOT_AGENT_COMMAND)'
	$(MAKE) validate-page-records SOURCE_ID=$(SOURCE_ID)
	$(MAKE) assemble-authors SOURCE_ID=$(SOURCE_ID) PAGES=$(PILOT_PAGES)
	$(MAKE) validate-authors SOURCE_ID=$(SOURCE_ID)
	$(MAKE) audit SOURCE_ID=$(SOURCE_ID)
	$(MAKE) build

pilot-api: PAGE_AGENT_BACKEND=openai
pilot-api: pilot

clean-extraction:
	rm -rf $(LAYOUT_DIR)
	rm -rf $(CLASSIFICATION_DIR)
	rm -rf $(REVIEW_DIR)
	rm -rf $(PROMPTS_DIR)
	rm -rf $(AUDIT_DIR)
	rm -rf $(PAGE_RECORDS_DIR)
	rm -rf $(AUTHOR_DRAFTS_DIR)

clean-generated:
	rm -rf $(SLICED_DIR)
	rm -rf work
	rm -rf generated
	rm -rf site
	rm -rf .site
