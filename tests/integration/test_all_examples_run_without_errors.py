import tomllib
from io import StringIO
from pathlib import Path

import pytest
from owlplanner.config.plan_bridge import config_to_plan

from owlroost.domain.case import Case

EXAMPLES_DIR = Path("examples/example01")


def get_example_files():
    files = sorted(EXAMPLES_DIR.glob("*.toml"))
    if not files:
        pytest.fail("No example TOML files found.")
    return files


@pytest.mark.parametrize(
    "path",
    get_example_files(),
    ids=lambda p: p.name,
)
def test_owlplanner_example_runs(path):
    """
    Native OWLPlanner integration test.

    Each example TOML file must:
    - build a Plan
    - solve successfully
    """

    with path.open("rb") as f:
        config = tomllib.load(f)

    try:
        plan = config_to_plan(
            config,
            dirname=str(path.parent),
            loadHFP=True,
            verbose=False,
            logstreams=[StringIO(), StringIO()],  # silence logging
        )

        plan.solve(plan.objective, plan.solverOptions)

    except Exception as e:
        pytest.fail(f"{path.name} raised exception: {e}")

    assert getattr(plan, "caseStatus", None) == "solved", (
        f"{path.name} did not solve successfully. " f"Status: {getattr(plan, 'caseStatus', None)}"
    )


@pytest.mark.parametrize(
    "path",
    get_example_files(),
    ids=lambda p: p.name,
)
def test_rewrite_preserves_solution(path, monkeypatch):
    # Move into examples directory
    monkeypatch.chdir(path.parent)

    local_path = Path(path.name)

    # 1️⃣ Run original
    with local_path.open("rb") as f:
        original_config = tomllib.load(f)

    plan_original = config_to_plan(
        original_config,
        dirname=str(Path.cwd()),
        loadHFP=True,
        verbose=False,
        logstreams=[StringIO(), StringIO()],
    )
    plan_original.solve(plan_original.objective, plan_original.solverOptions)

    assert plan_original.caseStatus == "solved"

    orig_max_spending = getattr(plan_original, "maxSpending", None)
    orig_first_year = getattr(plan_original, "firstYearTotalWithdrawals", None)

    # 2️⃣ Rewrite
    case = Case(local_path)
    case.write()

    # 3️⃣ Run rewritten
    with local_path.open("rb") as f:
        rewritten_config = tomllib.load(f)

    plan_rewritten = config_to_plan(
        rewritten_config,
        dirname=str(Path.cwd()),
        loadHFP=True,
        verbose=False,
        logstreams=[StringIO(), StringIO()],
    )
    plan_rewritten.solve(plan_rewritten.objective, plan_rewritten.solverOptions)

    assert plan_rewritten.caseStatus == "solved"

    if orig_max_spending is not None:
        assert plan_rewritten.maxSpending == pytest.approx(orig_max_spending, rel=1e-9)

    if orig_first_year is not None:
        assert plan_rewritten.firstYearTotalWithdrawals == pytest.approx(orig_first_year, rel=1e-9)
