.PHONY: help sync pre-commit pytest test

help:
	cat Makefile

sync-dev:
	uv sync --extra dev

pre-commit:
	uv run pre-commit run --all-files

pytest:
	uv run pytest

test: sync-dev pre-commit pytest


verify-mode:
	uv run python -c "import pkgutil; print([m.name for m in pkgutil.iter_modules() if 'owl' in m.name.lower()])"
	uv run python -c "import subprocess, pathlib; p=pathlib.Path('../owl-planner'); print(subprocess.check_output(['git','branch','--show-current'], cwd=p).decode().strip())" fixes/bootstrap-sor


# ---------------------------------------
# Release versioning
# ---------------------------------------

.PHONY: release release-apply release-patch release-minor release-major

# Preview next patch version (dry-run)
release:
	uv run scripts/bump_version.py
	@echo ""
	@echo + Run \"make pre-commit\" and \"uv run pytest\" prior to bumping version.
	@echo + use \"make version-apply\" to bump version.

# Actually tag patch release
release-apply:
	uv run scripts/bump_version.py patch --apply
	uv pip install -e . --force-reinstall

# Explicit bump types
release-patch:
	uv run scripts/bump_version.py patch --apply
	uv pip install -e . --force-reinstall

release-minor:
	uv run scripts/bump_version.py minor --apply
	uv pip install -e . --force-reinstall

release-major:
	uv run scripts/bump_version.py major --apply
	uv pip install -e . --force-reinstall
