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
authoring convenience, but semantic
ownership ultimately belongs to the
catalog subsystem.

Architectural Invariant
-----------------------
DisplayField.field(...) acts as an
authoring DSL.

Ontology declarations supplied through
DisplayField.field(...) are converted
into catalog declarations.

Catalog synthesis later determines
whether those declarations:

    - create new semantic entities
    - overlay existing semantic entities

Display itself remains presentation-only.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import (
    dataclass,
    field,
)
from typing import TYPE_CHECKING, Literal, TypedDict

if TYPE_CHECKING:
    from owlroost.catalog.specs import CatalogSpec

DisplayMode = Literal[
    "table",
    "pivot",
]


class OntologyKwargs(
    TypedDict,
    total=False,
):
    owner: str
    semantic_domain: str
    value_origin: str
    projection_kind: str
    analytic_kind: str
    materialization_level: str
    node_type: str


# =========================================================
# Display Profile
# =========================================================


@dataclass
class DisplayProfile:
    """
    Renderer-facing presentation profile.
    """

    label: str | None = None

    fmt: str | None = None

    label_align: str = "left"

    content_align: str = "left"

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

    DisplayField owns presentation metadata
    only.

    Semantic identity, ontology, lineage,
    and provenance remain owned by the
    catalog subsystem.

    Existing catalog variables may be
    referenced directly.

    Synthetic semantic variables may be
    declared through the authoring DSL.
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
    # Catalog Declaration
    # =====================================================

    catalog_declaration: CatalogSpec | None = None

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
    # Documentation
    # =====================================================

    description: str | None = None

    notes: str = ""

    @staticmethod
    def default_profiles():
        return {
            "table": DisplayProfile(),
        }

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

        DisplayField.field(...) acts as an
        authoring DSL.

        Authors may optionally declare
        semantic ontology metadata.

        When ontology metadata is supplied,
        a CatalogSpec declaration is
        synthesized automatically and
        attached to the DisplayField.

        Architectural Invariant
        -----------------------
        Every semantic catalog entity must
        have complete ontology metadata.

        Therefore:

            - ontology without lineage
            is valid

            - ontology with lineage
            is valid

            - lineage without ontology
            is invalid

        DisplayField remains a presentation
        construct. CatalogSpec remains the
        semantic construct.
        """

        from owlroost.catalog.specs import (
            CatalogSpec,
        )

        ontology_keys = {
            "owner",
            "semantic_domain",
            "value_origin",
            "projection_kind",
            "analytic_kind",
            "materialization_level",
            "node_type",
        }

        lineage_keys = {
            "derived_from",
            "expands_to",
        }

        ontology: OntologyKwargs = {}

        lineage: dict[
            str,
            list[str],
        ] = {}
        # =====================================================
        # Extract Catalog Metadata
        # =====================================================

        for key in list(kwargs):
            if key in ontology_keys:
                ontology[key] = kwargs.pop(
                    key,
                )

            elif key in lineage_keys:
                lineage[key] = kwargs.pop(
                    key,
                )

        # =====================================================
        # Pure Presentation Overlay
        # =====================================================

        if not ontology and not lineage:
            return cls(
                field_name=field_name,
                catalog_declaration=None,
                **kwargs,
            )

        # =====================================================
        # Invalid Semantic Declaration
        # =====================================================

        if lineage and not ontology:
            raise ValueError(f"{field_name}: lineage metadata requires ontology metadata")

        # =====================================================
        # Default display profiles
        # =====================================================

        profiles = kwargs.pop(
            "profiles",
            {},
        )

        if not profiles:
            profiles = cls.default_profiles()

        # =====================================================
        # Required Ontology Validation
        # =====================================================

        required = {
            "owner",
            "semantic_domain",
            "value_origin",
            "projection_kind",
        }

        missing = required - set(
            ontology,
        )

        if missing:
            raise ValueError(
                f"{field_name}: semantic declaration missing ontology metadata: {sorted(missing)}"
            )

        # =====================================================
        # Catalog Declaration
        # =====================================================

        catalog_declaration = CatalogSpec(
            field_name=field_name,
            derived_from=list(
                lineage.get(
                    "derived_from",
                    [],
                )
            ),
            expands_to=list(
                lineage.get(
                    "expands_to",
                    [],
                )
            ),
            **ontology,
        )

        return cls(
            field_name=field_name,
            catalog_declaration=(catalog_declaration),
            profiles=profiles,
            **kwargs,
        )

    # =====================================================
    # Post Init
    # =====================================================

    def __post_init__(
        self,
    ):
        """
        Normalize lightweight metadata.
        """

        if not self.profiles:
            self.profiles = self.default_profiles()

        if self.path is None:
            self.path = self.field_name


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

    entries: list[str | tuple[str, dict]]

    description: str = ""
