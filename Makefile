.PHONY: \
	help \
	sync-dev \
	pre-commit \
	lint \
	format \
	pyright \
	pytest \
	coverage \
	check \
	verify \
	test \
	audit \
	audit-tree \
	imports \
	architecture \
	verify-mode \
	owl-upgrade \
	release \
	release-apply \
	release-patch \
	release-minor \
	release-major

# ==========================================================
# General
# ==========================================================

help:
	cat Makefile

sync-dev:
	uv sync --extra dev

# ==========================================================
# Code Quality
# ==========================================================

pre-commit:
	uv run pre-commit run --all-files

lint:
	uv run ruff check src tests

format:
	uv run ruff format src tests

pyright:
	uv run pyright

# ==========================================================
# Testing
# ==========================================================

pytest:
	uv run pytest

coverage:
	uv run pytest --cov=owlroost

# Fast developer verification
check: lint pyright

# Full validation
verify: pre-commit pytest

# Typical workflow
test: sync-dev verify

# ==========================================================
# Architecture Audits
# ==========================================================

audit:
	uv run roost-audit

# Useful while developing audit subsystem
audit-tree:
	uv run python -m owlroost.audit.tree

# Requires .importlinter
imports:
	uv run lint-imports

# Full architecture verification
architecture: imports audit

# ==========================================================
# Development Environment Diagnostics
# ==========================================================

verify-mode:
	uv run python -c "import pkgutil; print([m.name for m in pkgutil.iter_modules() if 'owl' in m.name.lower()])"
	uv run python -c "import subprocess, pathlib; p=pathlib.Path('../owl-planner'); print(subprocess.check_output(['git','branch','--show-current'], cwd=p).decode().strip())"

# ==========================================================
# OWL Upgrade / Regeneration
# ==========================================================

owl-upgrade:
	@echo ""
	@echo "=================================================="
	@echo "UPGRADING OWL PIN + REGENERATING HYDRA CONFIG"
	@echo "=================================================="
	@echo ""
	@echo "This may introduce BREAKING CHANGES."
	@echo ""
	@echo "Steps:"
	@echo "  1. Update Owl pin"
	@echo "  2. Sync environment"
	@echo "  3. Regenerate Hydra config"
	@echo "  4. Run schema consistency checks"
	@echo "  5. Run full pytest suite"
	@echo ""

	uv run scripts/update_owl_pin.py

	uv sync --extra dev

	uv run src/owlroost/tools/generate_hydra_conf.py

	uv run src/owlroost/tools/schema_coverage.py

	uv run scripts/sync_owl_examples.py

	uv run pytest

# ==========================================================
# Release Versioning
# ==========================================================

release:
	uv run scripts/bump_version.py
	@echo ""
	@echo "+ Run \"make architecture\" before releasing."
	@echo "+ Run \"make test\" before releasing."
	@echo "+ Use one of:"
	@echo "    make release-patch"
	@echo "    make release-minor"
	@echo "    make release-major"

release-apply:
	uv run scripts/bump_version.py patch --apply
	uv pip install -e . --force-reinstall
	uv run roost --version

release-patch:
	uv run scripts/bump_version.py patch --apply
	uv pip install -e . --force-reinstall
	uv run roost --version

release-minor:
	uv run scripts/bump_version.py minor --apply
	uv pip install -e . --force-reinstall
	uv run roost --version

release-major:
	uv run scripts/bump_version.py major --apply
	uv pip install -e . --force-reinstall
	uv run roost --version
