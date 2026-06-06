# src/owlroost/schema/sections/case.py

"""
Case schema section.

Notes
-----
Defines ROOST case-discovery and case-selection inputs.

These variables control how ROOST
locates and names a case independent
of the retirement planning inputs
contained within the case itself.

Architectural Invariant
-----------------------
This module owns:

    - section model
    - schema registration
    - ontology metadata

for the case TOML/Hydra section.
"""

from __future__ import annotations

from pydantic import (
    Field,
)

from owlroost.catalog.ontology import (
    CatalogNodeType,
)
from owlroost.core.utils import normalize_module_path
from owlroost.schema.registry import (
    FieldSpec,
)
from owlroost.schema.utils import (
    resolve_field_default,
    unwrap_annotation,
    walk_model,
)

from ..specs import (
    BaseSectionConfig,
)

# =========================================================
# Section Model
# =========================================================


class CaseConfig(
    BaseSectionConfig,
):
    """
    Hydra-level case selection
    configuration.
    """

    file: str | None = Field(
        default=None,
        description=("Path to case TOML file."),
    )

    name: str | None = Field(
        default=None,
        description=("Case name override."),
    )


# =========================================================
# Registration
# =========================================================


def register_schema_fields(
    reg,
):
    """
    Register case fields.
    """

    for name, field in walk_model(
        "",
        CaseConfig,
    ):
        full_name = f"case.{name}"

        if full_name in reg:
            continue

        reg.register(
            FieldSpec(
                # =====================================
                # Identity
                # =====================================
                name=full_name,
                dtype=unwrap_annotation(
                    field.annotation,
                ),
                # =====================================
                # Runtime Realization
                # =====================================
                path=("case",) + tuple(name.split(".")),
                source="input",
                default=resolve_field_default(field),
                # =====================================
                # Ontology
                # =====================================
                owner="ROOST",
                semantic_domain="design",
                value_origin="user-specified",
                projection_kind="canonical",
                analytic_kind="observed",
                materialization_level="case",
                node_type=(CatalogNodeType.VARIABLE),
                # =====================================
                # Documentation
                # =====================================
                description=(field.description or ""),
                # =========================================
                # Provenance
                # =========================================
                defined_in=normalize_module_path(__file__),
            )
        )
