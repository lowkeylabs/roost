# src/owlroost/schema/specs.py

from __future__ import annotations

from dataclasses import (
    dataclass,
    field,
)
from typing import (
    Callable,
    Literal,
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
    "helper",
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
        - lightweight provenance
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
    # Provenance
    # =====================================================

    defined_in: str | None = None

    derived_from: list[str] = field(
        default_factory=list,
    )

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
