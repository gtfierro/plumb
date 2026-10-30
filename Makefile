.DEFAULT_GOAL := help

UV ?= uv
TEST_ARGS ?=
DOCS_ARGS ?=

PYTHON_PATHS := src tests examples
DOCS_DIR := docs/book
FORMAT_EXCLUDE := src/plumb/qudt/units.py,src/plumb/qudt/quantity_kinds.py

.PHONY: help setup check test lint format-check typecheck format build dist-check docs docs-rebuild \
	docs-check docs-open docs-clean regen regen-check examples clean

help: ## Show available commands
	@awk 'BEGIN {FS = ":.*## "} /^[a-zA-Z_-]+:.*## / {printf "  %-16s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

setup: ## Install project, development, and documentation dependencies
	$(UV) sync --group docs

check: lint format-check typecheck test ## Run lint, format, type checks, and tests

test: ## Run tests (override TEST_ARGS to select tests or options)
	$(UV) run pytest $(TEST_ARGS)

lint: ## Check Python style and common errors
	$(UV) run ruff check $(PYTHON_PATHS)

format-check: ## Check formatting, excluding generated ontology output
	$(UV) run ruff format --check --extend-exclude '$(FORMAT_EXCLUDE)' $(PYTHON_PATHS) scripts

typecheck: ## Check Python types
	$(UV) run ty check $(PYTHON_PATHS)

format: ## Format Python source, excluding generated ontology output
	$(UV) run ruff format --extend-exclude '$(FORMAT_EXCLUDE)' $(PYTHON_PATHS) scripts

build: ## Build the source distribution and wheel in dist/, replacing old output
	$(UV) build --clear

dist-check: build ## Build, then check metadata and smoke-test the installed wheel
	$(UV) run --isolated --no-project --with twine twine check --strict dist/*
	$(UV) run --isolated --no-project --with dist/plumb_rdf-*.whl \
		python -I scripts/check_dist.py

docs: ## Build HTML documentation and execute tutorial notebooks
	$(UV) run --group docs jupyter-book build $(DOCS_DIR) $(DOCS_ARGS)

docs-rebuild: ## Rebuild all documentation pages
	$(UV) run --group docs jupyter-book build $(DOCS_DIR) --all $(DOCS_ARGS)

docs-check: ## Rebuild documentation with warnings treated as errors
	$(UV) run --group docs jupyter-book build $(DOCS_DIR) --all --warningiserror $(DOCS_ARGS)

docs-open: docs ## Build documentation and open it in the default browser
	$(UV) run --group docs python -c 'from pathlib import Path; import webbrowser; webbrowser.open(Path("$(DOCS_DIR)/_build/html/index.html").resolve().as_uri())'

docs-clean: ## Remove generated documentation and notebook caches
	$(UV) run --group docs jupyter-book clean $(DOCS_DIR) --all

regen: ## Regenerate S223, WaTr, QUDT, and domain packages from locked local inputs
	$(UV) run python scripts/regenerate.py

regen-check: ## Check offline regeneration, including generated file ownership
	$(UV) run python scripts/regenerate.py --check

examples: ## Run every example, refreshing its committed Turtle output
	cd examples/brick/quickstart && $(UV) run python brick_quickstart.py
	cd examples/s223/ahu && $(UV) run python s223_quickstart.py
	cd examples/s223/cooling_coil && $(UV) run python cooling_coil.py
	cd examples/watr/asm2d && $(UV) run python watertap_asm2d.py
	cd examples/watr/epanet_anytown && $(UV) run python epanet_anytown_to_watr.py Anytown.inp
	cd examples/watr/seawater_ro && $(UV) run python watertap_seawater_ro_full.py
	cd examples/watr/seawater_ro_pretreatment && \
		$(UV) run python watertap_seawater_ro_pretreatment.py
	cd examples/watr/treatment && $(UV) run python watr_quickstart.py

clean: docs-clean ## Remove documentation, build output, and tool caches
	rm -rf build dist .pytest_cache .ruff_cache
