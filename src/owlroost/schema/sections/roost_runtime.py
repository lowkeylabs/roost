# src/owlroost/schema/sections/roost_runtime.py

"""
ROOST runtime schema section.

Notes
-----
Defines ROOST execution and orchestration
configuration.

These variables describe HOW ROOST executes
sessions, runs, and trials.

Architectural Invariant
-----------------------
This module owns:

    - section model
    - schema registration
    - ontology metadata

for the roost_runtime TOML section.
"""

from __future__ import annotations

from pydantic import (
    Field,
)

from owlroost.catalog.ontology import (
    CatalogNodeType,
)
from owlroost.schema.registry import (
    FieldSpec,
)
from owlroost.schema.utils import (
    unwrap_annotation,
    walk_model,
)

from ..specs import (
    BaseSectionConfig,
)

# =========================================================
# Section Model
# =========================================================


class RoostRuntimeConfig(
    BaseSectionConfig,
):
    """
    ROOST execution/orchestration configuration.

    These settings define HOW ROOST executes
    sessions and trials, separate from the
    retirement scenario itself.
    """

    # -----------------------------------------------------
    # Session provenance
    # -----------------------------------------------------

    session_id: str | None = Field(
        default=None,
        description="Session identifier.",
    )

    session_description: str | None = Field(
        default=None,
        description="Optional session description.",
    )

    run_id: int | None = Field(
        default=None,
        ge=0,
        description="Run index within session.",
    )

    run_description: str | None = Field(
        default=None,
        description="Optional run description.",
    )

    trial_id: int | None = Field(
        default=None,
        ge=0,
        description="Trial index within run.",
    )

    # -----------------------------------------------------
    # Deterministic execution
    # -----------------------------------------------------

    master_seed: int | None = Field(
        default=987_654_321,
        description="Master seed for deterministic execution.",
    )

    rate_seed: int | None = Field(
        default=None,
        description="Seed used for stochastic rates generation.",
    )

    longevity_seed: int | None = Field(
        default=None,
        description="Seed used for stochastic longevity generation.",
    )

    # -----------------------------------------------------
    # Trial generation
    # -----------------------------------------------------

    trials_per_run: int = Field(
        default=1,
        ge=1,
        description="Number of trials generated for each run.",
    )

    # -----------------------------------------------------
    # Parallel execution
    # -----------------------------------------------------

    workers_per_run: int | None = Field(
        default=None,
        ge=1,
        description=("Number of parallel workers used to execute trials within a run."),
    )

    worker_timeout: int = Field(
        default=120,
        ge=1,
        description="Timeout in seconds for each trial.",
    )

    run_owl_as_subprocess: bool = Field(
        default=False,
        description="Execute OWL in a subprocess.",
    )

    workers_per_run_mode: str = Field(
        default="auto",
        description=("Worker allocation strategy: 'fixed' or 'auto'."),
    )

    # -----------------------------------------------------
    # Solver-aware execution topology policies
    # -----------------------------------------------------

    auto_workers_by_solver: dict[str, int] = Field(
        default_factory=lambda: {
            "MOSEK": 8,
            "HiGHS": 12,
        },
        description=("Recommended workers_per_run by solver when workers_per_run_mode='auto'."),
    )

    auto_runtime_environment_by_solver: dict[
        str,
        dict[str, int],
    ] = Field(
        default_factory=lambda: {
            "MOSEK": {
                "OMP_NUM_THREADS": 1,
                "OPENBLAS_NUM_THREADS": 1,
                "MKL_NUM_THREADS": 1,
                "MSK_IPAR_NUM_THREADS": 1,
            },
            "HiGHS": {},
        },
        description=(
            "Recommended runtime environment variables by solver when workers_per_run_mode='auto'."
        ),
    )


# =========================================================
# Registration
# =========================================================


def register_schema_fields(
    reg,
):
    """
    Register roost runtime fields.
    """

    for name, field in walk_model(
        "",
        RoostRuntimeConfig,
    ):
        full_name = f"roost_runtime.{name}"

        if full_name in reg:
            continue

        reg.register(
            FieldSpec(
                # =========================================
                # Identity
                # =========================================
                name=full_name,
                dtype=unwrap_annotation(
                    field.annotation,
                ),
                # =========================================
                # Runtime Realization
                # =========================================
                path=("roost_runtime",) + tuple(name.split(".")),
                source="input",
                # =========================================
                # Ontology
                # =========================================
                owner="ROOST",
                semantic_domain="execution",
                value_origin="user-specified",
                projection_kind="canonical",
                analytic_kind="observed",
                materialization_level="case",
                node_type=CatalogNodeType.VARIABLE,
                # =========================================
                # Documentation
                # =========================================
                description=(field.description or ""),
                defined_in="roost_runtime",
            )
        )
