import tomllib
from io import StringIO
from pathlib import Path

import pytest
from owlplanner.config.plan_bridge import config_to_plan

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
