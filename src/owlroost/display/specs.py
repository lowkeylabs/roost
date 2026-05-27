# src/owlroost/display/specs.py

from __future__ import annotations

from collections.abc import (
    Callable,
)
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

    Notes
    -----
    DisplayProfile intentionally owns only:

        - labels
        - formatting
        - alignment
        - visibility
        - wrapping

    It intentionally does NOT own:

        - ontology semantics
        - canonical identity
        - provenance
        - runtime materialization
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
# Display Overlay Field
# =========================================================


@dataclass
class DisplayField:
    """
    Renderer-facing presentation overlay.

    Notes
    -----
    DisplayField represents presentation
    overlays layered atop canonical ontology.

    Canonical semantic ownership belongs to:

        - schema fields
        - metric fields
        - catalog entities

    DisplayField intentionally owns only:

        - presentation overlays
        - formatting
        - labels
        - view composition
        - renderer-facing metadata

    Architectural Invariant
    -----------------------
    DisplayField must never redefine
    canonical ontology identity.
    """

    # =====================================================
    # Overlay Identity
    # =====================================================

    field_name: str

    # =====================================================
    # Runtime Extraction Path
    # =====================================================

    path: str | None = None

    # =====================================================
    # Canonical Ontology Linkage
    # =====================================================

    ontology_field: object | None = None

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
    # Computed Presentation Overlay
    # =====================================================

    display_fn: (
        DisplayValueFn | None
    ) = None

    # =====================================================
    # Lightweight Renderer Metadata
    # =====================================================

    description: str | None = None

    # =====================================================
    # Post Init
    # =====================================================

    def __post_init__(
        self,
    ):
        """
        Normalize lightweight defaults.
        """

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

    entries: list[
        str | tuple | dict
    ]

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
    