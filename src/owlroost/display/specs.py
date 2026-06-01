# src/owlroost/display/specs.py

"""
Display subsystem specifications.

Notes
-----
Display provides renderer-facing presentation
overlays layered atop canonical semantic
entities.

Display owns:

    - labels
    - formatting
    - alignment
    - visibility
    - grouping
    - views

Display does NOT own:

    - canonical ontology
    - semantic identity
    - lineage graphs
    - provenance graphs

Synthetic semantic variables may be
declared within display modules for
convenience, but their semantic identity
ultimately belongs to the catalog layer.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import (
    dataclass,
    field,
)

# =========================================================
# Display Profile
# =========================================================


@dataclass
class DisplayProfile:
    """
    Renderer-facing presentation profile.
    """

    # =====================================================
    # Labeling
    # =====================================================

    label: str | None = None

    # =====================================================
    # Formatting
    # =====================================================

    fmt: str | None = None

    # =====================================================
    # Alignment
    # =====================================================

    label_align: str = "left"

    content_align: str = "left"

    # =====================================================
    # Layout
    # =====================================================

    width: int | None = None

    wrap: bool = False

    visible: bool = True


# =========================================================
# Display Value Function
# =========================================================

DisplayValueFn = Callable[
    [dict],
    object,
]

# =========================================================
# Display Field
# =========================================================


@dataclass
class DisplayField:
    """
    Renderer-facing display field.

    DisplayField represents a presentation
    entity layered atop ROOST ontology.

    The semantic classification of the field
    is determined by ontology metadata and
    lineage rather than constructor type.

    Examples
    --------

    Existing ontology field:

        DisplayField.field(
            "solver_options.bequest",
        )

    Synthetic display field:

        DisplayField.field(
            "display.net_worth",
            display_fn=net_worth_display,
            derived_from=[
                "display.total_savings",
                "display.net_hfp_assets",
            ],
        )
    """

    # =====================================================
    # Identity
    # =====================================================

    field_name: str

    # =====================================================
    # Runtime Extraction
    # =====================================================

    path: str | None = None

    display_fn: DisplayValueFn | None = None

    # =====================================================
    # Existing Ontology Link
    # =====================================================

    ontology_field: object | None = None

    # =====================================================
    # Ontology Metadata
    # =====================================================

    owner: str | None = None

    semantic_domain: str | None = None

    value_origin: str | None = None

    projection_kind: str | None = None

    analytic_kind: str | None = None

    materialization_level: str | None = None

    derived_from: list[str] = field(
        default_factory=list,
    )

    # =====================================================
    # Presentation Profiles
    # =====================================================

    profiles: dict[
        str,
        DisplayProfile,
    ] = field(
        default_factory=dict,
    )

    # =====================================================
    # Conditional Visibility
    # =====================================================

    show_if: list[str] = field(
        default_factory=list,
    )

    # =====================================================
    # Metadata
    # =====================================================

    description: str | None = None

    notes: str = ""

    # =====================================================
    # Constructor
    # =====================================================

    @classmethod
    def field(
        cls,
        field_name: str,
        **kwargs,
    ):
        """
        Preferred DisplayField constructor.

        Supports:

            - schema-backed fields
            - metric-backed fields
            - aggregate fields
            - synthetic fields
            - future derived fields

        Ontology metadata determines
        semantic behavior.
        """

        return cls(
            field_name=field_name,
            **kwargs,
        )

    # =====================================================
    # Classification
    # =====================================================

    @property
    def is_synthetic(
        self,
    ) -> bool:
        """
        Infer synthetic semantics from
        lineage and ontology metadata.
        """

        return (
            self.display_fn is not None
            or bool(self.derived_from)
            or self.projection_kind == "synthetic"
        )

    # =====================================================
    # Helper to set default values for synthetic fields
    # =====================================================

    def _apply_synthetic_defaults(
        self,
    ):
        self.owner = self.owner or "ROOST"

        self.semantic_domain = self.semantic_domain or "decision"

        self.value_origin = self.value_origin or "roost-computed"

        self.projection_kind = self.projection_kind or "synthetic"

        self.analytic_kind = self.analytic_kind or "synthetic"

        self.materialization_level = self.materialization_level or "case"

    # =====================================================
    # Post Init
    # =====================================================

    def __post_init__(
        self,
    ):
        if self.path is None:
            self.path = self.field_name

        if self.is_synthetic:
            self._apply_synthetic_defaults()


# =========================================================
# Display Groups
# =========================================================


@dataclass
class DisplayGroup:
    """
    Named display composition group.
    """

    key: str

    entries: list[str | tuple | dict]

    description: str = ""


# =========================================================
# Display Views
# =========================================================


@dataclass
class DisplayView:
    """
    Renderer-facing view specification.
    """

    level: str

    name: str

    entries: list

    description: str = ""
