# src/owlroost/schema/specs.py

"""
TODO: Document module.

Notes
-----
Describe responsibilities, ownership,
and architectural role.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import (
    dataclass,
    field,
)
from typing import (
    Literal,
)

from pydantic import (
    BaseModel,
    ConfigDict,
)

from owlroost.catalog.ontology import (
    OntologySpec,
)
from owlroost.display.specs import (
    DisplayProfile,
)

# =========================================================
# Runtime Source Domains
# =========================================================

RuntimeSource = Literal[
    "input",
    "derived",
    "discovered",
    "internal",
    "sweep",
]

# =========================================================
# Schema Field Specification
# =========================================================


@dataclass
class FieldSpec(
    OntologySpec,
):
    """
    Canonical executable schema field definition.

    Notes
    -----
    FieldSpec defines executable OWL/ROOST
    configuration ontology and runtime
    realization metadata.

    These fields typically materialize into:

        _inputs

    while also contributing semantic ontology
    metadata harvested by:

        - catalog subsystem
        - display subsystem
        - explainability systems
        - reporting pipelines
        - runtime provenance systems

    Ontology semantics are inherited from:

        OntologySpec

    This specification intentionally focuses on:

        - executable configuration ontology
        - runtime realization
        - authoring origin metadata
        - lightweight default presentation intent

    while avoiding:

        - renderer implementation
        - grouping/view composition
        - catalog indexing
        - operational registry behavior
    """

    # =====================================================
    # Identity
    # =====================================================

    name: str

    # =====================================================
    # Typing
    # =====================================================

    dtype: type | None = object

    # =====================================================
    # Runtime Realization
    # =====================================================

    path: tuple[str, ...] = field(
        default_factory=tuple,
    )

    source: RuntimeSource = "input"

    # =====================================================
    # Computed Runtime Fields
    # =====================================================

    compute_fn: Callable | None = None

    # =====================================================
    # Aggregation Compatibility
    # =====================================================

    aggregates: list[str] = field(
        default_factory=list,
    )

    # =====================================================
    # Semantic Metadata
    # =====================================================

    description: str = ""

    units: str | None = None

    # =====================================================
    # Authoring Metadata
    # =====================================================
    #
    # Identifies the schema module or source
    # responsible for declaring this field.
    #
    # This is NOT catalog provenance.
    #
    # Catalog provenance is synthesized later
    # from schema, metrics, display, and
    # aggregation layers.
    # =====================================================

    defined_in: str | None = None

    # =====================================================
    # Defaults
    # =====================================================

    default: object | None = None

    # =====================================================
    # Default Display Profiles
    # =====================================================

    profiles: dict[
        str,
        DisplayProfile,
    ] = field(
        default_factory=dict,
    )

    # =====================================================
    # Notes
    # =====================================================

    notes: str = ""

    # =====================================================
    # Post Init
    # =====================================================

    def __post_init__(
        self,
    ):
        # =================================================
        # Normalize Path
        # =================================================

        if self.path is None:
            self.path = ()


# =========================================================
# Base
# =========================================================


class BaseSectionConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
