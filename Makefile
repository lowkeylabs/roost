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
