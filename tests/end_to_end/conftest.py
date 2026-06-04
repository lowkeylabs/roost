from __future__ import annotations

import re
import shutil
import subprocess
import tomllib
from io import StringIO
from pathlib import Path

import pytest
from owlplanner.config import (
    config_to_plan,
    load_toml,
)

# =========================================================
# Test Cases
# =========================================================

CASE_ROOT = Path(__file__).parent / "cases"

# =========================================================
# Helpers
# =========================================================


def _safe_name(
    name: str,
) -> str:
    """
    Convert pytest node names into
    filesystem-safe session names.
    """

    return re.sub(
        r"[^A-Za-z0-9_.-]",
        "_",
        name,
    )


def load_toml_file(
    path: Path,
):
    """
    Load TOML into a raw dict.
    """

    with path.open("rb") as fp:
        return tomllib.load(fp)


def load_plan_from_toml(
    toml_file: Path,
):
    """
    Load TOML into a real OWL Plan.
    """

    diconf, dirname, _ = load_toml(
        str(toml_file),
    )

    logstreams = [StringIO(), StringIO()]
    return config_to_plan(
        diconf,
        dirname,
        verbose=False,
        loadHFP=False,
        logstreams=logstreams,
    )


# =========================================================
# Session Builder
# =========================================================


@pytest.fixture
def build_session(
    request,
):
    """
    Build a deterministic ROOST session.

    Example
    -------

    session = build_session(
        "case_alex+jamie.toml",
        "roost_sweeps.ss_age_pair=69-69",
    )
    """

    def _build(
        case_name: str,
        *overrides,
    ):
        case_path = CASE_ROOT / case_name

        assert case_path.exists(), f"Case file not found: {case_path}"

        session_date = "test"

        session_time = _safe_name(request.node.name)

        session_root = Path("results") / case_path.stem / session_date / session_time

        if session_root.exists():
            shutil.rmtree(
                session_root,
            )

        cmd = [
            "uv",
            "run",
            "roost",
            "build",
            str(case_path),
            *overrides,
            f"session.date={session_date}",
            f"session.time={session_time}",
        ]

        result = subprocess.run(
            cmd,
            text=True,
            capture_output=True,
        )

        assert result.returncode == 0, f"\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"

        assert session_root.exists()

        return session_root

    return _build


# =========================================================
# Raw TOML Fixtures
# =========================================================


@pytest.fixture
def load_session_toml():
    """
    Load session.toml as a dict.
    """

    def _load(
        session_dir: Path,
    ):
        session_file = session_dir / "session.toml"

        assert session_file.exists()

        return load_toml_file(
            session_file,
        )

    return _load


@pytest.fixture
def load_run_toml():
    """
    Load run_N/run.toml as a dict.
    """

    def _load(
        session_dir: Path,
        run_id: int = 0,
    ):
        run_file = session_dir / f"run_{run_id}" / "run.toml"

        assert run_file.exists()

        return load_toml_file(
            run_file,
        )

    return _load


@pytest.fixture
def load_trial_toml():
    """
    Load trial_NNNN/trial.toml as a dict.
    """

    def _load(
        session_dir: Path,
        run_id: int = 0,
        trial_id: int = 0,
    ):
        trial_file = session_dir / f"run_{run_id}" / "trials" / f"{trial_id:04d}" / "trial.toml"

        assert trial_file.exists()

        return load_toml_file(
            trial_file,
        )

    return _load


# =========================================================
# OWL Plan Fixtures
# =========================================================


@pytest.fixture
def load_run_plan():
    """
    Load run_N/run.toml into
    a real OWL Plan object.
    """

    def _load(
        session_dir: Path,
        run_id: int = 0,
    ):
        run_file = session_dir / f"run_{run_id}" / "run.toml"

        assert run_file.exists()

        return load_plan_from_toml(
            run_file,
        )

    return _load


@pytest.fixture
def load_trial_plan():
    """
    Load trial_NNNN/trial.toml into
    a real OWL Plan object.
    """

    def _load(
        session_dir: Path,
        run_id: int = 0,
        trial_id: int = 0,
    ):
        trial_file = session_dir / f"run_{run_id}" / "trials" / f"{trial_id:04d}" / "trial.toml"

        assert trial_file.exists()

        return load_plan_from_toml(
            trial_file,
        )

    return _load
